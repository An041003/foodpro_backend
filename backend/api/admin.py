from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'full_name', 'birthdate', 'gender', 'height', 'weight', 'waist', 'neck', 'hip', 'bmi', 'body_fat', 'updated_at'
    ]
