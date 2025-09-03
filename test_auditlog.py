# test_auditlog.py
# django-auditlogの動作確認テスト

from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import InvitationCode, Teacher, Kiosk, Lesson
from attendance_token.models import AttendanceToken, AttendanceRecord
from auditlog.models import LogEntry
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class AuditlogTest(TestCase):
    """django-auditlogの動作確認テスト"""
    
    def setUp(self):
        """テスト用データの準備"""
        # 招待コードを作成
        self.invitation_code = InvitationCode.objects.create(
            code='TEST1',
            name='テスト招待コード',
            type='teacher',
            is_active=True
        )
        
        # ユーザーを作成
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            name='テストユーザー',
            type='teacher'
        )
        
    def test_user_creation_logged(self):
        """ユーザー作成がログに記録されることを確認"""
        # ログエントリが作成されているか確認
        log_entries = LogEntry.objects.filter(
            content_type__model='customuser',
            object_id=self.user.id,
            action=LogEntry.Action.CREATE
        )
        self.assertTrue(log_entries.exists())
        
    def test_user_update_logged(self):
        """ユーザー更新がログに記録されることを確認"""
        # ユーザー情報を更新
        self.user.name = '更新されたユーザー'
        self.user.save()
        
        # 更新ログが記録されているか確認
        log_entries = LogEntry.objects.filter(
            content_type__model='customuser',
            object_id=self.user.id,
            action=LogEntry.Action.UPDATE
        )
        self.assertTrue(log_entries.exists())
        
    def test_invitation_code_logged(self):
        """招待コードの操作がログに記録されることを確認"""
        # 招待コードを無効に変更
        self.invitation_code.is_active = False
        self.invitation_code.save()
        
        # ログエントリが作成されているか確認
        log_entries = LogEntry.objects.filter(
            content_type__model='invitationcode',
            object_id=self.invitation_code.id
        )
        self.assertTrue(log_entries.exists())
        
    def test_teacher_creation_logged(self):
        """教師プロファイル作成がログに記録されることを確認"""
        teacher = Teacher.objects.create(
            user=self.user,
            subject='数学'
        )
        
        # ログエントリが作成されているか確認
        log_entries = LogEntry.objects.filter(
            content_type__model='teacher',
            object_id=teacher.id,
            action=LogEntry.Action.CREATE
        )
        self.assertTrue(log_entries.exists())
        
    def test_attendance_token_logged(self):
        """出席トークンの操作がログに記録されることを確認"""
        token = AttendanceToken.objects.create(
            token='test_token_123',
            user=self.user,
            expires=timezone.now() + timedelta(minutes=5)
        )
        
        # 作成ログが記録されているか確認
        log_entries = LogEntry.objects.filter(
            content_type__model='attendancetoken',
            object_id=token.id,
            action=LogEntry.Action.CREATE
        )
        self.assertTrue(log_entries.exists())
        
        # トークンを使用済みに変更
        token.mark_as_used()
        
        # 更新ログが記録されているか確認
        update_logs = LogEntry.objects.filter(
            content_type__model='attendancetoken',
            object_id=token.id,
            action=LogEntry.Action.UPDATE
        )
        self.assertTrue(update_logs.exists())
        
    def test_log_entry_details(self):
        """ログエントリの詳細情報を確認"""
        # ユーザー名を変更
        old_name = self.user.name
        new_name = '新しい名前'
        self.user.name = new_name
        self.user.save()
        
        # 最新の更新ログを取得
        log_entry = LogEntry.objects.filter(
            content_type__model='customuser',
            object_id=self.user.id,
            action=LogEntry.Action.UPDATE
        ).latest('timestamp')
        
        # ログエントリの詳細を確認
        self.assertEqual(log_entry.object_repr, str(self.user))
        self.assertIn('name', log_entry.changes)
        self.assertEqual(log_entry.changes['name'][0], old_name)
        self.assertEqual(log_entry.changes['name'][1], new_name)
        
    def test_deletion_logged(self):
        """削除操作がログに記録されることを確認"""
        user_id = self.user.id
        user_repr = str(self.user)
        
        # ユーザーを削除
        self.user.delete()
        
        # 削除ログが記録されているか確認
        log_entries = LogEntry.objects.filter(
            content_type__model='customuser',
            object_id=user_id,
            action=LogEntry.Action.DELETE
        )
        self.assertTrue(log_entries.exists())
        
        # 削除ログの詳細を確認
        delete_log = log_entries.first()
        self.assertEqual(delete_log.object_repr, user_repr)