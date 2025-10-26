import math
import os
import logging
from time import sleep
from datetime import datetime, timedelta
from celery import shared_task, chain
from celery.utils.log import get_task_logger
from django.core.mail import send_mail, send_mass_mail, EmailMultiAlternatives, get_connection
from django.template import Template, Context
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from django.core.paginator import Paginator
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from users.models import User
from goods.models import Products
from carts.models import Cart
from orders.models import Order
from notifications.models import Subscription

logger = get_task_logger(__name__)

# Константы
BATCH_SIZE = 100
DELAY_BETWEEN_BATCHES = 2
DEFAULT_FROM_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@gmail.com')
ADMIN_EMAIL = getattr(settings, 'ADMIN_EMAIL', 'gudiniboy@gmail.com')

@shared_task(bind=True, max_retries=3, retry_backoff=True)
def send_daily_notifications(self):
    """Отправляет ежедневные уведомления подписанным пользователям."""
    try:
        users = User.objects.filter(
            is_active=True,
            email__isnull=False,
        ).select_related('subscription')
        num_users = users.count()
        if not num_users:
            logger.info("Нет пользователей с email")
            return "Нет пользователей для отправки"

        messages = [
            (
                'Ежедневное уведомление от Home',
                "Привет! Сегодня акция на мебель - скидка 20%!",
                DEFAULT_FROM_EMAIL,
                [user.email]
            )
            for user in users
        ]

        if settings.DEBUG:
            logger.info(f"DEBUG=True: Симуляция отправки {num_users} уведомлений")
            return f"Уведомления симулированы для {num_users} пользователей"

        sent = send_mass_mail(messages, fail_silently=False)
        logger.info(f"Отправлено {sent} уведомлений")
        return f"Реальные уведомления отправлены {sent} пользователям"

    except Exception as exc:
        logger.error(f"Ошибка в send_daily_notifications: {exc}", exc_info=True)
        self.retry(exc=exc, countdown=300)


TIME_FOR_ABANDONED = 30
@shared_task(bind=True, max_retries=3, retry_backoff=True)
def cleanup_abandoned_carts(self):
    
    """Удаляет корзины, созданные более 30 дней назад."""
    try:
        one_month_ago = timezone.now() - timedelta(days=TIME_FOR_ABANDONED)
        abandoned_carts = Cart.objects.filter(created_timestamp__lt=one_month_ago)
        count = abandoned_carts.count()
        if count == 0:
            logger.info("Нет заброшенных корзин для удаления")
            return "Нет заброшенных корзин"

        abandoned_carts.delete()
        logger.info(f"Удалено {count} заброшенных корзин")
        return f"Удалено {count} заброшенных корзин"

    except Exception as exc:
        logger.error(f"Ошибка в cleanup_abandoned_carts: {exc}", exc_info=True)
        self.retry(exc=exc, countdown=300)

@shared_task(bind=True, max_retries=3, retry_backoff=True)
def generate_daily_report(self):
    print('generate_daily_report')
    """Создаёт и отправляет ежедневный отчёт, сохраняет PDF."""
    try:
        today = timezone.now().date()
        carts_today = Cart.objects.filter(created_timestamp__date=today)
        carts_items_count = sum(cart.quantity for cart in carts_today if hasattr(cart, 'quantity')) or 0
        orders_today = Order.objects.filter(created_timestamp__date=today)
        orders_items_count = orders_today.count()

        report_message = (
            f"Daily report for {today}:\n"
            f"- Things in carts: {carts_items_count}\n"
            f"- Amount of orders: {orders_items_count}"
        )

        if settings.DEBUG:
            logger.info(f"DEBUG=True: Симуляция отправки отчёта: {report_message}")
        else:
            send_mail(
                subject='Ежедневный отчёт по мебели',
                message=report_message,
                from_email=DEFAULT_FROM_EMAIL,
                recipient_list=[ADMIN_EMAIL],
                fail_silently=False,
            )

        report_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(report_dir, exist_ok=True)
        pdf_filename = f'daily_report_{today}.pdf'
        pdf_path = os.path.join(report_dir, pdf_filename)

        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, letter[1] - 100, f"Daily report for {today}")
        c.setFont("Helvetica", 12)
        text = c.beginText(100, letter[1] - 150)
        for line in report_message.split('\n'):
            text.textLine(line)
        c.drawText(text)
        c.save()

        logger.info(f"Отчёт сгенерирован: {pdf_path}")
        return f"Отчёт отправлен и PDF сохранён: {pdf_path}"

    except Exception as exc:
        logger.error(f"Ошибка в generate_daily_report: {exc}", exc_info=True)
        self.retry(exc=exc, countdown=300)

# @shared_task(bind=True, rate_limit='10/m', max_retries=3, retry_backoff=True)
# def send_batch_emails(self, message_template, subject, batch_user_ids, from_email=DEFAULT_FROM_EMAIL):
#     """Отправляет батч email на основе шаблона."""
#     try:
#         users = User.objects.filter(
#             id__in=batch_user_ids,
#             is_active=True,
#             email__isnull=False,
#             subscription__is_subscribed=True
#         ).select_related('subscription')
#         num_users = users.count()
#         if not num_users:
#             logger.info("Нет пользователей для отправки в батче")
#             return "Батч отправлен: 0 пользователей"

#         messages = []
#         for user in users:
#             context = Context({'user': user, 'message': message_template})
#             rendered_message = Template(message_template).render(context)
#             messages.append((subject, rendered_message, from_email, [user.email]))

#         if settings.DEBUG:
#             logger.info(f"DEBUG=True: Симуляция отправки {num_users} email")
#             for msg in messages:
#                 logger.info(f"  - {msg[0]} to {msg[3][0]}: {msg[1][:50]}...")
#             return f"Батч симулирован: {num_users} пользователей"

#         sent = send_mass_mail(messages, fail_silently=False)
#         logger.info(f"Отправлено {sent} email в батче")
#         return f"Батч отправлен: {sent} пользователей"

#     except Exception as exc:
#         logger.error(f"Ошибка в send_batch_emails: {exc}", exc_info=True)
#         self.retry(exc=exc, countdown=300)

# @shared_task
# def send_mass_notifications(message, subject, user_ids=None, batch_size=BATCH_SIZE, delay=DELAY_BETWEEN_BATCHES, dry_run=False):
#     """Запускает массовую рассылку уведомлений с разбивкой на батчи."""
#     print('send_mass_notifications')
#     try:
#         if user_ids is None:
#             user_ids = list(
#                 User.objects.filter(
#                     is_active=True,
#                     email__isnull=False,
#                     subscription__is_subscribed=True
#                 ).values_list('id', flat=True)
#             )

#         num_users = len(user_ids)
#         if num_users == 0:
#             logger.info("Нет пользователей для массовой рассылки")
#             return "Нет пользователей для отправки"

#         if dry_run or settings.DEBUG:
#             logger.info(f"Dry-run/DEBUG: Симуляция отправки {num_users} сообщений")
#             return f"Dry-run/DEBUG завершён: {num_users} симулировано"

#         if num_users <= batch_size:
#             send_batch_emails.delay(message, subject, user_ids)
#         else:
#             num_batches = math.ceil(num_users / batch_size)
#             tasks = []
#             for i in range(num_batches):
#                 batch_ids = user_ids[i * batch_size: (i + 1) * batch_size]
#                 tasks.append(send_batch_emails.s(message, subject, batch_ids))
#                 if i < num_batches - 1:
#                     tasks.append(shared_task(lambda x=i: sleep(delay)))
#             chain(*tasks).delay()

#         logger.info(f"Рассылка запущена для {num_users} пользователей")
#         return f"Рассылка {'симулирована' if settings.DEBUG else 'запущена'} для {num_users} пользователей"

#     except Exception as exc:
#         logger.error(f"Ошибка в send_mass_notifications: {exc}", exc_info=True)
#         raise

@shared_task(bind=True, rate_limit='10/m', max_retries=3, retry_backoff=True)
def send_daily_discounts(self):
    print('send_daily_discounts')
    """Отправляет уведомления о скидках на товары."""
    try:
        products = Products.objects.filter(discount__gt=0)
        if not products.exists():
            logger.info("Нет товаров со скидками для рассылки")
            return "Нет товаров со скидками для рассылки"

        users = User.objects.filter(
            # is_active=True,
            email__isnull=False,
            # subscription__is_subscribed=True
        ).select_related('subscription')
        num_users = users.count()
        if num_users == 0:
            logger.info("Нет активных подписанных пользователей для рассылки скидок")
            return "Рассылка скидок завершена для 0 пользователей"

        paginator = Paginator(users, BATCH_SIZE)
        for page_num in paginator.page_range:
            page_users = paginator.page(page_num).object_list
            messages = []
            for user in page_users:
                base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
                html_content = render_to_string('email/daily_discounts.html', {
                    'user': user,
                    'products': products,
                    'base_url': base_url,
                    'year': datetime.now().year,
                })
                plain_content = strip_tags(html_content)
                msg = EmailMultiAlternatives(
                    subject='Ежедневные скидки на мебель',
                    body=plain_content,
                    from_email=DEFAULT_FROM_EMAIL,
                    to=[user.email]
                )
                msg.attach_alternative(html_content, "text/html")
                messages.append(msg)

            if messages:
                if settings.DEBUG:
                    logger.info(f"DEBUG=True: Симуляция отправки {len(messages)} писем")
                    for msg in messages:
                        logger.info(f"  - {msg.subject} to {msg.to[0]}")
                else:
                    connection = get_connection()
                    sent = connection.send_messages(messages)
                    logger.info(f"Отправлено {len(messages)} писем о скидках")

        return f"Рассылка скидок {'симулирована' if settings.DEBUG else 'завершена'} для {num_users} пользователей"

    except Exception as exc:
        logger.error(f"Ошибка в send_daily_discounts: {exc}", exc_info=True)
        self.retry(exc=exc, countdown=300)



# notifications/tasks.py
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from users.models import User
from orders.models import Order
import logging
from django.contrib.auth import get_user_model

logger = logging.getLogger('notifications.tasks')








User = get_user_model()

@shared_task
def send_abandoned_cart_reminder():
    print('send_abandoned_cart_reminder')
    # Calculate the time 5 days ago from now
    five_days_ago = timezone.now() - timedelta(days=5)
    
    # Find carts that haven't been updated in 5 days
    abandoned_carts = Cart.objects.filter(
        created_timestamp__lte=five_days_ago,
        user__isnull=False  # Only carts associated with users
    ).select_related('user', 'product').distinct('user')

    for cart in abandoned_carts:
        user = cart.user
        # Get all carts for this user
        user_carts = Cart.objects.filter(user=user).select_related('product')
        
        # Prepare email context
        cart_items = [
            {
                'product_name': item.product.name,
                'quantity': item.quantity,
                'image_url': f"{settings.BASE_URL}{item.product.image.url}" if item.product.image else None
            }
            for item in user_carts
        ]
        
        # Render email template
        subject = f"{user.username}, Вы забыли товары в корзине!"
        message = render_to_string('email/abandoned_cart.html', {
            'username': user.username,
            'cart_items': cart_items,
            'base_url': settings.BASE_URL,
        })
        
        # Send email
        send_mail(
            subject=subject,
            message='',
            html_message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )


# @shared_task(bind=True, rate_limit='10/m', max_retries=3, retry_backoff=True)
# def send_order_confirmation(self, order_id, user_id):
#     """Отправляет письмо с подтверждением заказа пользователю."""
#     try:
#         user = User.objects.get(id=user_id, email__isnull=False)
#         order = Order.objects.get(id=order_id)
        
#         if not hasattr(user, 'subscription') or not user.subscription.is_subscribed:
#             logger.info(f"Пользователь {user.username} не подписан на уведомления")
#             return f"Не отправлено: пользователь {user.id} не подписан"

#         base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
#         html_content = render_to_string('email/order_confirmation.html', {
#             'user': user,
#             'order': order,
#             'base_url': base_url,
#             'year': timezone.now().year,
#         })
#         plain_content = strip_tags(html_content)
        
#         email = EmailMultiAlternatives(
#             subject=f'Подтверждение заказа #{order.id}',
#             body=plain_content,
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             to=[user.email]
#         )
#         email.attach_alternative(html_content, "text/html")

#         if settings.DEBUG:
#             logger.info(f"DEBUG=True: Симуляция отправки письма о заказе {order.id} для {user.email}")
#             return f"Симуляция отправки письма для заказа {order.id}"

#         email.send()
#         logger.info(f"Письмо о заказе {order.id} отправлено пользователю {user.email}")
#         return f"Письмо отправлено для заказа {order.id}"

#     except User.DoesNotExist:
#         logger.error(f"Пользователь с ID {user_id} не найден")
#         return f"Ошибка: пользователь {user_id} не найден"
#     except Order.DoesNotExist:
#         logger.error(f"Заказ с ID {order_id} не найден")
#         return f"Ошибка: заказ {order_id} не найден"
#     except Exception as exc:
#         logger.error(f"Ошибка в send_order_confirmation для заказа {order_id}: {exc}", exc_info=True)
#         self.retry(exc=exc, countdown=300)