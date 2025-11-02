# myproject/celery.py

import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app.settings')

app = Celery('django_app')

app.config_from_object('django.conf:settings',
                       namespace='CELERY')

app.autodiscover_tasks()

@app.task(bind = True , ignore_result = True)
def debug_taks(self):
    print(f'Request : {self.request!r}')