from django.core.management.base import BaseCommand
from accounts.models import Lesson, Kiosk
from django.utils import timezone

class Command(BaseCommand):
    help = 'レッスンとキオスクの状態を確認'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== レッスン状態確認 ==='))
        
        # アクティブなレッスンを確認
        active_lessons = Lesson.objects.filter(is_active=True)
        self.stdout.write(f'アクティブなレッスン数: {active_lessons.count()}')
        
        for lesson in active_lessons:
            self.stdout.write(f'レッスンID: {lesson.id}')
            self.stdout.write(f'科目: {lesson.subject}')
            self.stdout.write(f'講師: {lesson.teacher.user.username}')
            self.stdout.write(f'場所: {lesson.location}')
            self.stdout.write(f'受付中: {lesson.reception}')
            self.stdout.write(f'作成日時: {lesson.created_at}')
            self.stdout.write('---')
        
        # 受付中のレッスンを確認
        reception_lessons = Lesson.objects.filter(reception=True)
        self.stdout.write(f'\n受付中のレッスン数: {reception_lessons.count()}')
        
        for lesson in reception_lessons:
            self.stdout.write(f'レッスンID: {lesson.id}')
            self.stdout.write(f'科目: {lesson.subject}')
            self.stdout.write(f'場所: {lesson.location}')
            self.stdout.write(f'アクティブ: {lesson.is_active}')
            self.stdout.write('---')
        
        # キオスクの状態を確認
        self.stdout.write(self.style.SUCCESS('\n=== キオスク状態確認 ==='))
        kiosks = Kiosk.objects.all()
        self.stdout.write(f'キオスク数: {kiosks.count()}')
        
        for kiosk in kiosks:
            self.stdout.write(f'キオスクユーザー: {kiosk.user.username}')
            self.stdout.write(f'場所: {kiosk.location}')
            if kiosk.current_lesson:
                self.stdout.write(f'現在のレッスン: {kiosk.current_lesson.subject} (ID: {kiosk.current_lesson.id})')
                self.stdout.write(f'レッスンアクティブ: {kiosk.current_lesson.is_active}')
                self.stdout.write(f'レッスン受付中: {kiosk.current_lesson.reception}')
            else:
                self.stdout.write('現在のレッスン: なし')
            self.stdout.write('---')
        
        # 最近作成されたレッスンを確認
        self.stdout.write(self.style.SUCCESS('\n=== 最近のレッスン（最新5件） ==='))
        recent_lessons = Lesson.objects.all().order_by('-created_at')[:5]
        
        for lesson in recent_lessons:
            self.stdout.write(f'レッスンID: {lesson.id}')
            self.stdout.write(f'科目: {lesson.subject}')
            self.stdout.write(f'場所: {lesson.location}')
            self.stdout.write(f'アクティブ: {lesson.is_active}')
            self.stdout.write(f'受付中: {lesson.reception}')
            self.stdout.write(f'作成日時: {lesson.created_at}')
            self.stdout.write('---')