
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import Profile


User = get_user_model()


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 1
    max_num = 1
    verbose_name = "Профиль"
    verbose_name_plural = "Профиль"


class CustomUserAdmin(UserAdmin):
    inlines = [ProfileInline]


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "avatar")
    search_fields = ("user__username", "user__email")
    list_filter = ("user__is_staff", "user__is_active")
    list_select_related = ("user",)
    raw_id_fields = ("user",)
