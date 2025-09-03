from django.contrib import admin
from .models import CustomUser, InvitationCode, Teacher, Lesson

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'name', 'birth_date', 'admission_year', 'department', 'major', 'grade', 'invitation_code', 'date_joined')
    list_filter = ('department', 'major', 'grade', 'invitation_code', 'admission_year')
    search_fields = ('username', 'name')
    readonly_fields = ('date_joined', 'last_login')

@admin.register(InvitationCode)
class InvitationCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'type', 'is_active', 'used_count', 'created_at')
    list_filter = ('type', 'is_active', 'created_at')
    search_fields = ('code', 'name')
    readonly_fields = ('code', 'created_at', 'used_count')

    def save_model(self, request, obj, form, change):
        if not change:  # 新規作成時のみ
            obj.code = InvitationCode.generate_unique_code()
        super().save_model(request, obj, form, change)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject')
    search_fields = ('user__username', 'subject')

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'subject', 'lesson_times', 'location', 'reception', 'created_at')
    list_filter = ('reception', 'created_at')
    search_fields = ('teacher__user__username', 'subject', 'location')
    readonly_fields = ('created_at',)