from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import upload_cv, list_cvs, view_cv, delete_cv

urlpatterns = [
    path("", list_cvs, name="list_cvs"),
    path("upload/", upload_cv, name="upload_cv"),
    path("view/<int:cv_id>/", view_cv, name="view_cv"),
    path("delete/<int:cv_id>/", delete_cv, name="delete_cv"),
]
