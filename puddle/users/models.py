from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    image = models.ImageField(upload_to='users_images', blank=True, null=True, verbose_name='Аватар')
    phone_number = models.CharField(max_length=10, blank=True, null=True)
    
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