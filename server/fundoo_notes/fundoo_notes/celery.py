import os

from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fundoo_notes.settings')

app = Celery('fundoo_notes')

# Load task modules from all registered Django app configs.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'check-reminders-every-minute': {
        'task': 'notes.tasks.check_reminders',
        'schedule': crontab(),# Every minute
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
