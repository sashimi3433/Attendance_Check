# -*- coding: utf-8 -*-
from django.contrib.auth.forms import UserChangeForm, AuthenticationForm
from django import forms
from .models import CustomUser

class CustomUserChangeForm(UserChangeForm):
    password = None  # パスワードフィールドを完全に除外
    
    class Meta:
        model = CustomUser
        fields = ('username', 'name', 'grade', 'age')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # パスワード関連のフィールドを削除
        if 'password' in self.fields:
            del self.fields['password']

class CustomUserCreationForm(forms.ModelForm):
    """
    パスワードなしでの新規ユーザー作成フォーム
    """
    class Meta:
        model = CustomUser
        fields = ('username', 'name', 'grade', 'age')
        labels = {
            'username': 'ユーザー名',
            'name': '名前',
            'grade': '学年',
            'age': '年齢',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ユーザー名を入力してください'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '名前を入力してください'}),
            'grade': forms.Select(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '年齢を入力してください'}),
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # パスワードを設定しない（unusable passwordに設定）
        user.set_unusable_password()
        if commit:
            user.save()
        return user

class PasswordlessLoginForm(forms.Form):
    """
    パスワードなしでのログインフォーム
    """
    username = forms.CharField(
        label='ユーザー名',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ユーザー名を入力してください',
            'autofocus': True
        })
    )