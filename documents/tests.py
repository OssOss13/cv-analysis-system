from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import CV
import os
from .forms import CVUploadForm

class CVModelTest(TestCase):
    def test_create_cv(self):
        """Test if a CV can be created"""
        cv = CV.objects.create(file="sample.pdf")
        self.assertEqual(str(cv.file), "sample.pdf")

class CVViewsTest(TestCase):
    def setUp(self):
        """Setup a sample CV"""
        self.cv = CV.objects.create(file="sample.pdf")

    def test_cv_list_view(self):
        """Test if the CV list page loads successfully"""
        response = self.client.get(reverse("list_cvs"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "documents/list_cvs.html")

    def test_delete_cv_view(self):
        """Test deleting a CV"""
        response = self.client.post(reverse("delete_cv", args=[self.cv.id]))
        self.assertEqual(response.status_code, 302)  # Redirect expected after delete
        self.assertFalse(CV.objects.filter(id=self.cv.id).exists())

    def test_view_cv_detail(self):
        """Test viewing a CV detail page"""
        response = self.client.get(reverse("view_cv", args=[self.cv.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "documents/cv_details.html")

class CVUploadFormTest(TestCase):
    def test_valid_form(self):
        """Test CV upload form with valid data"""
        file_data = SimpleUploadedFile("test_cv.pdf", b"dummy content", content_type="application/pdf")
        form = CVUploadForm(files={"file": file_data})
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        """Test CV upload form with missing file"""
        form = CVUploadForm(files={})
        self.assertFalse(form.is_valid())


        