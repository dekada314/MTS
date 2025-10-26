from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_verified',
            field=models.BooleanField(default=False, verbose_name='Email подтвержден'),
        ),
        migrations.AddField(
            model_name='user',
            name='verification_token',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Токен верификации'),
        ),
        migrations.AddField(
            model_name='user',
            name='token_created_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Токен создан'),
        ),
    ]