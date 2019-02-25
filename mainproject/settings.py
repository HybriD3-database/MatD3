"""Django settings for HybriD3.

"""

import os
import raven
import socket

from django.contrib.messages import constants as messages


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    with open('/etc/hybrid3_database_django.key', 'r') as f:
        SECRET_KEY = f.read()
except Exception:
    pass

DEBUG = False

ALLOWED_HOSTS = ['vwb3-web-02.egr.duke.edu', 'materials.hybrid3.duke.edu']

# Application definition

INSTALLED_APPS = [
    'materials',
    'accounts',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'raven.contrib.django.raven_compat',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mainproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'mainproject/templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mainproject.wsgi.application'

# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'materials',
        'USER': 'xd24',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '',
    }
}

# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.'
        'UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
        'MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
        'CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
        'NumericPasswordValidator',
    },
]

# Internationalization

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/New_York'

USE_I18N = True

USE_L10N = True

USE_TZ = True

FILE_UPLOAD_PERMISSIONS = 0o775

# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'mainproject/static')
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'mainproject/media')

LOGIN_REDIRECT_URL = '/'

LOGIN_URL = '/account/login'

# Account settings

ACCOUNT_ACTIVATION_DAYS = 7

# Email settings

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.office365.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = os.environ.get('HYBRID3_EMAIL_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('HYBRID3_EMAIL_PASSWORD', '')
EMAIL_HOST_USER = 'XXXXXXX'
EMAIL_HOST_PASSWORD = 'XXXXXXX'
DEFAULT_FROM_EMAIL = 'HybriD3 materials database <hybrid3project@duke.edu>'
EMAIL_USE_TLS = True

# Messages framework

MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

# Logging

RAVEN_CONFIG = {
    'dsn': 'https://768890a8001b4782bd27155f351fdea6:817997aed0d1430282276964afbe22bc@sentry.io/1395175',
    'release': raven.fetch_git_sha(BASE_DIR),
}
# Disable Sentry for development
if socket.gethostname() not in ALLOWED_HOSTS:
    RAVEN_CONFIG['dsn'] = ''

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} - {asctime} - {module} - {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'sentry': {
            'level': 'WARNING',
            'class':
            'raven.contrib.django.raven_compat.handlers.SentryHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
        '': {
            'handlers': ['console', 'sentry'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
    },
}
