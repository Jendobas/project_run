from django.contrib import admin
from django.urls import path
from app_run.views import company_details
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/company_details/', company_details)
]