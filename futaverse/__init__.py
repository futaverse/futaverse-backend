# Celery app auto-discovery — reserved for future use.
# django-q (python manage.py qcluster) is the active task queue.
from .celery import app as celery_app

__all__ = ('celery_app',)