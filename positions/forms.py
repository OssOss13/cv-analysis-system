from django import forms
from .models import Position

class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = [
            'title', 'description', 'skills_needed', 'seniority', 
            'location', 'salary_range', 'employment_type', 
            'is_remote', 'closing_date', 'responsibilities', 'benefits'
        ]
        widgets = {
            'closing_date': forms.DateInput(attrs={'type': 'date'}),
            'skills_needed': forms.Textarea(attrs={'rows': 3}),
            'responsibilities': forms.Textarea(attrs={'rows': 5}),
            'benefits': forms.Textarea(attrs={'rows': 5}),
        }
