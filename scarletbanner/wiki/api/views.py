from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import pagination, viewsets
from rest_framework.response import Response

from scarletbanner.wiki.api.serializers import PageSerializer
from scarletbanner.wiki.models import Page


class WikiPagination(pagination.LimitOffsetPagination):
    default_limit = 50
    max_limit = 100

    def get_paginated_response(self, data):
        return Response(
            {
                "query": self.request.query_params.get("query", ""),
                "offset": self.offset,
                "limit": self.limit,
                "total": self.count,
                "pages": data,
            }
        )


@extend_schema_view(
    list=extend_schema(
        summary="List all pages",
        description="This endpoint returns a list of all wiki pages.",
        auth=[],
    ),
    retrieve=extend_schema(
        summary="Return a page",
        description="This endpoint returns a single wiki page.",
        auth=[],
    ),
)
class PageViewSet(viewsets.ModelViewSet):
    serializer_class = PageSerializer
    pagination_class = WikiPagination
    lookup_field = "slug"

    def get_queryset(self):
        queryset = Page.objects.all().order_by("-id")
        query = self.request.query_params.get("query", None)
        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(slug__icontains=query))
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        slug = kwargs.get("slug")
        instance = self.get_queryset().filter(slug=slug).first()
        if instance is None:
            return Response({"detail": f"No page found with the path '{slug}'"}, status=404)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
