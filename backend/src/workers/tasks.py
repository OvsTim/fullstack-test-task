from src.services.processing import process_uploaded_file as run_process_uploaded_file
from src.workers.celery_app import celery_app


@celery_app.task
def process_uploaded_file(file_id: str) -> None:
    run_process_uploaded_file(file_id)
