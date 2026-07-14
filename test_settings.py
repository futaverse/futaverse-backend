from pathlib import Path
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
    'DEFAULT_PAGINATION_CLASS': None,
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
