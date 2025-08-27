from django.contrib import admin
from .models import TeacherDashboardSettings


@admin.register(TeacherDashboardSettings)
class TeacherDashboardSettingsAdmin(admin.ModelAdmin):
    list_display = (
        'teacher',
        'default_period_days',
        'records_per_page',
        'email_notifications',
        'daily_report',
        'weekly_report',
        'created_at',
        'updated_at'
    )
    list_filter = (
        'email_notifications',
        'daily_report',
        'weekly_report',
        'created_at'
    )
    search_fields = (
        'teacher__username',
        'teacher__name',
        'teacher__email'
    )
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('基本情報', {
            'fields': ('teacher',)
        }),
        ('表示設定', {
            'fields': (
                'default_period_days',
                'records_per_page'
            )
        }),
        ('通知設定', {
            'fields': (
                'email_notifications',
                'daily_report',
                'weekly_report'
            )
        }),
        ('タイムスタンプ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        """講師タイプのユーザーの設定のみ表示"""
        qs = super().get_queryset(request)
        return qs.filter(teacher__type='teacher')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """講師タイプのユーザーのみ選択可能にする"""
        if db_field.name == 'teacher':
            kwargs['queryset'] = db_field.related_model.objects.filter(type='teacher')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def has_add_permission(self, request):
        """管理者のみ追加可能"""
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """管理者または設定の所有者のみ変更可能"""
        if request.user.is_superuser:
            return True
        if obj and hasattr(request.user, 'type') and request.user.type == 'teacher':
            return obj.teacher == request.user
        return False
    
    def has_delete_permission(self, request, obj=None):
        """管理者のみ削除可能"""
        return request.user.is_superuser