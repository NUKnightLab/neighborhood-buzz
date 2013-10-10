"""Staging settings and globals."""
import sys
import os
from os import environ
from .base import *

# Import secrets
sys.path.append(
    os.path.normpath(os.path.join(PROJECT_ROOT, '../secrets/buzz/stg'))
)
from secrets import *

STATIC_URL = 'http://media.knilab.com/buzz/'

# should these be in site.py?
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_HOST_PASSWORD = environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_HOST_USER = environ.get('EMAIL_HOST_USER', 'knightlab@northwestern.edu')
EMAIL_PORT = environ.get('EMAIL_PORT', 587)
EMAIL_SUBJECT_PREFIX = '[buzz] '
EMAIL_USE_TLS = True
SERVER_EMAIL = EMAIL_HOST_USER

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'buzz',
        'USER': 'buzzer',
        'PASSWORD': '',
        'HOST': 'stg-pgis1.knilab.com',
        'PORT': '5432',
    }
}

#
# Bucket for tweet archives (archivetweets management command)
#
AWS_ARCHIVE_BUCKET_NAME = 'archive.knilab.com'

