from django.urls import path, include
from .views import upload_cv, list_cvs, view_cv, delete_cv
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", list_cvs, name="list_cvs"),
    path("upload/", upload_cv, name="upload_cv"),
    path("view/<int:cv_id>/", view_cv, name="view_cv"),
    path("delete/<int:cv_id>/", delete_cv, name="delete_cv"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
