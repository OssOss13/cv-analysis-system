import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from core import celery_app
from documents.tasks import process_cv_task

def verify_setup():
    print("Verifying Celery Setup...")
    
    # Check if Celery app is loaded
    print(f"Celery App: {celery_app}")
    print(f"Broker URL: {settings.CELERY_BROKER_URL}")
    
    # Check if task is registered
    print(f"Task Name: {process_cv_task.name}")
    if 'documents.tasks.process_cv_task' in process_cv_task.name:
        print("Task 'process_cv_task' is correctly defined in documents app.")
    else:
        print("Task name mismatch.")

    # Check if task has delay method (Celery task wrapper)
    if hasattr(process_cv_task, 'delay'):
        print("Task has 'delay' method (Celery wrapper active).")
    else:
        print("Task is missing 'delay' method.")

if __name__ == "__main__":
    verify_setup()
