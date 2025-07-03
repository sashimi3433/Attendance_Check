# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import CustomUserChangeForm, CustomUserCreationForm, PasswordlessLoginForm

@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('home:home-account')  # Redirect to the account page after a successful edit
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'accounts/profile_edit.html', {'form': form})

def signup(request):
    """
    パスワードなしでの新規ユーザー登録
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 自動的にログインさせる
            login(request, user, backend='accounts.backends.PasswordlessAuthBackend')
            messages.success(request, 'アカウントが作成されました。')
            return redirect('home:index')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})

def passwordless_login(request):
    """
    パスワードなしでのログイン
    """
    if request.method == 'POST':
        form = PasswordlessLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            user = authenticate(request, username=username)
            if user is not None:
                login(request, user, backend='accounts.backends.PasswordlessAuthBackend')
                messages.success(request, 'ログインしました。')
                return redirect('home:index')
            else:
                messages.error(request, 'ユーザー名が見つかりません。')
    else:
        form = PasswordlessLoginForm()
    return render(request, 'accounts/passwordless_login.html', {'form': form})