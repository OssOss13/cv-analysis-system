# your_app/tasks.py
from celery import shared_task
from rag.ingestion import ingest_cv_by_id

@shared_task
def process_cv_task(cv_id: int):
    return ingest_cv_by_id(cv_id)
