from pathlib import Path
import futaverse.settings as base_settings
from futaverse.settings import *

BASE_DIR = Path(__file__).resolve().parent

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3',
    }
}

Q_CLUSTER = {
    'sync': True,
}

REST_FRAMEWORK = {
    **base_settings.REST_FRAMEWORK,
    'DEFAULT_PAGINATION_CLASS': None,
}

CACHES = {
    **base_settings.CACHES,
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
