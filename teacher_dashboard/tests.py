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
            reception=True,
            target_grade='1',
            target_major='情報工学科'
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
            reception=False,
            target_grade='2',
            target_major='機械工学科'
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
            reception=False,
            target_grade='3',
            target_major='電気工学科'
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
        # 既存の出席記録を削除（setUpで作成されたもの）
        AttendanceRecord.objects.filter(user=self.student_user, lesson=self.lesson1).delete()
        
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

    def test_duplicate_checkin_prevention(self):
        """同じ生徒が同じ授業に重複してチェックインできないことをテスト"""
        # 既存の出席記録を削除（setUpで作成されたもの）
        AttendanceRecord.objects.filter(user=self.student_user, lesson=self.lesson1).delete()
        
        # 新しいトークン作成（未使用）
        duplicate_token = AttendanceToken.objects.create(
            token='duplicate_test_token',
            user=self.student_user,
            expires=timezone.now() + timezone.timedelta(minutes=5)
        )

        # キオスクユーザーでログイン
        kiosk_client = Client()
        kiosk_client.login(username='test_kiosk', password='password123')

        # 最初のconfirm_attendance実行（成功するはず）
        response = kiosk_client.post('/checkin/confirm-attendance/', {
            'token': 'duplicate_test_token',
            'status': 'present'
        }, content_type='application/json')

        # デバッグ用：レスポンス内容を確認
        if response.status_code != 200:
            print(f"First request failed with status {response.status_code}")
            print(f"Response content: {response.content.decode()}")

        # 成功することを確認
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])

        # 2回目のトークン作成（同じユーザー、同じ授業）
        second_token = AttendanceToken.objects.create(
            token='second_duplicate_token',
            user=self.student_user,
            expires=timezone.now() + timezone.timedelta(minutes=5)
        )

        # 2回目のconfirm_attendance実行（拒否されるはず）
        response = kiosk_client.post('/checkin/confirm-attendance/', {
            'token': 'second_duplicate_token',
            'status': 'present'
        }, content_type='application/json')

        # 拒否されることを確認
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('既にチェックイン済みです', response_data['error'])

        # 出席記録が1つだけ存在することを確認
        attendance_count = AttendanceRecord.objects.filter(
            user=self.student_user,
            lesson=self.lesson1
        ).count()
        self.assertEqual(attendance_count, 1)

    def test_same_token_reuse_prevention(self):
        """同じトークンでの重複使用を防ぐテスト"""
        # 既存の出席記録を削除
        AttendanceRecord.objects.filter(user=self.student_user, lesson=self.lesson1).delete()
        
        # 新しいトークンを作成
        test_token = AttendanceToken.objects.create(
            token='reuse_test_token',
            user=self.student_user,
            expires=timezone.now() + timezone.timedelta(minutes=5)
        )
        
        # キオスクユーザーでログイン
        kiosk_client = Client()
        kiosk_client.login(username='test_kiosk', password='password123')

        # 1回目のチェックイン（成功するはず）
        response = kiosk_client.post('/checkin/confirm-attendance/', {
            'token': 'reuse_test_token',
            'status': 'present'
        }, content_type='application/json')
        
        # 成功することを確認
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # トークンが使用済みになっていることを確認
        test_token.refresh_from_db()
        self.assertTrue(test_token.is_used)

        # 2回目のチェックイン（同じトークンで試行、拒否されるはず）
        response = kiosk_client.post('/checkin/confirm-attendance/', {
            'token': 'reuse_test_token',
            'status': 'present'
        }, content_type='application/json')

        # 拒否されることを確認
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('トークンが無効または既に使用済み', response_data['error'])


class SessionManagementTest(TestCase):
    """セッション管理機能のテストケース"""
    
    def setUp(self):
        """テスト用データの準備"""
        # 招待コードを作成
        self.invitation_code = InvitationCode.objects.create(
            code='TEST123',
            name='テスト招待コード',
            type='teacher',
            is_active=True
        )
        
        # 教師ユーザーを作成
        self.teacher_user = CustomUser.objects.create_user(
            username='test_teacher',
            password='password123',
            type='teacher',
            invitation_code=self.invitation_code
        )
        
        # 教師プロファイルを作成
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            subject='テスト科目'
        )
    
    def test_session_invalidation_on_login(self):
        """ログイン時の既存セッション無効化テスト"""
        from django.contrib.sessions.models import Session
        from accounts.utils import invalidate_user_sessions
        
        # 最初のログイン
        client1 = Client()
        response1 = client1.post('/accounts/login/', {
            'username': 'test_teacher',
            'password': 'password123'
        })
        self.assertEqual(response1.status_code, 302)  # リダイレクト成功
        
        # セッションが作成されていることを確認
        session_count_before = Session.objects.count()
        self.assertGreater(session_count_before, 0)
        
        # ユーザーのcurrent_session_keyが設定されていることを確認
        self.teacher_user.refresh_from_db()
        self.assertIsNotNone(self.teacher_user.current_session_key)
        first_session_key = self.teacher_user.current_session_key
        
        # 2回目のログイン（別のクライアント）
        client2 = Client()
        response2 = client2.post('/accounts/login/', {
            'username': 'test_teacher',
            'password': 'password123'
        })
        self.assertEqual(response2.status_code, 302)  # リダイレクト成功
        
        # ユーザーのcurrent_session_keyが更新されていることを確認
        self.teacher_user.refresh_from_db()
        self.assertIsNotNone(self.teacher_user.current_session_key)
        second_session_key = self.teacher_user.current_session_key
        self.assertNotEqual(first_session_key, second_session_key)
        
        # 最初のセッションでアクセスできないことを確認
        response_old = client1.get('/teacher/')
        # ログインページにリダイレクトされるか、403エラーになることを確認
        self.assertIn(response_old.status_code, [302, 403])
        
        # 新しいセッションでアクセスできることを確認
        response_new = client2.get('/teacher/')
        self.assertEqual(response_new.status_code, 200)
    
    def test_session_key_update_on_login(self):
        """ログイン時のセッションキー更新テスト"""
        client = Client()
        
        # ログイン前はcurrent_session_keyがNone
        self.assertIsNone(self.teacher_user.current_session_key)
        
        # ログイン
        response = client.post('/accounts/login/', {
            'username': 'test_teacher',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)
        
        # ログイン後はcurrent_session_keyが設定される
        self.teacher_user.refresh_from_db()
        self.assertIsNotNone(self.teacher_user.current_session_key)
        
        # セッションキーが実際のセッションと一致することを確認
        session_key = client.session.session_key
        self.assertEqual(self.teacher_user.current_session_key, session_key)
    
    def test_invalidate_user_sessions_utility(self):
        """セッション無効化ユーティリティ関数のテスト"""
        from django.contrib.sessions.models import Session
        from accounts.utils import invalidate_user_sessions
        
        # 複数のセッションを作成
        client1 = Client()
        client2 = Client()
        
        # 両方でログイン
        client1.post('/accounts/login/', {
            'username': 'test_teacher',
            'password': 'password123'
        })
        
        client2.post('/accounts/login/', {
            'username': 'test_teacher',
            'password': 'password123'
        })
        
        # セッション数を確認
        initial_session_count = Session.objects.count()
        self.assertGreater(initial_session_count, 0)
        
        # 特定のセッション以外を無効化
        current_session_key = client2.session.session_key
        invalidate_user_sessions(self.teacher_user, exclude_session_key=current_session_key)
        
        # 除外されたセッション以外が削除されていることを確認
        remaining_sessions = Session.objects.filter(session_key=current_session_key)
        self.assertEqual(remaining_sessions.count(), 1)
        
        # 最初のクライアントでアクセスできないことを確認
        response1 = client1.get('/teacher/')
        self.assertIn(response1.status_code, [302, 403])
        
        # 2番目のクライアントでアクセスできることを確認
        response2 = client2.get('/teacher/')
        self.assertEqual(response2.status_code, 200)
    
    def test_logout_clears_session_key(self):
        """ログアウト時のセッションキークリアテスト"""
        client = Client()
        
        # ログイン
        client.post('/accounts/login/', {
            'username': 'test_teacher',
            'password': 'password123'
        })
        
        # セッションキーが設定されていることを確認
        self.teacher_user.refresh_from_db()
        self.assertIsNotNone(self.teacher_user.current_session_key)
        
        # ログアウト
        response = client.post('/accounts/logout/')
        self.assertEqual(response.status_code, 302)
        
        # セッションキーがクリアされていることを確認
        self.teacher_user.refresh_from_db()
        self.assertIsNone(self.teacher_user.current_session_key)


class LessonTargetFieldsTest(TestCase):
    """授業の対象学年・専攻フィールドのテストケース"""
    
    def setUp(self):
        """テストデータのセットアップ"""
        # 招待コードを作成
        self.invitation_code = InvitationCode.objects.create(
            code='TEST456',
            name='テスト教師',
            type='teacher',
            is_active=True
        )
        
        # 教師ユーザーを作成
        self.teacher_user = CustomUser.objects.create_user(
            username='test_teacher_target',
            password='password123',
            type='teacher',
            invitation_code=self.invitation_code
        )
        
        # 教師プロファイルを作成
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            subject='テスト科目'
        )
        
        # クライアント設定
        self.client = Client()
        self.client.login(username='test_teacher_target', password='password123')
    
    def test_lesson_creation_with_target_fields(self):
        """対象学年・専攻フィールドを含む授業作成のテスト"""
        lesson = Lesson.objects.create(
            teacher=self.teacher,
            subject='プログラミング基礎',
            lesson_times=1,
            location='Room101',
            target_grade='1',
            target_major='情報工学科'
        )
        
        # フィールドが正しく保存されているか確認
        self.assertEqual(lesson.target_grade, '1')
        self.assertEqual(lesson.target_major, '情報工学科')
        self.assertEqual(lesson.subject, 'プログラミング基礎')
    
    def test_lesson_creation_without_target_fields(self):
        """対象学年・専攻フィールドなしでの授業作成のテスト"""
        lesson = Lesson.objects.create(
            teacher=self.teacher,
            subject='一般講義',
            lesson_times=1,
            location='Room102'
        )
        
        # デフォルト値が設定されているか確認
        self.assertEqual(lesson.target_grade, '')
        self.assertEqual(lesson.target_major, '')
    
    def test_generate_lesson_with_target_fields(self):
        """授業生成フォームでの対象学年・専攻指定のテスト"""
        response = self.client.post('/teacher/generate_lesson/', {
            'lesson_name': 'データベース設計',
            'lesson_count': '3',
            'target_grade': '2',
            'target_major': '情報工学科'
        })
        
        # レスポンスが成功するか確認
        self.assertEqual(response.status_code, 200)
        
        # 授業が正しく作成されているか確認（3回分の授業が作成される）
        lessons = Lesson.objects.filter(
            teacher=self.teacher,
            subject='データベース設計'
        ).order_by('lesson_times')
        
        self.assertEqual(lessons.count(), 3)
        
        # 各授業の内容を確認
        for i, lesson in enumerate(lessons, 1):
            self.assertEqual(lesson.target_grade, '2')
            self.assertEqual(lesson.target_major, '情報工学科')
            self.assertEqual(lesson.lesson_times, i)
            self.assertEqual(lesson.subject, 'データベース設計')
    
    def test_edit_lesson_target_fields(self):
        """授業編集での対象学年・専攻変更のテスト"""
        # 初期授業を作成
        lesson = Lesson.objects.create(
            teacher=self.teacher,
            subject='初期科目',
            lesson_times=1,
            location='Room104',
            target_grade='1',
            target_major='機械工学科'
        )
        
        # 授業を編集
        response = self.client.post(f'/teacher/edit_lesson/{lesson.id}/', {
            'subject': '更新科目',
            'lesson_times': '2',
            'location': 'Room105',
            'target_grade': '3',
            'target_major': '電気工学科'
        })
        
        # レスポンスが成功するか確認
        self.assertEqual(response.status_code, 200)
        
        # 授業が正しく更新されているか確認
        lesson.refresh_from_db()
        self.assertEqual(lesson.subject, '更新科目')
        self.assertEqual(lesson.target_grade, '3')
        self.assertEqual(lesson.target_major, '電気工学科')
        self.assertEqual(lesson.lesson_times, 2)
    
    def test_lesson_str_representation(self):
        """授業の文字列表現のテスト"""
        lesson = Lesson.objects.create(
            teacher=self.teacher,
            subject='ネットワーク基礎',
            lesson_times=5,
            target_grade='2',
            target_major='情報工学科'
        )
        
        expected_str = f"ネットワーク基礎 - {self.teacher.user.username} (第5回)"
        self.assertEqual(str(lesson), expected_str)
    
    def test_lesson_target_fields_choices(self):
        """対象学年・専攻の選択肢が正しく機能するかのテスト"""
        # 有効な選択肢でのテスト
        valid_grades = ['1', '2', '3', '4']
        valid_majors = ['情報工学科', '機械工学科', '電気工学科', '建築学科', '化学工学科']
        
        for grade in valid_grades:
            for major in valid_majors:
                lesson = Lesson.objects.create(
                    teacher=self.teacher,
                    subject=f'テスト科目_{grade}_{major}',
                    lesson_times=1,
                    target_grade=grade,
                    target_major=major
                )
                self.assertEqual(lesson.target_grade, grade)
                self.assertEqual(lesson.target_major, major)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.client.logout()
