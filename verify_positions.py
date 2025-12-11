import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from positions.models import Position, Application
from documents.models import CV

def verify():
    print("Verifying Position App...")
    
    # 1. Create User
    user, created = User.objects.get_or_create(username='testuser', email='test@example.com')
    if created:
        user.set_password('password')
        user.save()
    print(f"User: {user}")

    # 2. Create Position
    position = Position.objects.create(
        title="Senior Python Developer",
        description="We are looking for a Python expert.",
        skills_needed="Python, Django, Celery",
        seniority="Senior",
        location="Remote",
        employment_type="Full-time",
        is_remote=True
    )
    print(f"Created Position: {position}")

    # 3. Create CV
    cv_content = b"Mock CV Content"
    cv_file = SimpleUploadedFile("test_cv.pdf", cv_content, content_type="application/pdf")
    cv = CV.objects.create(
        file=cv_file,
        uploaded_by=user,
        original_filename="test_cv.pdf"
    )
    print(f"Created CV: {cv}")

    # 4. Create Application
    application = Application.objects.create(
        position=position,
        cv=cv
    )
    print(f"Created Application: {application}")

    # 5. Verify
    assert Application.objects.count() > 0
    assert Position.objects.count() > 0
    assert CV.objects.count() > 0
    
    print("Verification Successful!")

if __name__ == "__main__":
    verify()
