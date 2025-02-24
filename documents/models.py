from django.db import models
import os

class CV(models.Model):
    file = models.FileField(upload_to="cvs/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name
    
    def delete(self, *args, **kwargs):
        # Delete the file from the filesystem before deleting the model instance
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)

class PersonalInfo(models.Model):
    cv = models.OneToOneField(CV, on_delete=models.CASCADE, related_name='personal_info')
    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    linkedin = models.URLField(null=True, blank=True)
    github = models.URLField(null=True, blank=True)

class WorkExperience(models.Model):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='work_experience')
    job_title = models.CharField(max_length=255, null=True, blank=True)
    company = models.CharField(max_length=50, null=True, blank=True)
    duration = models.CharField(max_length=50, null=True)
    location = models.CharField(max_length=100, null=True, blank=True)


class Education(models.Model):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='education')
    institution = models.CharField(max_length=255, null=True)
    degree = models.CharField(max_length=255, null=True)
    duration = models.CharField(max_length=50, null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)


class Project(models.Model):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True, max_length=255)

class Certification(models.Model):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='certifications')
    name = models.CharField(max_length=255, null=True)
    issuer = models.CharField(max_length=255, null=True, blank=True)
    year = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True, max_length=255)

class Skill(models.Model):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)