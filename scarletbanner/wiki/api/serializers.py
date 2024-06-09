from rest_framework import serializers

from scarletbanner.wiki.enums import PermissionLevel
from scarletbanner.wiki.models import Page


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ["id", "title", "slug", "body", "parent", "read", "write"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["read"] = PermissionLevel(instance.read).name.replace("_", " ").title()
        representation["write"] = PermissionLevel(instance.write).name.replace("_", " ").title()
        if representation["parent"] is None:
            representation.pop("parent")
        return representation
