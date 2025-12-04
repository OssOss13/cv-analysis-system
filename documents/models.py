from sqlalchemy.sql._elements_constructors import null
from django.db import models
import os
from django.contrib.auth.models import User

class CV(models.Model):
    file = models.FileField(upload_to="cvs/")
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cvs", null=True)
    original_filename = models.CharField(max_length=255, null=True)
    file_size = models.IntegerField(help_text="File size in bytes", null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "CV"
        verbose_name_plural = "CVs"
    
    def __str__(self):
        return f"{self.original_filename} ({self.uploaded_by.username})"
    
    def delete(self, *args, **kwargs):
        # Delete from vectorstore before deleting the model
        from rag.vectorstore import delete_cv_from_vectorstore
        delete_cv_from_vectorstore(self.id)
        
        # Delete the file from filesystem
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)

class CVSummary(models.Model):
    cv = models.OneToOneField(CV, on_delete=models.CASCADE, related_name="summary")
    summary_json = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Cache commonly accessed fields for faster queries
    candidate_name = models.CharField(max_length=255, blank=True, null=True)
    years_experience = models.FloatField(blank=True, null=True)
    
    class Meta:
        verbose_name = "CV Summary"
        verbose_name_plural = "CV Summaries"
    
    def __str__(self):
        return f"Summary for {self.cv.original_filename}"
    
    def save(self, *args, **kwargs):
        # Auto-populate cached fields from JSON
        if self.summary_json:
            self.candidate_name = self.summary_json.get('name')
            self.years_experience = self.summary_json.get('years_experience')
        super().save(*args, **kwargs)