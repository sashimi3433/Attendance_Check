from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.models import CustomUser, Teacher, Lesson, Kiosk, InvitationCode
from attendance_token.models import AttendanceToken, AttendanceRecord
import json

class AutomaticCheckinEndingTest(TestCase):
    def setUp(self):
        """テストデータのセットアップ"""
        # 教師ユーザー作成
        self.teacher_user = CustomUser.objects.create_user(
            username='test_teacher',
            password='password123',
            type='teacher'
        )
        self.invitation_code = InvitationCode.objects.create(
            code='12345',
            name='Test Teacher',
            type='teacher'
        )
        self.teacher_user.invitation_code = self.invitation_code
        self.teacher_user.save()

        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            subject='Test Subject'
        )

        # 生徒ユーザー作成
        self.student_user = CustomUser.objects.create_user(
            username='test_student',
            password='password123',
            type='student'
        )

        # キオスクユーザー作成
        self.kiosk_user = CustomUser.objects.create_user(
            username='test_kiosk',
            password='password123',
            type='kiosk'
        )
        self.kiosk = Kiosk.objects.create(
            user=self.kiosk_user,
            location='Room207'
        )

        # 最初のレッスン作成（アクティブ）
        self.lesson1 = Lesson.objects.create(
            teacher=self.teacher,
            subject='Lesson 1',
            lesson_times=1,
            location='Room207',
            is_active=True,
            reception=True
        )
        self.kiosk.current_lesson = self.lesson1
        self.kiosk.save()

        # 出席トークン作成
        self.token = AttendanceToken.objects.create(
            token='test_token_123',
            user=self.student_user,
            expires=timezone.now() + timezone.timedelta(minutes=5)
        )

        # 最初のレッスンの出席記録作成（終了時間なし）
        self.record1 = AttendanceRecord.objects.create(
            user=self.student_user,
            token=self.token,
            lesson=self.lesson1,
            status='present'
        )

        # クライアント設定
        self.client = Client()
        self.client.login(username='test_teacher', password='password123')

    def test_automatic_ending_when_new_lesson_starts(self):
        """新しいレッスンを開始すると、以前のチェックインが自動的に終了されることをテスト"""
        # 新しいレッスン作成
        lesson2 = Lesson.objects.create(
            teacher=self.teacher,
            subject='Lesson 2',
            lesson_times=2,
            reception=False
        )

        # start_checkinをシミュレート
        response = self.client.post('/teacher/start_checkin/', {
            'lesson_id': lesson2.id,
            'location': 'Room207'
        })

        # レスポンスが成功するか確認
        self.assertEqual(response.status_code, 200)

        # 最初のレッスンが非アクティブになったか確認
        self.lesson1.refresh_from_db()
        self.assertFalse(self.lesson1.is_active)

        # 最初のレッスンの出席記録のend_timeが設定されたか確認
        self.record1.refresh_from_db()
        self.assertIsNotNone(self.record1.end_time)

        # 新しいレッスンがアクティブになったか確認
        lesson2.refresh_from_db()
        self.assertTrue(lesson2.is_active)
        self.assertTrue(lesson2.reception)

        # キオスクのcurrent_lessonが新しいレッスンに設定されたか確認
        self.kiosk.refresh_from_db()
        self.assertEqual(self.kiosk.current_lesson, lesson2)

    def test_kiosk_association_reset(self):
        """キオスクの関連付けが正しくリセットされることをテスト"""
        # 新しいレッスン作成
        lesson2 = Lesson.objects.create(
            teacher=self.teacher,
            subject='Lesson 2',
            lesson_times=2,
            reception=False
        )

        # start_checkin実行
        self.client.post('/teacher/start_checkin/', {
            'lesson_id': lesson2.id,
            'location': 'Room207'
        })

        # キオスクのcurrent_lessonがリセットされたか確認（以前のレッスンから）
        self.kiosk.refresh_from_db()
        self.assertNotEqual(self.kiosk.current_lesson, self.lesson1)
        self.assertEqual(self.kiosk.current_lesson, lesson2)

    def test_checkin_validation_for_inactive_lesson(self):
        """アクティブでないレッスンではチェックインが拒否されることをテスト"""
        # レッスンを非アクティブに設定
        self.lesson1.is_active = False
        self.lesson1.save()
        self.kiosk.current_lesson = None
        self.kiosk.save()

        # 新しいトークン作成（未使用）
        new_token = AttendanceToken.objects.create(
            token='inactive_test_token',
            user=self.student_user,
            expires=timezone.now() + timezone.timedelta(minutes=5)
        )

        # キオスクユーザーでログイン
        kiosk_client = Client()
        kiosk_client.login(username='test_kiosk', password='password123')

        # confirm_attendanceを試行
        response = kiosk_client.post('/checkin/confirm-attendance/', {
            'token': 'inactive_test_token',
            'status': 'present'
        }, content_type='application/json')

        # 拒否されることを確認
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('アクティブなレッスンがありません', response_data['error'])

    def test_checkin_allowed_for_active_lesson(self):
        """アクティブなレッスンではチェックインが許可されることをテスト"""
        # 新しいトークン作成（未使用）
        new_token = AttendanceToken.objects.create(
            token='new_test_token',
            user=self.student_user,
            expires=timezone.now() + timezone.timedelta(minutes=5)
        )

        # キオスクユーザーでログイン
        kiosk_client = Client()
        kiosk_client.login(username='test_kiosk', password='password123')

        # confirm_attendance実行
        response = kiosk_client.post('/checkin/confirm-attendance/', {
            'token': 'new_test_token',
            'status': 'present'
        }, content_type='application/json')

        # 成功することを確認
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])

        # 出席記録が作成されたか確認
        record = AttendanceRecord.objects.filter(token=new_token).first()
        self.assertIsNotNone(record)
        self.assertEqual(record.lesson, self.lesson1)

    def test_end_lesson_functionality(self):
        """レッスン終了機能が正しく動作することをテスト"""
        # レッスン終了
        response = self.client.post(f'/teacher/end_lesson/{self.lesson1.id}/')

        # レスポンスが成功するか確認
        self.assertEqual(response.status_code, 200)

        # レッスンが非アクティブになったか確認
        self.lesson1.refresh_from_db()
        self.assertFalse(self.lesson1.is_active)
        self.assertFalse(self.lesson1.reception)

        # 出席記録のend_timeが設定されたか確認
        self.record1.refresh_from_db()
        self.assertIsNotNone(self.record1.end_time)

        # キオスクのcurrent_lessonがリセットされたか確認
        self.kiosk.refresh_from_db()
        self.assertIsNone(self.kiosk.current_lesson)
