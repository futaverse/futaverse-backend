import os

# Celery app — reserved for future use. django-q is the active task queue.
# Registered automatically by futaverse/__init__.py on Django startup.
# No tasks are currently registered.

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'futaverse.settings')

app = Celery('futaverse')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')