from mainproject.settings.base import *

# insert custom settings here
DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# EMAIL_HOST = 'localhost'
# EMAIL_PORT = 1025

try:
    from mainproject.settings.local import *
except:
    pass
