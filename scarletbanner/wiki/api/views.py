from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets

from scarletbanner.wiki.api.serializers import PageSerializer
from scarletbanner.wiki.models import Page


@extend_schema_view(
    list=extend_schema(
        summary="List all page",
        description="This endpoint returns a list of all wiki pages.",
        auth=[],
    ),
)
class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all()
    serializer_class = PageSerializer
