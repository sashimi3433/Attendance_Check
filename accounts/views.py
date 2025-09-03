# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponse
from functools import wraps
import csv
import io
from .forms import CustomUserChangeForm, CustomUserCreationForm, CustomAuthenticationForm
from .models import CustomUser, department_choices, major_choices, grade_choices
from .utils import invalidate_user_sessions


def user_type_required(user_type):
    """
    指定されたユーザータイプのみアクセスを許可するデコレータ
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.type != user_type:
                # 現在のページがすでに適切なリダイレクト先の場合はリダイレクトしない
                if user_type == 'kiosk' and request.path.startswith('/checkin/'):
                    return view_func(request, *args, **kwargs)
                elif user_type == 'teacher' and request.path.startswith('/teacher/'):
                    return view_func(request, *args, **kwargs)

                # それ以外の場合は適切なページにリダイレクト
                if user_type == 'kiosk':
                    return redirect('checkin:qr_scanner')
                elif user_type == 'teacher':
                    return redirect('teacher_dashboard:index')
                else:
                    return redirect('home:index')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator




@login_required
def profile_edit(request):
    # キオスクアカウントの場合はQRスキャナーページにリダイレクト
    if request.user.type == 'kiosk':
        return redirect('checkin:qr_scanner')
    
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('home:account')  # Redirect to the account page after a successful edit
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'accounts/profile_edit.html', {'form': form})

def signup(request):
    """
    パスワード付きの新規ユーザー登録
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 自動的にログインさせる
            login(request, user)
            messages.success(request, 'アカウントが作成されました。')
            return redirect('home:index')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})

def custom_login(request):
    """
    カスタムログインビュー
    複数端末からの同時ログインを防止し、既存セッションを無効化する
    """
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                # 既存のセッションを無効化（現在のセッションは除外）
                invalidate_user_sessions(user, exclude_session_key=request.session.session_key)
                
                # ログイン処理
                login(request, user)
                
                # 新しいセッションキーをユーザーに保存
                user.current_session_key = request.session.session_key
                user.save(update_fields=['current_session_key'])
                
                messages.success(request, 'ログインしました。')
                # ログイン後はホームにリダイレクト（home/indexでユーザータイプに応じた処理を行う）
                return redirect('home:index')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

@login_required
def custom_logout(request):
    """
    カスタムログアウトビュー
    ログアウト時にユーザーのセッション情報をクリアする
    """
    if request.user.is_authenticated:
        # ユーザーのセッション情報をクリア
        request.user.current_session_key = None
        request.user.save(update_fields=['current_session_key'])
    
    logout(request)
    messages.success(request, 'ログアウトしました。')
    return redirect('accounts:login')


@user_type_required('teacher')
def export_students_csv(request):
    """
    生徒データをCSV形式でエクスポートする
    """
    # 生徒のみを取得
    students = CustomUser.objects.filter(type='student').order_by('username')
    
    # HTTPレスポンスの設定
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="students.csv"'
    
    # BOMを追加してExcelで正しく表示されるようにする
    response.write('\ufeff')
    
    writer = csv.writer(response)
    
    # ヘッダー行を書き込み
    writer.writerow([
        'ユーザー名',
        '名前',
        '生年月日',
        '入学年度',
        '学科',
        '専攻',
        '学年'
    ])
    
    # 生徒データを書き込み
    for student in students:
        writer.writerow([
            student.username,
            student.name or '',
            student.birth_date.strftime('%Y-%m-%d') if student.birth_date else '',
            student.admission_year or '',
            dict(department_choices).get(student.department, student.department),
            dict(major_choices).get(student.major, student.major),
            dict(grade_choices).get(student.grade, student.grade)
        ])
    
    return response


@user_type_required('teacher')
def import_students_csv(request):
    """
    CSVファイルから生徒データをインポートする
    """
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        
        if not csv_file:
            messages.error(request, 'CSVファイルを選択してください。')
            return render(request, 'accounts/import_students.html')
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'CSVファイルを選択してください。')
            return render(request, 'accounts/import_students.html')
        
        try:
            # CSVファイルを読み込み
            decoded_file = csv_file.read().decode('utf-8-sig')
            io_string = io.StringIO(decoded_file)
            reader = csv.reader(io_string)
            
            # ヘッダー行をスキップ
            next(reader, None)
            
            success_count = 0
            error_count = 0
            errors = []
            
            for row_num, row in enumerate(reader, start=2):
                if len(row) < 8:  # 最低限必要な列数をチェック（招待コード含む）
                    error_count += 1
                    errors.append(f'行{row_num}: 列数が不足しています')
                    continue
                
                username = row[0].strip()
                name = row[1].strip()
                birth_date_str = row[2].strip()
                admission_year_str = row[3].strip()
                department = row[4].strip()
                major = row[5].strip()
                grade = row[6].strip()
                invitation_code_str = row[7].strip()
                
                # バリデーション
                if not username:
                    error_count += 1
                    errors.append(f'行{row_num}: ユーザー名が空です')
                    continue
                
                # ユーザー名の重複チェック
                if CustomUser.objects.filter(username=username).exists():
                    error_count += 1
                    errors.append(f'ユーザー名 {username} は既に存在します')
                    continue
                
                # 招待コードの確認
                invitation_code = None
                if invitation_code_str:
                    try:
                        from .models import InvitationCode
                        invitation_code = InvitationCode.objects.get(code=invitation_code_str, type='student')
                    except InvitationCode.DoesNotExist:
                        error_count += 1
                        errors.append(f'招待コード {invitation_code_str} が見つかりません')
                        continue
                
                # 生年月日の変換
                birth_date = None
                if birth_date_str:
                    try:
                        from datetime import datetime
                        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        error_count += 1
                        errors.append(f'行{row_num}: 生年月日の形式が正しくありません（YYYY-MM-DD形式で入力してください）')
                        continue
                
                # 入学年度の変換
                admission_year = None
                if admission_year_str:
                    try:
                        admission_year = int(admission_year_str)
                    except ValueError:
                        error_count += 1
                        errors.append(f'行{row_num}: 入学年度は数値で入力してください')
                        continue
                
                # 学科の選択肢チェック
                department_codes = [code for code, _ in department_choices]
                if department and department not in department_codes:
                    # 日本語名から英語コードに変換を試行
                    department_dict = {name: code for code, name in department_choices}
                    if department in department_dict:
                        department = department_dict[department]
                    else:
                        error_count += 1
                        errors.append(f'行{row_num}: 学科「{department}」は無効です')
                        continue
                
                # 専攻の選択肢チェック
                major_codes = [code for code, _ in major_choices]
                if major and major not in major_codes:
                    # 日本語名から英語コードに変換を試行
                    major_dict = {name: code for code, name in major_choices}
                    if major in major_dict:
                        major = major_dict[major]
                    else:
                        error_count += 1
                        errors.append(f'行{row_num}: 専攻「{major}」は無効です')
                        continue
                
                # 学年の選択肢チェック
                grade_codes = [code for code, _ in grade_choices]
                if grade and grade not in grade_codes:
                    # 日本語名から数字コードに変換を試行
                    grade_dict = {name: code for code, name in grade_choices}
                    if grade in grade_dict:
                        grade = grade_dict[grade]
                    else:
                        error_count += 1
                        errors.append(f'行{row_num}: 学年「{grade}」は無効です')
                        continue
                
                try:
                    # 生徒ユーザーを作成
                    user = CustomUser.objects.create_user(
                        username=username,
                        name=name,
                        birth_date=birth_date,
                        admission_year=admission_year,
                        department=department or 'other',
                        major=major,
                        grade=grade,
                        type='student',
                        invitation_code=invitation_code
                    )
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f'行{row_num}: ユーザー作成エラー - {str(e)}')
            
            # 結果メッセージ
            if success_count > 0:
                messages.success(request, f'{success_count}件の生徒データをインポートしました。')
            
            if error_count > 0:
                error_message = f'{error_count}件のエラーがありました。\n' + '\n'.join(errors[:10])
                if len(errors) > 10:
                    error_message += f'\n...他{len(errors) - 10}件のエラー'
                messages.error(request, error_message)
                return render(request, 'accounts/import_students.html')
            
            # エラーがない場合はリダイレクト
            if error_count == 0:
                return redirect('accounts:student_management')
            
        except Exception as e:
            messages.error(request, f'CSVファイルの処理中にエラーが発生しました: {str(e)}')
    
    return render(request, 'accounts/import_students.html')


@user_type_required('teacher')
def student_management(request):
    """
    生徒管理ページ（CSVインポート・エクスポートのメニュー）
    """
    students = CustomUser.objects.filter(type='student').order_by('username')
    return render(request, 'accounts/student_management.html', {'students': students})