import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory

from scarletbanner.wiki.api.views import PageViewSet
from scarletbanner.wiki.models import Page


@pytest.mark.django_db
class TestPageViewSet:
    @pytest.fixture
    def api_rf(self) -> APIRequestFactory:
        return APIRequestFactory()

    def test_list_pages(self, api_rf: APIRequestFactory, page: Page):
        view = PageViewSet.as_view({"get": "list"})
        request = api_rf.get("/api/v1/pages/")
        response = view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data[0]["title"] == page.title
