# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from functools import wraps
from .forms import CustomUserChangeForm, CustomUserCreationForm, CustomAuthenticationForm
from .models import CustomUser


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
    """
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'ログインしました。')
                # ログイン後はホームにリダイレクト（home/indexでユーザータイプに応じた処理を行う）
                return redirect('home:index')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})