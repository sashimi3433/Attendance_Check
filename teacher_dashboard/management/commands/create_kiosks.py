from django.core.management.base import BaseCommand
from accounts.models import CustomUser, Kiosk, Lesson
from django.db import transaction

class Command(BaseCommand):
    help = 'キオスクデータを作成し、アクティブなレッスンと関連付ける'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== キオスク作成開始 ==='))
        
        # 教室の定義
        locations = {
            'Room207': '207教室',
            'Room208': '208教室', 
            'Room204': '204教室',
        }
        
        with transaction.atomic():
            for room_code, room_name in locations.items():
                # キオスクユーザーを作成または取得
                kiosk_user, created = CustomUser.objects.get_or_create(
                    username=room_code,
                    defaults={
                        'name': room_name,
                        'type': 'kiosk',
                        'is_staff': False,
                        'is_active': True,
                    }
                )
                
                if created:
                    self.stdout.write(f'キオスクユーザー作成: {room_code}')
                else:
                    self.stdout.write(f'キオスクユーザー既存: {room_code}')
                
                # キオスクプロファイルを作成または取得
                kiosk, kiosk_created = Kiosk.objects.get_or_create(
                    user=kiosk_user,
                    defaults={
                        'location': room_name,
                        'is_active': True,
                    }
                )
                
                if kiosk_created:
                    self.stdout.write(f'キオスクプロファイル作成: {room_name}')
                else:
                    self.stdout.write(f'キオスクプロファイル既存: {room_name}')
                
                # 該当する場所のアクティブなレッスンを検索
                active_lesson = Lesson.objects.filter(
                    location=room_name,
                    is_active=True,
                    reception=True
                ).first()
                
                if active_lesson:
                    kiosk.current_lesson = active_lesson
                    kiosk.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'キオスク {room_name} にレッスン {active_lesson.subject} (ID: {active_lesson.id}) を関連付けました'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'キオスク {room_name} に関連付けるアクティブなレッスンが見つかりません'
                        )
                    )
        
        self.stdout.write(self.style.SUCCESS('\n=== 作成後の状態確認 ==='))
        
        # 作成後の状態を確認
        kiosks = Kiosk.objects.all()
        for kiosk in kiosks:
            self.stdout.write(f'キオスク: {kiosk.user.username} ({kiosk.location})')
            if kiosk.current_lesson:
                self.stdout.write(f'  現在のレッスン: {kiosk.current_lesson.subject} (ID: {kiosk.current_lesson.id})')
                self.stdout.write(f'  レッスンアクティブ: {kiosk.current_lesson.is_active}')
                self.stdout.write(f'  レッスン受付中: {kiosk.current_lesson.reception}')
            else:
                self.stdout.write('  現在のレッスン: なし')
            self.stdout.write('---')
        
        self.stdout.write(self.style.SUCCESS('キオスク作成完了'))