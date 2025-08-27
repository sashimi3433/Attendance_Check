# -*- coding: utf-8 -*-
from django.contrib.auth.forms import UserChangeForm, AuthenticationForm, UserCreationForm
from django import forms
from .models import CustomUser, InvitationCode, department_choices

class CustomUserChangeForm(UserChangeForm):
    password = None  # パスワードフィールドを完全に除外
    
    class Meta:
        model = CustomUser
        fields = ('username', 'name', 'type', 'birth_date', 'admission_year', 'department')
        labels = {
            'username': 'ユーザー名',
            'name': '名前',
            'type': 'アカウント種別',
            'birth_date': '生年月日',
            'admission_year': '入学年度',
            'department': '学科',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'admission_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # パスワード関連のフィールドを削除
        if 'password' in self.fields:
            del self.fields['password']

class CustomUserCreationForm(UserCreationForm):
    """
    パスワード付きの新規ユーザー作成フォーム（招待コード必須）
    """
    invitation_code = forms.CharField(
        label='招待コード',
        max_length=5,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '5桁の招待コードを入力してください'
        }),
        help_text='登録には有効な招待コードが必要です'
    )
    name = forms.CharField(
        label='名前',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '名前を入力してください'
        })
    )
    birth_date = forms.DateField(
        label='生年月日',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    admission_year = forms.IntegerField(
        label='入学年度',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '入学年度を入力してください（例：2024）'
        })
    )
    department = forms.ChoiceField(
        label='学科',
        choices=department_choices,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    account_type = forms.ChoiceField(
        label='アカウント種別',
        choices=[
            ('student', '生徒'),
            ('teacher', '講師'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = CustomUser
        fields = ('invitation_code', 'username', 'password1', 'password2', 'name', 'birth_date', 'admission_year', 'department', 'account_type')
        labels = {
            'username': 'ユーザー名',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ユーザー名を入力してください'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'パスワードを入力してください'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'パスワードを再入力してください'})
    
    def clean_invitation_code(self):
        """
        招待コードの検証（アカウント種別との整合性もチェック）
        """
        code = self.cleaned_data.get('invitation_code')
        account_type = self.cleaned_data.get('account_type')
        
        if code:
            try:
                invitation = InvitationCode.objects.get(code=code, is_active=True)
                # アカウント種別と招待コードの種別が一致するかチェック
                if account_type == 'teacher' and invitation.type != 'teacher':
                    raise forms.ValidationError('講師アカウントの登録には講師用の招待コードが必要です。')
                elif account_type == 'student' and invitation.type != 'student':
                    raise forms.ValidationError('生徒アカウントの登録には生徒用の招待コードが必要です。')
                return code
            except InvitationCode.DoesNotExist:
                raise forms.ValidationError('無効な招待コードです。')
        raise forms.ValidationError('招待コードは必須です。')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.name = self.cleaned_data['name']
        user.birth_date = self.cleaned_data['birth_date']
        user.admission_year = self.cleaned_data['admission_year']
        user.department = self.cleaned_data['department']
        user.type = self.cleaned_data['account_type']  # アカウント種別を設定
        
        # 招待コードを関連付け
        invitation_code = self.cleaned_data['invitation_code']
        invitation = InvitationCode.objects.get(code=invitation_code, is_active=True)
        user.invitation_code = invitation
        
        if commit:
            user.save()
            # 招待コードの使用回数を増加
            invitation.used_count += 1
            invitation.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    """
    カスタマイズされたログインフォーム
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'ユーザー名を入力してください',
            'autofocus': True
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'パスワードを入力してください'
        })