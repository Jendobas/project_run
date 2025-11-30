from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from app_run.models import Run
from app_run.views import company_details, GetUsers, RunViewSet, StartView, AthleteInfoView, AllChallenges, \
    PositionViewSet, CollectibleView, UploadFileView
from django.conf.urls.static import static
from django.conf import settings

router = DefaultRouter()
router.register('api/runs', RunViewSet)
router.register('api/users', GetUsers)
router.register('api/challenges', AllChallenges)
router.register('api/positions', PositionViewSet)
router.register('api/collectible_item', CollectibleView)
router.register('api/upload_file', UploadFileView, basename='upload-file')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/company_details/', company_details),
    path('', include(router.urls)),
    path('api/runs/<run_id>/<condition>/', StartView.as_view()),
    path('api/athlete_info/<user_id>/', AthleteInfoView.as_view()),
]
