from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic import TemplateView
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import permissions
from rest_framework.authtoken.views import ObtainAuthToken


@extend_schema(
    summary="Authentication",
    description="If you submit your valid username and email to this "
    "endpoint, you will receive a token which you can use to authenticate "
    "for any other endpoint that requires authentication. This should be "
    "passed to the endpoint as an `Authorization` header with the format "
    "`Token TOKEN` (replacing `TOKEN` with the value of your token).",
    auth=[],
)
class DocumentedObtainAuthToken(ObtainAuthToken):
    pass


@extend_schema(
    summary="API Documentation",
    description="This endpoint returns documentation of the API in the OpenAPI specification.",
    auth=[],
)
class DocumentedAPIView(SpectacularAPIView):
    pass


urlpatterns = [
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path("about/", TemplateView.as_view(template_name="pages/about.html"), name="about"),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("users/", include("scarletbanner.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    # Your stuff: custom urls includes go here
    path("wiki/", include("scarletbanner.wiki.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# API URLS
urlpatterns += [
    # API base url
    path("api/v1/", include("config.api_router")),
    # DRF auth token
    path("api/v1/token/", DocumentedObtainAuthToken.as_view(), name="obtain-auth-token"),
    path("api/v1/schema/", DocumentedAPIView.as_view(permission_classes=(permissions.AllowAny,)), name="api-schema"),
    path(
        "api/v1/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema", permission_classes=(permissions.AllowAny,)),
        name="api-docs",
    ),
]

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
