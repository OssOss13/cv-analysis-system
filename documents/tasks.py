from celery import shared_task
from rag.ingestion import ingest_cv_by_id
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_cv_task(cv_id: int):
    logger.info(f"Task: Starting processing for CV {cv_id}")
    try:
        result = ingest_cv_by_id(cv_id)
        logger.info(f"Task: Finished processing for CV {cv_id}")
        return result
    except Exception as e:
        logger.error(f"Task: Error processing CV {cv_id}: {e}")
        raise
