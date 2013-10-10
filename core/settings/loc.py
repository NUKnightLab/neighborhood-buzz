"""Local settings and globals

Intended to be a shared local settings file that is to be used for development
environments. If you have user-specific settings, please put them in a 
<username>.py file that imports the local settings.
"""
import sys
import os
from .base import *

# Import secrets
sys.path.append(
    os.path.normpath(os.path.join(PROJECT_ROOT, '../secrets/buzz/stg'))
)
from secrets import *

WSGI_APPLICATION = 'conf.loc.wsgi.application'

DEBUG = True
TEMPLATE_DEBUG = DEBUG
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'buzz',
        'USER': 'buzzer',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '',
    }
}

#
# Bucket for tweet archives (archivetweets management command)
#

AWS_ARCHIVE_BUCKET_NAME = 'archive.knilab.com'

#
# django-debug-toolbar
#
INTERNAL_IPS = ('127.0.0.1', 'localhost')

#MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)

#INSTALLED_APPS += ('debug_toolbar',)
