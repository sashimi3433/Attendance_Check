from django.contrib import admin
from .models import AttendanceToken, AttendanceRecord


@admin.register(AttendanceToken)
class AttendanceTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'is_used', 'expires', 'created']
    list_filter = ['is_used', 'created', 'expires']
    search_fields = ['user__username', 'token']
    readonly_fields = ['token', 'created', 'updated']
    ordering = ['-created']


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'attended_at', 'location', 'kiosk', 'get_teacher_name', 'token']
    list_filter = ['attended_at', 'location', 'kiosk']
    search_fields = ['user__username', 'location', 'kiosk__name', 'kiosk__teacher__name', 'kiosk__teacher__username']
    readonly_fields = ['attended_at']
    ordering = ['-attended_at']
    
    def get_teacher_name(self, obj):
        """担当講師名を取得"""
        if obj.kiosk and obj.kiosk.teacher:
            return obj.kiosk.teacher.name or obj.kiosk.teacher.username
        return '未指定'
    get_teacher_name.short_description = '担当講師'