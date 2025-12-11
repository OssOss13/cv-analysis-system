from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from .models import Position, Application
from documents.forms import CVUploadForm
from documents.tasks import create_application_task
from rag.ingestion import ingest_cv_and_create_summary_by_id
import logging
from documents.models import CV
from positions.utils import compute_file_hash

logger = logging.getLogger(__name__)

from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm

def is_admin(user):
    return user.is_authenticated and user.is_staff

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            return redirect("position_list")
        messages.error(request, "Unsuccessful registration. Invalid information.")
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {"form": form})

from django.db.models import Q

def position_list(request):
    positions = Position.objects.all().order_by('-created_at')
    
    # Filter by search query
    query = request.GET.get('q')
    if query:
        positions = positions.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(skills_needed__icontains=query)
        )
        
    # Filter by seniority
    seniority = request.GET.get('seniority')
    if seniority:
        positions = positions.filter(seniority=seniority)
        
    # Filter by location
    location = request.GET.get('location')
    if location:
        positions = positions.filter(location__icontains=location)
        
    return render(request, 'positions/position_list.html', {
        'positions': positions,
        'seniority_choices': Position.SENIORITY_CHOICES
    })

def position_detail(request, pk):
    position = get_object_or_404(Position, pk=pk)
    applications = None
    if request.user.is_staff:
        applications = position.applications.select_related('cv', 'cv__uploaded_by').all()
        
    return render(request, 'positions/position_detail.html', {
        'position': position,
        'applications': applications
    })

from .forms import PositionForm

@user_passes_test(is_admin)
def position_create(request):
    if request.method == 'POST':
        form = PositionForm(request.POST)
        if form.is_valid():
            try:
                position = form.save()
                messages.success(request, 'Position created successfully.')
                return redirect('position_detail', pk=position.pk)
            except Exception as e:
                messages.error(request, f'Error creating position: {e}')
    else:
        form = PositionForm()
    
    return render(request, 'positions/position_form.html', {
        'form': form,
        'action': 'Create'
    })

@user_passes_test(is_admin)
def position_update(request, pk):
    position = get_object_or_404(Position, pk=pk)
    if request.method == 'POST':
        form = PositionForm(request.POST, instance=position)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Position updated successfully.')
                return redirect('position_detail', pk=position.pk)
            except Exception as e:
                messages.error(request, f'Error updating position: {e}')
    else:
        form = PositionForm(instance=position)

    return render(request, 'positions/position_form.html', {
        'form': form,
        'action': 'Update'
    })

@user_passes_test(is_admin)
def position_delete(request, pk):
    position = get_object_or_404(Position, pk=pk)
    if request.method == 'POST':
        position.delete()
        messages.success(request, 'Position deleted successfully.')
        return redirect('position_list')
    return render(request, 'positions/position_confirm_delete.html', {'position': position})

@login_required
def apply_for_position(request, pk):
    position = get_object_or_404(Position, pk=pk)
    
    # Check if already applied
    if Application.objects.filter(position=position, cv__uploaded_by=request.user).exists():
        messages.warning(request, 'You have already applied for this position.')
        return redirect('position_detail', pk=pk)

    if request.method == 'POST':
        form = CVUploadForm(request.POST, request.FILES)

        if not form.is_valid():
            # Form invalid → show errors
            return render(request, 'positions/apply.html', {
                'position': position,
                'form': form
            })

        uploaded_file = request.FILES['file']
        file_hash = compute_file_hash(uploaded_file)

        # Check duplicate CV to skip creating CVSummary if cv already exists
        existing_cv = CV.objects.filter(file_hash=file_hash).first()
        if existing_cv:
            cv = existing_cv
        # if new cv create new CV and CVSummary
        else:
            cv = form.save(commit=False)
            cv.uploaded_by = request.user
            cv.file_hash = file_hash
            cv.save()

            # save CV and create CVSummary entry
            ingest_cv_and_create_summary_by_id(cv.id) 
        
        # Trigger Async Processing
        create_application_task.delay(cv.id, position.id)
        logger.info(f"Queued CV {cv.id} for processing (Application to {position.title})")
        
        messages.success(request, 'Application submitted successfully!')
        return redirect('position_detail', pk=pk)
    else:
        form = CVUploadForm()
    
    return render(request, 'positions/apply.html', {'position': position, 'form': form})
