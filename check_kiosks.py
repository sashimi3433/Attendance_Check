#!/usr/bin/env python
import os
import django

# Django設定を読み込み
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myapp.settings')
django.setup()

from accounts.models import Kiosk, CustomUser

print('=== キオスクデータ調査 ===')
print(f'キオスク数: {Kiosk.objects.count()}')
print('\nキオスク一覧:')
for k in Kiosk.objects.all():
    print(f'ID: {k.id}, 名前: {k.name}, 講師: {k.teacher}')

print('\n=== 講師データ調査 ===')
teachers = CustomUser.objects.filter(type='teacher')
print(f'講師数: {teachers.count()}')
for teacher in teachers:
    print(f'講師ID: {teacher.id}, 名前: {teacher.username}, タイプ: {teacher.type}')

print('\n=== キオスクと講師の関係調査 ===')
for k in Kiosk.objects.all():
    print(f'キオスク「{k.name}」の講師: {k.teacher.username if k.teacher else "未設定"}')