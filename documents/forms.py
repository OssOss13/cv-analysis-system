from django import forms
from .models import CV

class CVUploadForm(forms.ModelForm):
    class Meta:
        model = CV
        fields = ["file"]