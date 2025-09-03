# -*- coding: utf-8 -*-
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.urls import reverse
from .models import InvitationCode
from .utils import invalidate_user_sessions, force_logout_user
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
import io
import csv

User = get_user_model()

class SessionManagementTest(TestCase):
    def setUp(self):
        """テストデータのセットアップ"""
        # 招待コード作成
        self.invitation_code = InvitationCode.objects.create(
            code='12345',
            name='Test User',
            type='student'
        )
        
        # テストユーザー作成
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            type='student',
            invitation_code=self.invitation_code
        )
        
        # クライアント作成
        self.client1 = Client()
        self.client2 = Client()
    
    def test_single_session_login(self):
        """単一セッションでのログインテスト"""
        # ログイン
        response = self.client1.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        # ログイン成功を確認
        self.assertEqual(response.status_code, 302)
        
        # ユーザーのセッションキーが設定されていることを確認
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.current_session_key)
        
        # セッションが存在することを確認
        session_exists = Session.objects.filter(
            session_key=self.user.current_session_key
        ).exists()
        self.assertTrue(session_exists)
    
    def test_multiple_device_login_prevention(self):
        """複数端末からのログイン防止テスト"""
        # 最初の端末でログイン
        response1 = self.client1.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response1.status_code, 302)
        
        # 最初のセッションキーを保存
        self.user.refresh_from_db()
        first_session_key = self.user.current_session_key
        self.assertIsNotNone(first_session_key)
        
        # 2番目の端末でログイン
        response2 = self.client2.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response2.status_code, 302)
        
        # ユーザーのセッションキーが更新されていることを確認
        self.user.refresh_from_db()
        second_session_key = self.user.current_session_key
        self.assertIsNotNone(second_session_key)
        self.assertNotEqual(first_session_key, second_session_key)
        
        # 最初のセッションが無効化されていることを確認
        first_session_exists = Session.objects.filter(
            session_key=first_session_key
        ).exists()
        self.assertFalse(first_session_exists)
        
        # 2番目のセッションが有効であることを確認
        second_session_exists = Session.objects.filter(
            session_key=second_session_key
        ).exists()
        self.assertTrue(second_session_exists)
    
    def test_logout_clears_session_key(self):
        """ログアウト時のセッションキークリアテスト"""
        # ログイン
        self.client1.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        # セッションキーが設定されていることを確認
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.current_session_key)
        
        # ログアウト
        response = self.client1.post(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)
        
        # セッションキーがクリアされていることを確認
        self.user.refresh_from_db()
        self.assertIsNone(self.user.current_session_key)
    
    def test_invalidate_user_sessions_utility(self):
        """セッション無効化ユーティリティ関数のテスト"""
        # ダミーセッションキーを設定
        dummy_session_key = 'dummy_session_key_12345'
        self.user.current_session_key = dummy_session_key
        self.user.save()
        
        # セッションを作成
        session = Session.objects.create(
            session_key=dummy_session_key,
            session_data='dummy_data',
            expire_date='2025-12-31 23:59:59'
        )
        
        # セッション無効化を実行
        new_session_key = 'new_session_key_67890'
        invalidate_user_sessions(self.user, exclude_session_key=new_session_key)
        
        # 古いセッションが削除されていることを確認
        session_exists = Session.objects.filter(
            session_key=dummy_session_key
        ).exists()
        self.assertFalse(session_exists)
        
        # 新しいセッションキーが設定されていることを確認
        self.user.refresh_from_db()
        self.assertEqual(self.user.current_session_key, new_session_key)
    
    def test_force_logout_user_utility(self):
        """強制ログアウトユーティリティ関数のテスト"""
        # ダミーセッションキーを設定
        dummy_session_key = 'dummy_session_key_force_logout'
        self.user.current_session_key = dummy_session_key
        self.user.save()
        
        # セッションを作成
        Session.objects.create(
            session_key=dummy_session_key,
            session_data='dummy_data',
            expire_date='2025-12-31 23:59:59'
        )
        
        # 強制ログアウトを実行
        force_logout_user(self.user)
        
        # セッションが削除されていることを確認
        session_exists = Session.objects.filter(
            session_key=dummy_session_key
        ).exists()
        self.assertFalse(session_exists)
        
        # セッションキーがクリアされていることを確認
        self.user.refresh_from_db()
        self.assertIsNone(self.user.current_session_key)
    
    def test_concurrent_login_from_same_user(self):
        """同一ユーザーの並行ログインテスト"""
        # 複数のクライアントで同時にログイン試行
        clients = [Client() for _ in range(3)]
        
        for i, client in enumerate(clients):
            response = client.post(reverse('accounts:login'), {
                'username': 'testuser',
                'password': 'testpass123'
            })
            self.assertEqual(response.status_code, 302)
        
        # 最後のログインのセッションのみが有効であることを確認
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.current_session_key)
        
        # 有効なセッションが1つだけであることを確認
        valid_sessions = Session.objects.filter(
            session_key=self.user.current_session_key
        ).count()
        self.assertEqual(valid_sessions, 1)


class CustomUserFieldsTest(TestCase):
    """CustomUserモデルの新しいフィールド（専攻・学年）のテスト"""
    
    def setUp(self):
        """テスト用のデータを準備"""
        self.User = get_user_model()
        self.invitation_code = InvitationCode.objects.create(
            code='TEST123',
            name='Test User',
            type='student'
        )
    
    def test_user_creation_with_major_and_grade(self):
        """専攻と学年を指定してユーザーを作成できることをテスト"""
        user = self.User.objects.create_user(
            username='testuser',
            password='testpass123',
            type='student',
            major='SE',  # システムエンジニア専攻
            grade='1',   # 1年
            invitation_code=self.invitation_code
        )
        
        self.assertEqual(user.major, 'SE')
        self.assertEqual(user.grade, '1')
        self.assertEqual(user.get_major_display(), 'システムエンジニア専攻')
        self.assertEqual(user.get_grade_display(), '1年')
    
    def test_major_choices_validation(self):
        """専攻の選択肢が正しく制限されることをテスト"""
        # 有効な専攻での作成
        user_se = self.User.objects.create_user(
            username='testuser_se',
            password='testpass123',
            type='student',
            major='SE',
            grade='1',
            invitation_code=self.invitation_code
        )
        self.assertEqual(user_se.major, 'SE')
        
        user_web = self.User.objects.create_user(
            username='testuser_web',
            password='testpass123',
            type='student',
            major='WEB',
            grade='2',
            invitation_code=self.invitation_code
        )
        self.assertEqual(user_web.major, 'WEB')
    
    def test_grade_choices_validation(self):
        """学年の選択肢が正しく制限されることをテスト"""
        # 各学年での作成テスト
        for grade in ['1', '2', '3']:
            user = self.User.objects.create_user(
                username=f'testuser_grade{grade}',
                password='testpass123',
                type='student',
                major='SE',
                grade=grade,
                invitation_code=self.invitation_code
            )
            self.assertEqual(user.grade, grade)
            self.assertEqual(user.get_grade_display(), f'{grade}年')
    
    def test_major_and_grade_can_be_blank(self):
        """専攻と学年は空白でも作成できることをテスト"""
        user = self.User.objects.create_user(
            username='testuser_blank',
            password='testpass123',
            type='student',
            invitation_code=self.invitation_code
            # major と grade を指定しない
        )
        
        self.assertEqual(user.major, '')
        self.assertEqual(user.grade, '')
    
    def test_user_string_representation_with_major_grade(self):
        """専攻と学年を含むユーザーの文字列表現をテスト"""
        user = self.User.objects.create_user(
            username='testuser_repr',
            password='testpass123',
            type='student',
            major='WEB',
            grade='3',
            invitation_code=self.invitation_code
        )
        
        # ユーザーの文字列表現にユーザー名が含まれることを確認
        self.assertIn('testuser_repr', str(user))
    
    def test_filtering_by_major_and_grade(self):
        """専攻と学年でのフィルタリングをテスト"""
        # 異なる専攻・学年のユーザーを作成
        user1 = self.User.objects.create_user(
            username='user1',
            password='testpass123',
            type='student',
            major='SE',
            grade='1',
            invitation_code=self.invitation_code
        )
        
        user2 = self.User.objects.create_user(
            username='user2',
            password='testpass123',
            type='student',
            major='WEB',
            grade='2',
            invitation_code=self.invitation_code
        )
        
        user3 = self.User.objects.create_user(
            username='user3',
            password='testpass123',
            type='student',
            major='SE',
            grade='3',
            invitation_code=self.invitation_code
        )
        
        # 専攻でのフィルタリング
        se_users = self.User.objects.filter(major='SE')
        self.assertEqual(se_users.count(), 2)
        self.assertIn(user1, se_users)
        self.assertIn(user3, se_users)
        
        web_users = self.User.objects.filter(major='WEB')
        self.assertEqual(web_users.count(), 1)
        self.assertIn(user2, web_users)
        
        # 学年でのフィルタリング
        first_year_users = self.User.objects.filter(grade='1')
        self.assertEqual(first_year_users.count(), 1)
        self.assertIn(user1, first_year_users)
        
        # 専攻と学年の組み合わせでのフィルタリング
        se_third_year = self.User.objects.filter(major='SE', grade='3')
        self.assertEqual(se_third_year.count(), 1)
        self.assertIn(user3, se_third_year)


class CSVImportExportTest(TestCase):
    """CSVインポート・エクスポート機能のテストケース"""
    
    def setUp(self):
        """テストデータのセットアップ"""
        self.User = get_user_model()
        
        # 教師用招待コード作成
        self.teacher_invitation_code = InvitationCode.objects.create(
            code='teacher123',
            name='Test Teacher',
            type='teacher'
        )
        
        # 生徒用招待コード作成
        self.student_invitation_code = InvitationCode.objects.create(
            code='student123',
            name='Test Student',
            type='student'
        )
        
        # 教師ユーザー作成
        self.teacher = self.User.objects.create_user(
            username='teacher',
            password='testpass123',
            type='teacher',
            name='テスト教師',
            invitation_code=self.teacher_invitation_code
        )
        
        # 生徒ユーザー作成
        self.student1 = self.User.objects.create_user(
            username='student1',
            password='testpass123',
            type='student',
            name='テスト生徒1',
            birth_date='2000-01-01',
            admission_year=2020,
            department='IT',
            major='SE',
            grade='1',
            invitation_code=self.student_invitation_code
        )
        
        self.student2 = self.User.objects.create_user(
            username='student2',
            password='testpass123',
            type='student',
            name='テスト生徒2',
            birth_date='2001-02-02',
            admission_year=2021,
            department='IT',
            major='WEB',
            grade='2',
            invitation_code=self.student_invitation_code
        )
        
        self.client = Client()
    
    def test_export_students_csv_as_teacher(self):
        """教師として生徒データをCSVエクスポートするテスト"""
        # 教師としてログイン
        self.client.login(username='teacher', password='testpass123')
        
        # CSVエクスポートのリクエスト
        response = self.client.get(reverse('accounts:export_students_csv'))
        
        # レスポンスの確認
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('attachment; filename="students.csv"', response['Content-Disposition'])
        
        # CSVの内容を確認
        content = response.content.decode('utf-8-sig')
        csv_reader = csv.reader(io.StringIO(content))
        rows = list(csv_reader)
        
        # ヘッダーの確認
        expected_header = ['ユーザー名', '名前', '生年月日', '入学年度', '学科', '専攻', '学年']
        self.assertEqual(rows[0], expected_header)
        
        # データ行の確認（生徒のみ）
        self.assertEqual(len(rows), 3)  # ヘッダー + 2人の生徒
        
        # 生徒1のデータ確認
        student1_row = rows[1]
        self.assertEqual(student1_row[0], 'student1')
        self.assertEqual(student1_row[1], 'テスト生徒1')
        self.assertEqual(student1_row[2], '2000-01-01')
        self.assertEqual(student1_row[3], '2020')
        self.assertEqual(student1_row[4], 'IT')
        self.assertEqual(student1_row[5], 'システムエンジニア専攻')
        self.assertEqual(student1_row[6], '1年')
    
    def test_export_students_csv_as_student_forbidden(self):
        """生徒としてCSVエクスポートを試行すると403エラーになるテスト"""
        # 生徒としてログイン
        self.client.login(username='student1', password='testpass123')
        
        # CSVエクスポートのリクエスト
        response = self.client.get(reverse('accounts:export_students_csv'))
        
        # リダイレクトの確認（権限なしの場合はログインページにリダイレクト）
        self.assertEqual(response.status_code, 302)
    
    def test_import_students_csv_valid_data(self):
        """有効なCSVデータでのインポートテスト"""
        # 教師としてログイン
        self.client.login(username='teacher', password='testpass123')
        
        # 新しい招待コード作成
        invitation_code = InvitationCode.objects.create(
            code='newstudent123',
            name='New Student',
            type='student'
        )
        
        # CSVデータ作成
        csv_content = "ユーザー名,名前,生年月日,入学年度,学科,専攻,学年,招待コード\n"
        csv_content += "newstudent,新規生徒,2002-03-03,2022,IT_sougou,SE,3,newstudent123\n"
        
        csv_file = SimpleUploadedFile(
            "students.csv",
            csv_content.encode('utf-8-sig'),
            content_type="text/csv"
        )
        
        # CSVインポートのリクエスト
        response = self.client.post(reverse('accounts:import_students_csv'), {
            'csv_file': csv_file
        })
        
        # 成功時のリダイレクトの確認
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:student_management'))
        
        # 新しいユーザーが作成されたことを確認
        new_user = self.User.objects.get(username='newstudent')
        self.assertEqual(new_user.name, '新規生徒')
        self.assertEqual(str(new_user.birth_date), '2002-03-03')
        self.assertEqual(new_user.admission_year, 2022)
        self.assertEqual(new_user.department, 'IT_sougou')
        self.assertEqual(new_user.major, 'SE')
        self.assertEqual(new_user.grade, '3')
        self.assertEqual(new_user.type, 'student')
    
    def test_import_students_csv_duplicate_username(self):
        """重複するユーザー名でのインポートテスト"""
        # 教師としてログイン
        self.client.login(username='teacher', password='testpass123')
        
        # 既存のユーザー名を含むCSVデータ作成
        csv_content = "ユーザー名,名前,生年月日,入学年度,学科,専攻,学年,招待コード\n"
        csv_content += "student1,重複生徒,2002-03-03,2022,IT_sougou,SE,3,student123\n"
        
        csv_file = SimpleUploadedFile(
            "students.csv",
            csv_content.encode('utf-8-sig'),
            content_type="text/csv"
        )
        
        # CSVインポートのリクエスト
        response = self.client.post(reverse('accounts:import_students_csv'), {
            'csv_file': csv_file
        })
        
        # エラーメッセージが表示されることを確認
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ユーザー名 student1 は既に存在します')
    
    def test_import_students_csv_invalid_invitation_code(self):
        """無効な招待コードでのインポートテスト"""
        # 教師としてログイン
        self.client.login(username='teacher', password='testpass123')
        
        # 無効な招待コードを含むCSVデータ作成
        csv_content = "ユーザー名,名前,生年月日,入学年度,学科,専攻,学年,招待コード\n"
        csv_content += "newstudent,新規生徒,2002-03-03,2022,IT_sougou,SE,3,invalid_code\n"
        
        csv_file = SimpleUploadedFile(
            "students.csv",
            csv_content.encode('utf-8-sig'),
            content_type="text/csv"
        )
        
        # CSVインポートのリクエスト
        response = self.client.post(reverse('accounts:import_students_csv'), {
            'csv_file': csv_file
        })
        
        # エラーメッセージが表示されることを確認
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '招待コード invalid_code が見つかりません')
    
    def test_student_management_page_access_as_teacher(self):
        """教師として生徒管理ページにアクセスするテスト"""
        # 教師としてログイン
        self.client.login(username='teacher', password='testpass123')
        
        # 生徒管理ページのリクエスト
        response = self.client.get(reverse('accounts:student_management'))
        
        # ページが正常に表示されることを確認
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '生徒管理')
        self.assertContains(response, 'CSVエクスポート')
        self.assertContains(response, 'CSVインポート')
        
        # 生徒一覧が表示されることを確認
        self.assertContains(response, 'student1')
        self.assertContains(response, 'テスト生徒1')
        self.assertContains(response, 'student2')
        self.assertContains(response, 'テスト生徒2')
    
    def test_student_management_page_access_as_student_forbidden(self):
        """生徒として生徒管理ページにアクセスすると403エラーになるテスト"""
        # 生徒としてログイン
        self.client.login(username='student1', password='testpass123')
        
        # 生徒管理ページのリクエスト
        response = self.client.get(reverse('accounts:student_management'))
        
        # リダイレクトの確認（権限なしの場合はログインページにリダイレクト）
        self.assertEqual(response.status_code, 302)
