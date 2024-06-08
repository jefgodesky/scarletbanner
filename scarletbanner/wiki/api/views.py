from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets, pagination
from rest_framework.response import Response

from scarletbanner.wiki.api.serializers import PageSerializer
from scarletbanner.wiki.models import Page


class WikiPagination(pagination.LimitOffsetPagination):
    default_limit = 50
    max_limit = 100

    def get_paginated_response(self, data):
        return Response({
            "query": self.request.query_params.get("query", ""),
            "offset": self.offset,
            "limit": self.limit,
            "total": self.count,
            "pages": data
        })


@extend_schema_view(
    list=extend_schema(
        summary="List all page",
        description="This endpoint returns a list of all wiki pages.",
        auth=[],
    ),
)
class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all().order_by("-id")
    serializer_class = PageSerializer
    pagination_class = WikiPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
