from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse
from .models import CV
from rag.vectorstore import delete_cv_from_vectorstore
import logging
from django.contrib.auth.decorators import user_passes_test

logger = logging.getLogger(__name__)

def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
def view_cv(request, cv_id):
    cv = get_object_or_404(CV, id=cv_id)
    return FileResponse(open(cv.file.path, 'rb'))

@user_passes_test(is_admin)
def delete_cv(request, cv_id):
    """View to delete a CV by ID."""
    cv = get_object_or_404(CV, id=cv_id)
    
    # Delete from vectorstore first
    delete_cv_from_vectorstore(cv.id)
    
    # Delete from DB and filesystem
    cv.delete()
    return redirect('position_list')