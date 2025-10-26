# 🪑 Puddle - Furniture E-Commerce Platform

> Современная платформа электронной коммерции для мебельного магазина с полнофункциональным REST API

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://djangoproject.com)
[![DRF](https://img.shields.io/badge/DRF-3.15-red.svg)](https://django-rest-framework.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Содержание

- [Возможности](#-возможности)
- [Технологический стек](#-технологический-стек)
- [Быстрый старт](#-быстрый-старт)
- [Установка](#-установка)
- [Конфигурация](#-конфигурация)
- [API Документация](#-api-документация)
- [Структура проекта](#-структура-проекта)
- [Развёртывание](#-развёртывание)
- [Тестирование](#-тестирование)

## ✨ Возможности

### Веб-приложение
- 🛍️ **Каталог товаров** с категориями и фильтрацией
- 🛒 **Корзина покупок** с динамическим обновлением
- 📦 **Система заказов** с отслеживанием статуса
- 👤 **Профили пользователей** с историей заказов
- ✉️ **Email верификация** для безопасности
- 🎯 **Система скидок** с автоматическими акциями
- 📧 **Email рассылки** о новых скидках

### REST API
- 🔐 **Аутентификация** (Session/Token)
- 📱 **RESTful endpoints** для всех операций
- 📊 **Swagger UI** для интерактивной документации
- 🔍 **Поиск и фильтрация** товаров
- 📈 **Статистика заказов** для администраторов
- 🚀 **Оптимизация запросов** с select_related/prefetch_related

### Фоновые задачи
- ⚡ **Celery** для асинхронных операций
- 📧 **Автоматические email уведомления**
- 📊 **Ежедневная рассылка скидок**
- 🔄 **Периодические задачи** с Celery Beat

## 🛠 Технологический стек

### Backend
- **Django 5.2** - Web framework
- **Django REST Framework 3.15** - API framework
- **PostgreSQL** - Production database
- **Redis** - Caching & message broker
- **Celery** - Асинхронные задачи
- **Pillow** - Обработка изображений

### API & Documentation
- **drf-spectacular** - OpenAPI 3.0 schema
- **django-cors-headers** - CORS support
- **django-filter** - Advanced filtering

### Development
- **Docker & Docker Compose** - Containerization
- **Gunicorn** - WSGI server
- **python-decouple** - Environment management

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Docker (опционально)

### С Docker (рекомендуется)

```bash
# Клонировать репозиторий
git clone <repository-url>
cd Django

# Создать .env файл
cp .env.example .env
# Отредактируйте .env с вашими настройками

# Запустить контейнеры
docker-compose up -d

# Выполнить миграции
docker-compose exec web python manage.py migrate

# Создать суперпользователя
docker-compose exec web python manage.py createsuperuser

# Собрать статику
docker-compose exec web python manage.py collectstatic --noinput
Приложение доступно по адресу: http://localhost:8000

Без Docker
bash
# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt

# Настроить базу данных PostgreSQL
createdb puddle_db

# Создать .env файл
cp .env.example .env
# Настроить DATABASE_URL и другие переменные

# Выполнить миграции
cd puddle
python manage.py migrate

# Создать суперпользователя
python manage.py createsuperuser

# Запустить сервер разработки
python manage.py runserver

# В отдельном терминале запустить Celery
celery -A puddle worker -l info

# В третьем терминале запустить Celery Beat
celery -A puddle beat -l info
⚙️ Конфигурация
Переменные окружения (.env)
bash
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
BASE_URL=http://localhost:8000

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/puddle_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Email Verification
EMAIL_VERIFICATION_REQUIRED=True
EMAIL_CONFIRMATION_EXPIRE_DAYS=7

# CORS (для API)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
Настройка email для Gmail
Включите 2FA в вашем Google аккаунте
Создайте App Password
Используйте App Password в EMAIL_HOST_PASSWORD
📚 API Документация
Endpoints Overview
После запуска сервера доступны:

Swagger UI: http://localhost:8000/api/docs/
ReDoc: http://localhost:8000/api/redoc/
OpenAPI Schema: http://localhost:8000/api/schema/
Основные endpoints
Аутентификация
POST   /api/v1/users/                    - Регистрация
GET    /api/v1/users/me/                 - Текущий пользователь
PUT    /api/v1/users/change_password/   - Смена пароля
GET    /api/v1/users/email_status/       - Статус email
Товары и категории
GET    /api/v1/categories/               - Список категорий
GET    /api/v1/products/                 - Список товаров
GET    /api/v1/products/{slug}/          - Детали товара
GET    /api/v1/products/discounted/      - Товары со скидками
GET    /api/v1/products/search/?q=text   - Поиск
Корзина
GET    /api/v1/cart/                     - Просмотр корзины
POST   /api/v1/cart/                     - Добавить товар
PUT    /api/v1/cart/{id}/                - Обновить количество
DELETE /api/v1/cart/{id}/                - Удалить товар
GET    /api/v1/cart/summary/             - Сводка корзины
DELETE /api/v1/cart/clear/               - Очистить корзину
Заказы
GET    /api/v1/orders/                   - Список заказов
POST   /api/v1/orders/                   - Создать заказ
GET    /api/v1/orders/{id}/              - Детали заказа
GET    /api/v1/orders/my_orders/         - Мои заказы
GET    /api/v1/orders/statistics/        - Статистика (admin)
Примеры использования
Регистрация пользователя
bash
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "user@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }'
Получение товаров со скидками
bash
curl http://localhost:8000/api/v1/products/discounted/
Создание заказа
bash
curl -X POST http://localhost:8000/api/v1/orders/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=your-session-id" \
  -d '{
    "phone_number": "+79001234567",
    "requires_delivery": true,
    "delivery_address": "Moscow, Red Square, 1",
    "payment_on_get": true
  }'
📁 Структура проекта
Django/
├── puddle/                     # Главный проект
│   ├── puddle/                 # Настройки проекта
│   │   ├── settings.py         # Конфигурация Django
│   │   ├── urls.py             # Главные URL
│   │   └── celery.py           # Конфигурация Celery
│   ├── users/                  # Приложение пользователей
│   │   ├── models.py           # Модель User
│   │   ├── views.py            # Веб-views
│   │   ├── serializers.py      # API serializers
│   │   └── viewsets.py         # API viewsets
│   ├── goods/                  # Товары и категории
│   │   ├── models.py           # Products, Categories
│   │   ├── serializers.py      # API serializers
│   │   └── viewsets.py         # API viewsets
│   ├── carts/                  # Корзина
│   │   ├── models.py           # Cart model
│   │   ├── serializers.py      # API serializers
│   │   └── viewsets.py         # API viewsets
│   ├── orders/                 # Заказы
│   │   ├── models.py           # Order, OrderItem
│   │   ├── serializers.py      # API serializers
│   │   └── viewsets.py         # API viewsets
│   ├── notifications/          # Email уведомления
│   │   ├── tasks.py            # Celery задачи
│   │   └── templates/email/    # Email шаблоны
│   ├── api_urls.py             # API routing
│   ├── manage.py               # Django CLI
│   └── requirements.txt        # Python зависимости
├── docker-compose.yml          # Docker конфигурация
├── Dockerfile                  # Docker образ
├── .env.example                # Пример переменных окружения
├── .gitignore                  # Git ignore правила
└── README.md                   # Этот файл
🚢 Развёртывание
Production Checklist
 DEBUG = False в production
 Настроить ALLOWED_HOSTS
 Использовать PostgreSQL (не SQLite)
 Настроить Redis для кеширования
 Собрать статику: python manage.py collectstatic
 Использовать Gunicorn/uWSGI
 Настроить HTTPS/SSL
 Настроить Nginx как reverse proxy
 Включить логирование
 Настроить мониторинг (Sentry)
 Регулярные бэкапы БД
 Переменные окружения в секретах
Docker Production
bash
# Собрать production образ
docker-compose -f docker-compose.prod.yml build

# Запустить в production режиме
docker-compose -f docker-compose.prod.yml up -d

# Выполнить миграции
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Собрать статику
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
Heroku Deployment
bash
# Установить Heroku CLI
# Войти в аккаунт
heroku login

# Создать приложение
heroku create puddle-app

# Добавить PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Добавить Redis
heroku addons:create heroku-redis:hobby-dev

# Установить переменные окружения
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS=puddle-app.herokuapp.com

# Деплой
git push heroku main

# Выполнить миграции
heroku run python puddle/manage.py migrate

# Создать суперпользователя
heroku run python puddle/manage.py createsuperuser
🧪 Тестирование
bash
# Запустить все тесты
python manage.py test

# С покрытием кода
coverage run --source='.' manage.py test
coverage report
coverage html  # Создаст htmlcov/index.html

# Запустить конкретное приложение
python manage.py test users
python manage.py test goods

# Запустить с verbose
python manage.py test --verbosity=2
📊 Мониторинг и логирование
Логирование
Логи сохраняются в:

Консоль (development)
Файлы в logs/ (production)
Sentry (production errors)
Celery мониторинг
bash
# Flower - веб-интерфейс для Celery
celery -A puddle flower

# Доступно на http://localhost:5555
🤝 Разработка
Создание нового приложения
bash
python manage.py startapp app_name
Создание миграций
bash
python manage.py makemigrations
python manage.py migrate
Создание суперпользователя
bash
python manage.py createsuperuser
Code Style
Проект следует PEP 8. Используйте:

bash
# Форматирование
black .

# Линтинг
flake8

# Проверка типов
mypy .
📝 License
This project is licensed under the MIT License - see the LICENSE file for details.

👥 Авторы
Your Name - Initial work - YourGithub
🙏 Благодарности
Django team за отличный фреймворк
DRF community за REST framework
Всем контрибьюторам open-source библиотек
📞 Контакты
Email: your.email
example.com
GitHub: [yourusername](cci:4://file://yourusername](https://github.com/yourusername):0:0-0:0)
LinkedIn: Your Name
⭐ Если этот проект был полезен, поставьте звезду!