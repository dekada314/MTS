# Puddle — интернет-магазин мебели на Django

Проект интернет-магазина с каталогом товаров, корзиной, оформлением заказов, аутентификацией пользователей и системой email-уведомлений/рассылок на Celery. Поддерживается локальный запуск и Docker-окружение (PostgreSQL + Redis + Gunicorn + Celery worker/beat).

## Содержание
- [Возможности](#возможности)
- [Технологии](#технологии)
- [Архитектура](#архитектура)
- [Структура репозитория](#структура-репозитория)
- [Подготовка окружения](#подготовка-окружения)
- [Запуск локально](#запуск-локально)
- [Запуск в Docker](#запуск-в-docker)
- [Переменные окружения](#переменные-окружения)
- [Статика и медиа](#статика-и-медиа)
- [Фоновые задачи](#фоновые-задачи)
- [Тестирование](#тестирование)
- [Полезные команды](#полезные-команды)

## Возможности
- Каталог товаров с категориями, карточкой товара и скидками.
- Корзина для авторизованных и анонимных пользователей.
- Оформление заказов с адресом, доставкой и статусами.
- Аутентификация, профиль пользователя, аватар.
- Email-уведомления и рассылки, планируемые задачи (Celery Beat).
- Генерация PDF-отчетов о состоянии магазина (ReportLab).

## Технологии
- Backend: Django 5.2.x (admin, auth, sessions, messages, staticfiles, contrib.postgres)
- БД: PostgreSQL 16
- Очереди/планировщик: Celery 5.5 + Redis 7, django-celery-beat
- Сервер: Gunicorn
- Контейнеризация: Docker, docker-compose
- Email: Gmail SMTP
- Тестирование: pytest, pytest-django, pytest-cov
- Прочее: python-decouple/os.environ, reportlab, dj-database-url (в требованиях)

## Архитектура
- Проект: `puddle`
- Приложения:
  - `main` — главные страницы
  - `goods` — каталог, категории, товары
  - `carts` — корзина и операции с ней
  - `orders` — оформление заказов
  - `users` — аутентификация и профиль
  - `notifications` — фоновые задачи, рассылки, отчеты
- Инфраструктура:
  - Dockerfile, docker-compose.yml (web, db, redis, celery worker, celery beat)
  - Логи Celery: `puddle/logs/celery.log`

## Структура репозитория
```
Django/
└─ puddle/
   ├─ manage.py
   ├─ requirements.txt
   ├─ docker-compose.yml
   ├─ Dockerfile
   ├─ .env (локальные переменные окружения)
   ├─ templates/
   ├─ static/    # исходники статики
   ├─ staticfiles/ # collectstatic output
   ├─ media/
   ├─ logs/
   ├─ puddle/    # ядро проекта
   │  ├─ settings.py
   │  ├─ urls.py
   │  ├─ wsgi.py
   │  ├─ asgi.py
   │  └─ celery_app.py
   ├─ main/
   ├─ goods/
   ├─ carts/
   ├─ orders/
   ├─ users/
   └─ notifications/
```

## Подготовка окружения
Требования:
- Python 3.11+
- PostgreSQL 16
- Redis 7

Установка зависимостей:
```bash
pip install -r puddle/requirements.txt
```

## Запуск локально
1) Настройте переменные окружения (см. раздел ниже). Можно использовать `puddle/.env` или экспортировать в OS.
2) Примените миграции:
```bash
python puddle/manage.py migrate
```
3) Создайте суперпользователя:
```bash
python puddle/manage.py createsuperuser
```
4) Запустите сервер разработки:
```bash
python puddle/manage.py runserver
```
5) Запустите Celery worker и beat в отдельных терминалах:
```bash
celery -A puddle.puddle.celery_app:app worker -l info
celery -A puddle.puddle.celery_app:app beat -l info \
  --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

## Запуск в Docker
1) Перейдите в директорию `puddle` и создайте `.env` с переменными (см. список ниже).
2) Поднимите сервисы:
```bash
cd puddle
docker-compose up --build
```
Сервисы:
- `web` — Django + Gunicorn (порт 8000)
- `db` — Postgres 16
- `redis` — Redis 7 (порт 6379)
- `celery_worker` — воркер задач
- `celery_beat` — планировщик (DatabaseScheduler)

## Переменные окружения
Обязательные:
- `SECRET_KEY`
- `DEBUG` (0/1)
- `ALLOWED_HOSTS` (через запятую, напр. `localhost,127.0.0.1`)
- `SQL_ENGINE` (по умолчанию `django.db.backends.postgresql`)
- `SQL_DATABASE`, `SQL_USER`, `SQL_PASSWORD`, `SQL_HOST`, `SQL_PORT`
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` (локально: `redis://127.0.0.1:6379/0`, в Docker: `redis://redis:6379/0`)
- `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` (Gmail SMTP)
Опциональные:
- `BASE_URL` (по умолчанию `http://localhost:8000`)

## Статика и медиа
- Статика: `STATIC_URL = 'static/'`, исходники в `static/`, сборка в `staticfiles/`.
- Команда сборки статики (обычно для prod):
```bash
python puddle/manage.py collectstatic
```
- Медиа загружаются в `media/`.

## Фоновые задачи
Определены в `puddle/notifications/tasks.py`, расписание в `puddle/puddle/settings.py` (`CELERY_BEAT_SCHEDULE`). Основные задачи:
- `send_daily_notifications` — ежедневные уведомления пользователям.
- `cleanup_abandoned_carts` — удаление заброшенных корзин старше N дней.
- `generate_daily_report` — ежедневный отчёт, отправка email админу, сохранение PDF в `media/reports/*.pdf`.
- `send_daily_discounts` — рассылка скидок по товарам со скидками.
- `send_abandoned_cart_reminder` — напоминания о забытых корзинах.
В режиме `DEBUG=True` многие задачи работают в «симуляции» отправки.

## Тестирование
Запуск тестов:
```bash
pytest
```
С покрытием:
```bash
pytest --cov
```

## Полезные команды
```bash
# миграции
python puddle/manage.py makemigrations
python puddle/manage.py migrate

# создание суперпользователя
python puddle/manage.py createsuperuser

# сбор статики
python puddle/manage.py collectstatic

# запуск celery локально
celery -A puddle.puddle.celery_app:app worker -l info
celery -A puddle.puddle.celery_app:app beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

## Безопасность и прод-настройки
- `DEBUG=False` в проде, корректные `ALLOWED_HOSTS`.
- Секреты хранить в переменных окружения/секрет-менеджере.
- Пробросить volumes для `media/`, `staticfiles/`, `logs/`.
- Рассмотреть Redis-кеш в проде (сейчас FileBasedCache).

---
Автор: вы. Лицензирование и контактная информация — по необходимости.
