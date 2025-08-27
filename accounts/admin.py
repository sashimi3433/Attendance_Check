from django.contrib import admin
from .models import CustomUser, InvitationCode, Kiosk

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'name', 'birth_date', 'admission_year', 'department', 'invitation_code', 'date_joined')
    list_filter = ('department', 'type', 'invitation_code', 'admission_year')
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

@admin.register(Kiosk)
class KioskAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'user', 'teacher', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'teacher')
    search_fields = ('name', 'location', 'user__username', 'teacher__name')
    readonly_fields = ('created_at', 'updated_at')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = CustomUser.objects.filter(type='kiosk')
        elif db_field.name == "teacher":
            kwargs["queryset"] = CustomUser.objects.filter(type='teacher')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)