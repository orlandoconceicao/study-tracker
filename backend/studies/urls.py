from rest_framework.routers import DefaultRouter
from .views import StudyViewSet
router = DefaultRouter(); router.register("", StudyViewSet, basename="study")
urlpatterns = router.urls
