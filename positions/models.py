from django.db import models
from django.contrib.auth.models import User
from documents.models import CV

class Position(models.Model):
    SENIORITY_CHOICES = [
        ('Junior', 'Junior'),
        ('Mid', 'Mid'),
        ('Senior', 'Senior'),
        ('Lead', 'Lead'),
    ]
    
    EMPLOYMENT_TYPE_CHOICES = [
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
        ('Contract', 'Contract'),
        ('Freelance', 'Freelance'),
        ('Internship', 'Internship'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    skills_needed = models.TextField(help_text="Comma-separated list of skills")
    seniority = models.CharField(max_length=20, choices=SENIORITY_CHOICES)
    location = models.CharField(max_length=100)
    salary_range = models.CharField(max_length=100, blank=True)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES)
    is_remote = models.BooleanField(default=False)
    closing_date = models.DateField(null=True, blank=True)
    responsibilities = models.TextField(blank=True)
    benefits = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
        
    def get_skills(self):
        if not self.skills_needed:
            return []
        return [skill.strip() for skill in self.skills_needed.split(',') if skill.strip()]

class Application(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Reviewed', 'Reviewed'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ]

    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='applications')
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='applications')
    match_score = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    explanation = models.CharField(max_length=255, null=True, blank=True)
    matched_skills = models.JSONField(default=list, blank=True)

    class Meta:
        unique_together = ('position', 'cv')

    def __str__(self):
        return f"Application for {self.position.title} by {self.cv.uploaded_by.username if self.cv.uploaded_by else 'Unknown'}"
