import os

from celery import Celery, shared_task
from celery.schedules import crontab

from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'culturizeweb.settings')

app = Celery('culturizeweb')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

schedule = {
    'export-records': {
        'task': 'api.tasks.export_records',
        'schedule': crontab(minute=0, hour=2),
    },
    'export-logs': {
        'task': 'api.tasks.export_logs',
        'schedule': crontab(minute=0, hour=3),
    },
    'clean-up': {
        'task': 'api.tasks.cleanup',
        'schedule': crontab(minute=0, hour=4),
    },
    'check-url-availability': {
        'task': 'api.tasks.check_url_availability',
        'schedule': crontab.from_string(settings.URL_MONITORING_FREQUENCY),
    },
}

if settings.URL_MONITORING_ENABLED.lower() != "enabled":
    del schedule["check-url-availability"]

app.conf.beat_schedule = schedule


@shared_task()
def debug_task(self):
    print(f'Request: {self.request!r}')
