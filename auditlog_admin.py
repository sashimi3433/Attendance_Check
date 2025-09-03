# auditlog_admin.py
# django-auditlogの管理画面設定

from django.contrib import admin
from auditlog.models import LogEntry
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

# 既存の登録を解除
if admin.site.is_registered(LogEntry):
    admin.site.unregister(LogEntry)

@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    """auditlogのLogEntryを管理画面で表示するための設定"""
    
    list_display = [
        'timestamp',
        'object_repr_short',
        'content_type',
        'action_display',
        'actor_display',
        'remote_addr',
        'changes_summary'
    ]
    
    list_filter = [
        'action',
        'content_type',
        'timestamp',
    ]
    
    search_fields = [
        'object_repr',
        'actor__username',
        'actor__name',
        'remote_addr'
    ]
    
    readonly_fields = [
        'timestamp',
        'object_id',
        'object_repr',
        'action',
        'changes_formatted',
        'actor',
        'remote_addr',
        'content_type'
    ]
    
    date_hierarchy = 'timestamp'
    
    ordering = ['-timestamp']
    
    def object_repr_short(self, obj):
        """オブジェクト表現を短縮表示"""
        if len(obj.object_repr) > 50:
            return obj.object_repr[:50] + '...'
        return obj.object_repr
    object_repr_short.short_description = 'オブジェクト'
    
    def action_display(self, obj):
        """アクションを日本語で表示"""
        action_map = {
            0: '作成',
            1: '更新', 
            2: '削除'
        }
        return action_map.get(obj.action, str(obj.action))
    action_display.short_description = 'アクション'
    
    def actor_display(self, obj):
        """実行者を表示（リンク付き）"""
        if obj.actor:
            if hasattr(obj.actor, 'name') and obj.actor.name:
                display_name = f"{obj.actor.name} ({obj.actor.username})"
            else:
                display_name = obj.actor.username
            
            url = reverse('admin:accounts_customuser_change', args=[obj.actor.pk])
            return format_html('<a href="{}">{}</a>', url, display_name)
        return 'システム'
    actor_display.short_description = '実行者'
    
    def changes_summary(self, obj):
        """変更内容の要約を表示"""
        if not obj.changes:
            return '-'
        
        changes = obj.changes
        if isinstance(changes, str):
            try:
                changes = json.loads(changes)
            except json.JSONDecodeError:
                return '変更内容の解析エラー'
        
        if isinstance(changes, dict):
            field_count = len(changes)
            if field_count == 1:
                field_name = list(changes.keys())[0]
                return f"{field_name}を変更"
            else:
                return f"{field_count}個のフィールドを変更"
        
        return '変更あり'
    changes_summary.short_description = '変更概要'
    
    def changes_formatted(self, obj):
        """変更内容を整形して表示"""
        if not obj.changes:
            return 'なし'
        
        changes = obj.changes
        if isinstance(changes, str):
            try:
                changes = json.loads(changes)
            except json.JSONDecodeError:
                return '変更内容の解析エラー'
        
        if isinstance(changes, dict):
            formatted_changes = []
            for field, (old_value, new_value) in changes.items():
                formatted_changes.append(
                    f"<strong>{field}:</strong> {old_value} → {new_value}"
                )
            return mark_safe('<br>'.join(formatted_changes))
        
        return str(changes)
    changes_formatted.short_description = '変更詳細'
    
    def has_add_permission(self, request):
        """ログエントリの追加を禁止"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """ログエントリの変更を禁止"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """ログエントリの削除を禁止（読み取り専用）"""
        return False