# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import CustomUserChangeForm, CustomUserCreationForm, PasswordlessLoginForm
from .models import CustomUser
from django.shortcuts import get_object_or_404

# Staff check decorator
def staff_required(view_func):
    decorated_view_func = user_passes_test(
        lambda u: u.is_active and u.is_staff,
        login_url='home:index'  # Redirect if not staff
    )(view_func)
    return decorated_view_func


@login_required
def profile_edit(request):
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
            name = form.cleaned_data['name']
            grade = form.cleaned_data['grade']
            age = form.cleaned_data['age']
            user = authenticate(request, username=username, name=name, grade=grade, age=age)
            if user is not None:
                login(request, user, backend='accounts.backends.PasswordlessAuthBackend')
                messages.success(request, 'ログインしました。')
                return redirect('home:index')
            else:
                messages.error(request, '入力された情報と一致するユーザーが見つかりません。')
    else:
        form = PasswordlessLoginForm()
    return render(request, 'accounts/passwordless_login.html', {'form': form})


@staff_required
def admin_menu(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        if user_id:
            return redirect('accounts:admin_user_detail', user_id=user_id)
    return render(request, 'accounts/admin/admin_menu.html')

@staff_required
def admin_user_detail(request, user_id):
    target_user = get_object_or_404(CustomUser, pk=user_id)
    return render(request, 'accounts/admin/user_detail.html', {'target_user': target_user})

@staff_required
def admin_edit_user(request, user_id):
    target_user = get_object_or_404(CustomUser, pk=user_id)
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=target_user)
        if form.is_valid():
            form.save()
            messages.success(request, f'{target_user.username}の情報を更新しました。')
            return redirect('accounts:admin_user_detail', user_id=user_id)
    else:
        form = CustomUserChangeForm(instance=target_user)
    return render(request, 'accounts/admin/edit_user.html', {'form': form, 'target_user': target_user})