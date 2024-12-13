"""
Настройки Django для проекта Orgo_Back.

Создано с использованием 'django-admin startproject' версии Django 5.1.1.

Для получения дополнительной информации смотрите:
https://docs.djangoproject.com/en/5.1/topics/settings/

Полный список настроек и их значений доступен по ссылке:
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os
from datetime import timedelta

# Построение путей внутри проекта, например: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Использование WhiteNoise для обслуживания статических файлов
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Безопасность: хранение секретного ключа
SECRET_KEY = 'django-insecure-7gx)4y4h2k1)0&&k(aaoo!ukb5j&%25$iwhz$rjk6jtislfw'

# Безопасность: управление режимом отладки
DEBUG = True  # Установите в False для продакшен-среды

# Разрешенные хосты
ALLOWED_HOSTS = [
    'orgoback-production.up.railway.app',
    # Добавьте другие разрешённые хосты, например:
    # 'example.com',
]

# Настройка статических файлов
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Настройка медиа-файлов
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Определение доверенных источников для CSRF
CSRF_TRUSTED_ORIGINS = [
    'https://orgoback-production.up.railway.app',
    # Замените на домен вашего фронтенда, если применимо
]

# Оптимизированная конфигурация CORS
CORS_ALLOWED_ORIGINS = [
    'https://orgoback-production.up.railway.app',
    # Добавьте другие разрешённые источники, если необходимо
]

# Параметры CORS
CORS_ALLOW_CREDENTIALS = False  # Не позволяйте использовать куки с кросс-доменных запросов

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# Определение установленных приложений
INSTALLED_APPS = [
    # Стандартные приложения Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
     'django_filters',
    # Приложения третьих сторон
    'django_celery_beat',
    'rest_framework',
    'rest_framework.authtoken',
    'drf_yasg',
    'corsheaders',

    # Ваше основное приложение
    'main',
]

# Мидлвары приложения
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # WhiteNoise для обслуживания статических файлов
    'corsheaders.middleware.CorsMiddleware',       # CORS middleware должен быть как можно выше
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',    # Общая мидлварка должна быть ниже CORS
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Корневой URL конфигурации
ROOT_URLCONF = 'Orgo_Back.urls'

# Настройки шаблонов
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # Добавьте пути к вашим шаблонам, если необходимо
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',  # Необходим для DRF browsable API
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI приложение
WSGI_APPLICATION = 'Orgo_Back.wsgi.application'

# Конфигурация базы данных
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'railway',
        'USER': 'postgres',
        'PASSWORD': 'hkWUiJXywuzDtMueArXgGgtLXRJqEcyX',
        'HOST': 'autorack.proxy.rlwy.net',
        'PORT': 28022,  # Убедитесь, что порт указан как целое число
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,  # Установите минимальную длину пароля
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Пользовательская модель пользователя
AUTH_USER_MODEL = 'main.User'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0') # Redis URL
CELERY_ACCEPT_CONTENT = ['json']                # Supported content types
CELERY_TASK_SERIALIZER = 'json'                 # Serializer for tasks
CELERY_TIMEZONE = 'UTC'                         # Set your timezone
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0' 


# Международные настройки
LANGUAGE_CODE = 'ru'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Статические файлы (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'

# По умолчанию используем WhiteNoise для статических файлов
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Настройка REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',  # Используем стандартный класс аутентификации
        # Если у вас есть кастомный класс, замените на него
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',         # По умолчанию только аутентифицированные пользователи
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',      # Для удобства использования API
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,                                         # Размер страницы по умолчанию
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # Не отключать встроенные логгеры Django
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} [{name}] {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file_info': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs/info.log',
            'formatter': 'verbose',
        },
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs/error.log',
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file_info', 'file_error', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'main': {  # Логгер для вашего основного приложения 'main'
            'handlers': ['file_info', 'file_error', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        # Добавьте другие логгеры для других приложений при необходимости
    },
}

# Создайте директорию logs, если её нет
LOG_DIR = BASE_DIR / 'logs'
if not LOG_DIR.exists():
    LOG_DIR.mkdir(parents=True)
# Безопасность в продакшене
if not DEBUG:
    # Используйте HTTPS
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # Защита от XSS
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

    # HSTS настройки
    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Защита от Clickjacking
    X_FRAME_OPTIONS = 'DENY'