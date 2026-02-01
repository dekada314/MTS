import math
import os
import logging
from time import sleep
from datetime import datetime, timedelta
from celery import shared_task, chain, group
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

def _chunks(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]

@shared_task(bind=True, max_retries=3, retry_backoff=True)
def send_daily_notifications(self):
    """Отправляет ежедневные уведомления подписанным пользователям."""
    try:
        user_ids = list(
            User.objects.filter(
                is_active=True,
                email__isnull=False,
                subscription__is_subscribed=True,
            ).values_list("id", flat=True)
        )
        num_users = len(user_ids)
        if num_users == 0:
            logger.info("Нет пользователей с email")
            return "Нет пользователей для отправки"

        if settings.DEBUG:
            logger.info(f"DEBUG=True: Симуляция отправки {num_users} уведомлений")
            return f"Уведомления симулированы для {num_users} пользователей"

        batches = list(_chunks(user_ids, BATCH_SIZE))
        job = group(send_daily_notifications_batch.s(batch) for batch in batches)
        job.apply_async()
        logger.info(f"Запущена рассылка: {num_users} пользователей, {len(batches)} батчей")
        return f"Рассылка запущена для {num_users} пользователей"

    except Exception as exc:
        logger.error(f"Ошибка в send_daily_notifications: {exc}", exc_info=True)
        self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=3, retry_backoff=True)
def send_daily_notifications_batch(self, user_ids):
    try:
        users = User.objects.filter(id__in=user_ids, email__isnull=False)
        messages = [
            (
                'Ежедневное уведомление от Home',
                "Привет! Сегодня акция на мебель - скидка 20%!",
                DEFAULT_FROM_EMAIL,
                [user.email]
            )
            for user in users
        ]
        if not messages:
            return 0
        sent = send_mass_mail(messages, fail_silently=False)
        return sent
    except Exception as exc:
        logger.error(f"Ошибка в send_daily_notifications_batch: {exc}", exc_info=True)
        raise


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


@shared_task(bind=True, rate_limit='10/m', max_retries=3, retry_backoff=True)
def send_daily_discounts(self):
    print('send_daily_discounts')
    """Отправляет уведомления о скидках на товары."""
    try:
        discounted_product_ids = list(Products.objects.filter(discount__gt=0).values_list("id", flat=True))
        if not discounted_product_ids:
            logger.info("Нет товаров со скидками для рассылки")
            return "Нет товаров со скидками для рассылки"

        user_ids = list(
            User.objects.filter(
                is_active=True,
                email__isnull=False,
                subscription__is_subscribed=True,
            ).values_list("id", flat=True)
        )
        num_users = len(user_ids)
        if num_users == 0:
            logger.info("Нет активных подписанных пользователей для рассылки скидок")
            return "Рассылка скидок завершена для 0 пользователей"

        if settings.DEBUG:
            logger.info(f"DEBUG=True: Симуляция отправки {num_users} писем о скидках")
            return f"Рассылка скидок симулирована для {num_users} пользователей"

        batches = list(_chunks(user_ids, BATCH_SIZE))
        job = group(send_daily_discounts_batch.s(batch, discounted_product_ids) for batch in batches)
        job.apply_async()
        return f"Рассылка скидок запущена для {num_users} пользователей"

    except Exception as exc:
        logger.error(f"Ошибка в send_daily_discounts: {exc}", exc_info=True)
        self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=3, retry_backoff=True)
def send_daily_discounts_batch(self, user_ids, discounted_product_ids):
    try:
        products = Products.objects.filter(id__in=discounted_product_ids)
        users = User.objects.filter(id__in=user_ids, email__isnull=False)
        messages = []
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        for user in users:
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

        if not messages:
            return 0

        connection = get_connection()
        sent = connection.send_messages(messages)
        return sent
    except Exception as exc:
        logger.error(f"Ошибка в send_daily_discounts_batch: {exc}", exc_info=True)
        raise


@shared_task
def send_abandoned_cart_reminder():
    print('send_abandoned_cart_reminder')
    # Calculate the time 5 days ago from now
    five_days_ago = timezone.now() - timedelta(days=5)
    try:
        user_ids = list(
            Cart.objects.filter(
                created_timestamp__lte=five_days_ago,
                user__isnull=False,
            ).values_list("user_id", flat=True).distinct()
        )

        if len(user_ids) == 0:
            logger.info("Нет заброшенных корзин")
            return "Рассылка напоминаний о заброшенных корзин отправлена для 0 пользователей"

        if settings.DEBUG:
            logger.info(f"DEBUG=True: Симуляция напоминаний о корзине для {len(user_ids)} пользователей")
            return f"Рассылка напоминаний симулирована для {len(user_ids)} пользователей"

        job = group(send_abandoned_cart_reminder_to_user.s(user_id) for user_id in user_ids)
        job.apply_async()
        return f"Рассылка напоминаний запущена для {len(user_ids)} пользователей"

    except Exception as exc:
        logger.error(f"Проблемы в функции send_abandoned_cart_reminder")
        return f"Ошибка: корзины не найдены"


@shared_task(bind=True, rate_limit='30/m', max_retries=3, retry_backoff=True)
def send_abandoned_cart_reminder_to_user(self, user_id):
    try:
        user = User.objects.get(id=user_id, email__isnull=False)
        user_carts = Cart.objects.filter(user_id=user_id).select_related('product')
        if not user_carts.exists():
            return 0

        cart_items = [
            {
                'product_name': item.product.name,
                'quantity': item.quantity,
                'image_url': f"{settings.BASE_URL}{item.product.image.url}" if item.product.image else None
            }
            for item in user_carts
        ]

        subject = f"{user.username}, Вы забыли товары в корзине!"
        message = render_to_string('email/abandoned_cart.html', {
            'username': user.username,
            'cart_items': cart_items,
            'base_url': settings.BASE_URL,
        })

        send_mail(
            subject=subject,
            message='',
            html_message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return 1
    except Exception as exc:
        logger.error(f"Ошибка в send_abandoned_cart_reminder_to_user({user_id}): {exc}", exc_info=True)
        raise


@shared_task(bind=True, rate_limit='10/m', max_retries=3, retry_backoff=True)
def send_order_confirmation(self, order_id, user_id):
    """Отправляет письмо с подтверждением заказа пользователю."""
    try:
        user = User.objects.get(id=user_id, email__isnull=False)
        order = Order.objects.get(id=order_id)
        
        if not hasattr(user, 'subscription') or not user.subscription.is_subscribed:
            logger.info(f"Пользователь {user.username} не подписан на уведомления")
            return f"Не отправлено: пользователь {user.id} не подписан"

        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        html_content = render_to_string('email/order_confirmation.html', {
            'user': user,
            'order': order,
            'base_url': base_url,
            'year': timezone.now().year,
        })
        plain_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject=f'Подтверждение заказа #{order.id}',
            body=plain_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")

        if settings.DEBUG:
            logger.info(f"DEBUG=True: Симуляция отправки письма о заказе {order.id} для {user.email}")
            return f"Симуляция отправки письма для заказа {order.id}"

        email.send()
        logger.info(f"Письмо о заказе {order.id} отправлено пользователю {user.email}")
        return f"Письмо отправлено для заказа {order.id}"

    except User.DoesNotExist:
        logger.error(f"Пользователь с ID {user_id} не найден")
        return f"Ошибка: пользователь {user_id} не найден"
    except Order.DoesNotExist:
        logger.error(f"Заказ с ID {order_id} не найден")
        return f"Ошибка: заказ {order_id} не найден"
    except Exception as exc:
        logger.error(f"Ошибка в send_order_confirmation для заказа {order_id}: {exc}", exc_info=True)
        self.retry(exc=exc, countdown=300)