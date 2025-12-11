from django.urls import path, include
from .views import view_cv, delete_cv
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("<int:cv_id>/", view_cv, name="view_cv"),
    path("delete/<int:cv_id>/", delete_cv, name="delete_cv"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
