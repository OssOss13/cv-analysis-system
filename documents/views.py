from django.shortcuts import render, redirect, get_object_or_404
from .models import CV
from .forms import CVUploadForm

from .utils import extract_text_from_cv, parse_cv, save_cv_to_db

def upload_cv(request):
    if request.method == "POST":
        form = CVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            cv = form.save()
            extracted_text = extract_text_from_cv(cv.file.path)
            parsed_data = parse_cv(extracted_text)
            
            save_cv_to_db(cv, parsed_data)
            return redirect("view_cv", cv_id=cv.id)
    else:
        form = CVUploadForm()
    return render(request, "documents/upload_cv.html", {"form": form})

def list_cvs(request):
    """View to list all uploaded CVs."""
    cvs = CV.objects.all()
    return render(request, 'documents/list_cvs.html', {'cvs': cvs})

def view_cv(request, cv_id):
    cv = get_object_or_404(CV, id=cv_id)
    return render(request, "documents/cv_details.html", {"cv": cv})

def delete_cv(request, cv_id):
    """View to delete a CV by ID."""
    cv = get_object_or_404(CV, id=cv_id)
    cv.delete()
    return redirect('list_cvs')