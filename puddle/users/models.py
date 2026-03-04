from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    image = models.ImageField(upload_to='users_images', blank=True, null=True, verbose_name='Аватар')
    phone_number = models.CharField(max_length=10, blank=True, null=True)
    is_student_verified = models.BooleanField(default=False, verbose_name='Студент подтвержден')
    student_country = models.CharField(max_length=80, blank=True, verbose_name='Страна студента')
    student_university = models.CharField(max_length=160, blank=True, verbose_name='Университет')
    student_email = models.EmailField(blank=True, verbose_name='Студенческий email')
    student_id_card = models.ImageField(
        upload_to='student_id_cards',
        blank=True,
        null=True,
        verbose_name='Фото студенческого билета',
    )
    
    # Email verification fields
    email_verified = models.BooleanField(default=False, verbose_name='Email подтвержден')
    verification_token = models.CharField(max_length=100, blank=True, null=True, verbose_name='Токен верификации')
    token_created_at = models.DateTimeField(blank=True, null=True, verbose_name='Токен создан')

    class Meta:
        db_table = 'user'
        verbose_name = 'Пользователя'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username

    @property
    def account_type(self):
        if self.is_staff or self.is_superuser:
            return 'admin'
        if self.is_student_verified:
            return 'student'
        return 'user'
    
    def can_place_order(self):
        """Check if user can place orders (email must be verified)"""
        from django.conf import settings
        if not settings.EMAIL_VERIFICATION_REQUIRED:
            return True
        return self.email_verified
    
    def is_token_valid(self):
        """Check if verification token is still valid"""
        if not self.token_created_at:
            return False
        from django.conf import settings
        expiry_days = getattr(settings, 'EMAIL_CONFIRMATION_EXPIRE_DAYS', 7)
        expiry_date = self.token_created_at + timedelta(days=expiry_days)
        return timezone.now() < expiry_date
