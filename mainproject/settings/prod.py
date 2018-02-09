from mainproject.settings.base import *

# insert custom settings here
DEBUG = True

ALLOWED_HOSTS = ['vwb3-web-02.egr.duke.edu', 'materials.hybrid3.duke.edu']

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

try:
    from mainproject.settings.local import *
except:
    pass
