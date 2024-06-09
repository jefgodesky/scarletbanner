from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from scarletbanner.users.api.views import UserViewSet
from scarletbanner.wiki.api.views import PageViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet)
router.register("wiki", PageViewSet)


app_name = "api"
urlpatterns = router.urls
