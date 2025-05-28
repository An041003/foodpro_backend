from django.db import models
from django.contrib.auth.models import User
from math import log10

GENDER_CHOICES = (
    ('male', 'Nam'),
    ('female', 'Nữ'),
)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100, blank=True, help_text="Họ tên")
    birthdate = models.DateField(null=True, blank=True, help_text="Ngày sinh")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='male')
    height = models.FloatField(help_text="Chiều cao (cm)")
    weight = models.FloatField(help_text="Cân nặng (kg)")
    waist = models.FloatField(help_text="Vòng eo (cm)")
    neck = models.FloatField(help_text="Vòng cổ (cm)")
    hip = models.FloatField(null=True, blank=True, help_text="Vòng mông (cm, chỉ dùng cho nữ)")
    body_fat = models.FloatField(help_text="Phần trăm mỡ cơ thể", null=True, blank=True)
    bmi = models.FloatField(help_text="Chỉ số BMI", null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        try:
            # Tính Body Fat
            if self.gender == 'male' and self.waist and self.neck and self.height:
                self.body_fat = round(
                    495 / (1.0324 - 0.19077 * log10(self.waist - self.neck) + 0.15456 * log10(self.height)) - 450,
                    2
                )
            elif self.gender == 'female' and self.waist and self.hip and self.neck and self.height:
                self.body_fat = round(
                    495 / (1.29579 - 0.35004 * log10(self.waist + self.hip - self.neck) + 0.22100 * log10(self.height)) - 450,
                    2
                )

            # Tính BMI
            if self.height and self.weight:
                height_m = self.height / 100  # cm → m
                self.bmi = round(self.weight / (height_m ** 2), 2)
        except Exception as e:
            pass

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Hồ sơ: {self.user.username}"
    
class ExerciseLibrary(models.Model):
    name = models.CharField(max_length=255)
    muscle_group = models.CharField(max_length=100)
    video_id = models.CharField(max_length=50)
    mode = models.CharField(max_length=10, choices=[
        ("low", "Giảm mỡ"), ("medium", "Duy trì"), ("high", "Tăng cơ")
    ])
    gender = models.CharField(max_length=10, choices=[
        ("male", "Nam"), ("female", "Nữ"), ("any", "Mọi giới")
    ], default="any")

    def __str__(self):
        return self.name


class WorkoutPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    name = models.CharField(max_length=255)
    mode = models.CharField(max_length=10)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.date} ({self.mode})"


class Exercise(models.Model):
    workout = models.ForeignKey(WorkoutPlan, related_name="exercises", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    muscle_group = models.CharField(max_length=100)
    video_id = models.CharField(max_length=50)
    sets = models.PositiveIntegerField()
    reps = models.CharField(max_length=50)
    rest = models.PositiveIntegerField(help_text="Thời gian nghỉ giữa các set (giây)")

    def __str__(self):
        return self.name
