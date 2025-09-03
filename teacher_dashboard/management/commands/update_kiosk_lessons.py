from django.core.management.base import BaseCommand
from accounts.models import Kiosk, Lesson

class Command(BaseCommand):
    help = 'キオスクの現在のレッスンを最新のアクティブなレッスンに更新'

    def handle(self, *args, **options):
        # アクティブで受付中のレッスンを取得
        active_lesson = Lesson.objects.filter(is_active=True, reception=True).first()
        
        if not active_lesson:
            self.stdout.write(self.style.WARNING('アクティブで受付中のレッスンが見つかりません'))
            return
        
        self.stdout.write(f'アクティブなレッスン: {active_lesson.subject} (ID: {active_lesson.id}, 場所: {active_lesson.location})')
        
        # 該当する場所のキオスクを更新
        kiosks_updated = 0
        for kiosk in Kiosk.objects.all():
            # レッスンの場所とキオスクの場所が一致する場合に更新
            if active_lesson.location and kiosk.location:
                # "208教室" と "208教室" の完全一致、または "208" が含まれる場合
                if (active_lesson.location == kiosk.location or 
                    active_lesson.location.replace('教室', '') in kiosk.location or
                    kiosk.location.replace('教室', '') in active_lesson.location):
                    
                    old_lesson = kiosk.current_lesson
                    kiosk.current_lesson = active_lesson
                    kiosk.save()
                    
                    self.stdout.write(
                        f'キオスク {kiosk.user.username} ({kiosk.location}) のレッスンを更新: '
                        f'{old_lesson} → {active_lesson}'
                    )
                    kiosks_updated += 1
        
        if kiosks_updated == 0:
            self.stdout.write(self.style.WARNING('更新されたキオスクがありません'))
        else:
            self.stdout.write(self.style.SUCCESS(f'{kiosks_updated}台のキオスクを更新しました'))
        
        # 更新後の状態を確認
        self.stdout.write('\n=== 更新後のキオスク状態 ===')
        for kiosk in Kiosk.objects.all():
            self.stdout.write(
                f'キオスク: {kiosk.user.username} ({kiosk.location}) - '
                f'現在のレッスン: {kiosk.current_lesson}'
            )