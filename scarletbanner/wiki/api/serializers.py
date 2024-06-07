from rest_framework import serializers

from scarletbanner.wiki.models import Page


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ["id", "title", "slug", "body", "parent", "read", "write"]
