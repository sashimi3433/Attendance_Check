# attendance_token/management/commands/cleanup_tokens.py
# 未使用の期限切れトークンを削除するDjango管理コマンド
from django.core.management.base import BaseCommand
from django.utils import timezone
from attendance_token.models import AttendanceToken
from datetime import timedelta


class Command(BaseCommand):
    """
    未使用で期限切れのトークンを削除するコマンド
    
    使用方法:
    python manage.py cleanup_tokens
    
    オプション:
    --minutes: 何分前のトークンを削除するか（デフォルト: 10分）
    --dry-run: 実際に削除せず、削除対象のトークン数のみ表示
    """
    help = '未使用で期限切れのトークンを削除します'

    def add_arguments(self, parser):
        """コマンドライン引数を追加"""
        parser.add_argument(
            '--minutes',
            type=int,
            default=10,
            help='何分前のトークンを削除するか（デフォルト: 10分）'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='実際に削除せず、削除対象のトークン数のみ表示'
        )

    def handle(self, *args, **options):
        """コマンドのメイン処理"""
        minutes = options['minutes']
        dry_run = options['dry_run']
        
        # 指定された分数前の時刻を計算
        cutoff_time = timezone.now() - timedelta(minutes=minutes)
        
        # 削除対象のトークンを取得
        # 条件: 未使用 かつ 期限切れ かつ 指定時間より古い
        tokens_to_delete = AttendanceToken.objects.filter(
            is_used=False,
            expires__lt=cutoff_time
        )
        
        count = tokens_to_delete.count()
        
        if dry_run:
            # ドライランモード: 削除対象の数のみ表示
            self.stdout.write(
                self.style.WARNING(
                    f'[ドライラン] 削除対象のトークン数: {count}件'
                )
            )
            if count > 0:
                self.stdout.write('削除対象のトークン:')
                for token in tokens_to_delete[:10]:  # 最初の10件のみ表示
                    self.stdout.write(
                        f'  - {token.user.username}: {token.token[:10]}... '
                        f'(作成: {token.created.strftime("%Y-%m-%d %H:%M:%S")})'
                    )
                if count > 10:
                    self.stdout.write(f'  ... 他 {count - 10}件')
        else:
            # 実際に削除を実行
            if count > 0:
                deleted_count, _ = AttendanceToken.cleanup_expired_tokens(minutes)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'未使用の期限切れトークンを {deleted_count}件 削除しました'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('削除対象のトークンはありませんでした')
                )
        
        # 統計情報を表示
        stats = AttendanceToken.get_cleanup_statistics()
        
        self.stdout.write('\n=== トークン統計 ===')
        self.stdout.write(f'総トークン数: {stats["total"]}件')
        self.stdout.write(f'使用済み: {stats["used"]}件')
        self.stdout.write(f'未使用: {stats["unused"]}件')
        self.stdout.write(f'期限切れ未使用: {stats["expired_unused"]}件')