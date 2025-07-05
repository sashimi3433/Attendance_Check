# -*- coding: utf-8 -*-
from django import forms
from accounts.models import CustomUser, grade as GRADE_CHOICES

class UserSearchForm(forms.Form):
    username = forms.CharField(
        label='ユーザー名',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '一部でも可'})
    )
    name = forms.CharField(
        label='名前',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '一部でも可'})
    )
    grade = forms.ChoiceField(
        label='学年',
        required=False,
        choices=[('', '--------')] + list(GRADE_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    age = forms.IntegerField(
        label='年齢',
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    search_type = forms.ChoiceField(
        label='検索方法',
        choices=[
            ('AND', 'AND検索 (すべての条件に一致)'),
            ('OR', 'OR検索 (いずれかの条件に一致)'),
        ],
        required=True,
        widget=forms.RadioSelect
    )
