from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse
from .models import CV
from .forms import CVUploadForm
from rag.ingestion import ingest_cv_by_id
from rag.vectorstore import delete_cv_from_vectorstore
import logging

logger = logging.getLogger(__name__)

def upload_cv(request):
    if request.method == "POST":
        form = CVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            cv = form.save()
            
            # Process CV for RAG (Async)
            from documents.tasks import process_cv_task
            process_cv_task.delay(cv.id)
            logger.info(f"Queued CV {cv.id} for background processing")

            return redirect("view_cv", cv_id=cv.id)
    else:
        form = CVUploadForm()
    return render(request, "documents/upload_cv.html", {"form": form})

def list_cvs(request):
    """View to list all uploaded CVs."""
    cvs = CV.objects.all().order_by('-uploaded_at')
    return render(request, 'documents/list_cvs.html', {'cvs': cvs})

def view_cv(request, cv_id):
    cv = get_object_or_404(CV, id=cv_id)
    return FileResponse(open(cv.file.path, 'rb'))

def delete_cv(request, cv_id):
    """View to delete a CV by ID."""
    cv = get_object_or_404(CV, id=cv_id)
    
    # Delete from vectorstore first
    delete_cv_from_vectorstore(cv.id)
    
    # Delete from DB and filesystem
    cv.delete()
    return redirect('list_cvs')