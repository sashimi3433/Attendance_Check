# attendance_token/management/commands/test_ip_detection.py
# IP取得機能のテスト用管理コマンド

from django.core.management.base import BaseCommand
from django.test import RequestFactory
from django.conf import settings
import logging
from attendance_token.utils import (
    get_client_ip,
    get_global_ip_from_external_service,
    _is_local_request,
    _is_private_ip,
    _is_valid_global_ip
)


class Command(BaseCommand):
    help = 'IP取得機能のテスト'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='詳細なログを表示',
        )
        parser.add_argument(
            '--test-external-only',
            action='store_true',
            help='外部サービスのみをテスト',
        )
    
    def handle(self, *args, **options):
        # ログレベルの設定
        if options['verbose']:
            logging.getLogger('attendance_token.utils').setLevel(logging.DEBUG)
            logging.getLogger('ip_security').setLevel(logging.DEBUG)
        
        self.stdout.write(self.style.SUCCESS('=== IP取得機能テスト開始 ==='))
        
        # 設定情報の表示
        self._display_config()
        
        if options['test_external_only']:
            # 外部サービスのみテスト
            self._test_external_services()
        else:
            # 完全なテスト
            self._test_full_ip_detection()
        
        self.stdout.write(self.style.SUCCESS('=== IP取得機能テスト完了 ==='))
    
    def _display_config(self):
        """現在の設定を表示"""
        self.stdout.write(self.style.WARNING('\n--- 現在の設定 ---'))
        
        external_config = getattr(settings, 'EXTERNAL_IP_SERVICES', {})
        
        config_items = [
            ('ENABLED', external_config.get('ENABLED', False)),
            ('TIMEOUT', external_config.get('TIMEOUT', 5)),
            ('FORCE_EXTERNAL_FOR_LOCAL', external_config.get('FORCE_EXTERNAL_FOR_LOCAL', False)),
            ('DEBUG_IP_DETECTION', external_config.get('DEBUG_IP_DETECTION', False)),
            ('LOCAL_DEVELOPMENT_MODE', external_config.get('LOCAL_DEVELOPMENT_MODE', False)),
            ('FALLBACK_TO_HEADERS', external_config.get('FALLBACK_TO_HEADERS', True)),
        ]
        
        for key, value in config_items:
            self.stdout.write(f'{key}: {value}')
        
        services = external_config.get('SERVICES', [])
        self.stdout.write(f'外部サービス数: {len(services)}')
        for i, service in enumerate(services, 1):
            self.stdout.write(f'  {i}. {service}')
    
    def _test_external_services(self):
        """外部サービスのテスト"""
        self.stdout.write(self.style.WARNING('\n--- 外部サービステスト ---'))
        
        global_ip = get_global_ip_from_external_service()
        
        if global_ip:
            self.stdout.write(
                self.style.SUCCESS(f'✓ 外部サービスからグローバルIP取得成功: {global_ip}')
            )
            
            # IPの妥当性チェック
            if _is_valid_global_ip(global_ip):
                self.stdout.write(
                    self.style.SUCCESS(f'✓ 取得されたIPは有効なグローバルIPです')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ 取得されたIPは無効です')
                )
        else:
            self.stdout.write(
                self.style.ERROR('✗ 外部サービスからのIP取得に失敗')
            )
    
    def _test_full_ip_detection(self):
        """完全なIP取得テスト"""
        self.stdout.write(self.style.WARNING('\n--- 完全なIP取得テスト ---'))
        
        # モックリクエストの作成
        factory = RequestFactory()
        
        # テストケース1: ローカルホストリクエスト
        self.stdout.write('\n1. ローカルホストリクエストのテスト:')
        local_request = factory.get('/', HTTP_HOST='localhost:8000')
        local_request.META['REMOTE_ADDR'] = '127.0.0.1'
        
        is_local = _is_local_request(local_request)
        self.stdout.write(f'   ローカルリクエスト判定: {is_local}')
        
        local_ip = get_client_ip(local_request)
        self.stdout.write(f'   取得されたIP: {local_ip}')
        
        if _is_private_ip(local_ip):
            self.stdout.write('   → プライベートIPです')
        elif _is_valid_global_ip(local_ip):
            self.stdout.write('   → グローバルIPです')
        else:
            self.stdout.write('   → 無効なIPです')
        
        # テストケース2: プロキシ経由リクエスト
        self.stdout.write('\n2. プロキシ経由リクエストのテスト:')
        proxy_request = factory.get('/', HTTP_HOST='example.com')
        proxy_request.META['REMOTE_ADDR'] = '192.168.1.100'
        proxy_request.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.1, 192.168.1.100'
        
        is_local_proxy = _is_local_request(proxy_request)
        self.stdout.write(f'   ローカルリクエスト判定: {is_local_proxy}')
        
        proxy_ip = get_client_ip(proxy_request)
        self.stdout.write(f'   取得されたIP: {proxy_ip}')
        
        if _is_private_ip(proxy_ip):
            self.stdout.write('   → プライベートIPです')
        elif _is_valid_global_ip(proxy_ip):
            self.stdout.write('   → グローバルIPです')
        else:
            self.stdout.write('   → 無効なIPです')
        
        # テストケース3: 外部サービス強制使用
        self.stdout.write('\n3. 外部サービス強制使用テスト:')
        external_config = getattr(settings, 'EXTERNAL_IP_SERVICES', {})
        if external_config.get('FORCE_EXTERNAL_FOR_LOCAL', False):
            force_request = factory.get('/', HTTP_HOST='localhost:8000')
            force_request.META['REMOTE_ADDR'] = '127.0.0.1'
            
            force_ip = get_client_ip(force_request)
            self.stdout.write(f'   強制外部サービス使用時のIP: {force_ip}')
            
            if _is_valid_global_ip(force_ip):
                self.stdout.write(
                    self.style.SUCCESS('   ✓ ローカル環境でもグローバルIP取得成功')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('   ⚠ グローバルIP取得に失敗、フォールバック使用')
                )
        else:
            self.stdout.write('   FORCE_EXTERNAL_FOR_LOCALが無効です')
        
        # 設定の推奨事項
        self._display_recommendations()
    
    def _display_recommendations(self):
        """設定の推奨事項を表示"""
        self.stdout.write(self.style.WARNING('\n--- 推奨設定 ---'))
        
        external_config = getattr(settings, 'EXTERNAL_IP_SERVICES', {})
        
        recommendations = []
        
        if not external_config.get('ENABLED', False):
            recommendations.append('ENABLED を True に設定してください')
        
        if not external_config.get('FORCE_EXTERNAL_FOR_LOCAL', False):
            recommendations.append(
                'ローカル環境でもグローバルIPを取得するため、'
                'FORCE_EXTERNAL_FOR_LOCAL を True に設定してください'
            )
        
        if not external_config.get('DEBUG_IP_DETECTION', False):
            recommendations.append(
                'デバッグ情報を確認するため、'
                'DEBUG_IP_DETECTION を True に設定してください'
            )
        
        if recommendations:
            for rec in recommendations:
                self.stdout.write(f'• {rec}')
        else:
            self.stdout.write(
                self.style.SUCCESS('✓ 設定は適切に構成されています')
            )