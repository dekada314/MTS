from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_add_email_verification'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_student_verified',
            field=models.BooleanField(default=False, verbose_name='Студент подтвержден'),
        ),
        migrations.AddField(
            model_name='user',
            name='student_country',
            field=models.CharField(blank=True, max_length=80, verbose_name='Страна студента'),
        ),
        migrations.AddField(
            model_name='user',
            name='student_email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='Студенческий email'),
        ),
        migrations.AddField(
            model_name='user',
            name='student_id_card',
            field=models.ImageField(blank=True, null=True, upload_to='student_id_cards', verbose_name='Фото студенческого билета'),
        ),
        migrations.AddField(
            model_name='user',
            name='student_university',
            field=models.CharField(blank=True, max_length=160, verbose_name='Университет'),
        ),
    ]
