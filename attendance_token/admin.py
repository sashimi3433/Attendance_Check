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
    list_display = ['user', 'attended_at', 'location', 'token']
    list_filter = ['attended_at', 'location']
    search_fields = ['user__username', 'location']
    readonly_fields = ['attended_at']
    ordering = ['-attended_at']