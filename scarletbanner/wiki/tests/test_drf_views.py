from urllib.parse import quote

import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory

from scarletbanner.wiki.api.views import PageViewSet
from scarletbanner.wiki.models import Page
from scarletbanner.wiki.tests.factories import make_page


@pytest.mark.django_db
class TestPageViewSet:
    @pytest.fixture
    def api_rf(self) -> APIRequestFactory:
        return APIRequestFactory()

    def test_list_pages(self, api_rf: APIRequestFactory, page: Page):
        view = PageViewSet.as_view({"get": "list"})
        request = api_rf.get("/api/v1/wiki/")
        response = view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["query"] == ""
        assert response.data["offset"] == 0
        assert response.data["limit"] == 50
        assert response.data["pages"][0]["title"] == page.title

    def test_list_pagination(self, api_rf: APIRequestFactory):
        view = PageViewSet.as_view({"get": "list"})
        pages = [make_page(title=f"Page {i}") for i in range(5, 0, -1)]

        request = api_rf.get("/api/v1/wiki/?offset=0&limit=2")
        response = view(request)
        assert response.data["offset"] == 0
        assert response.data["limit"] == 2
        assert response.data["total"] == 5
        assert response.data["pages"][0]["title"] == pages[4].title
        assert response.data["pages"][1]["title"] == pages[3].title

        request = api_rf.get("/api/v1/wiki/?offset=2&limit=2")
        response = view(request)
        assert response.data["offset"] == 2
        assert response.data["limit"] == 2
        assert response.data["total"] == 5
        assert response.data["pages"][0]["title"] == pages[2].title
        assert response.data["pages"][1]["title"] == pages[1].title

        request = api_rf.get("/api/v1/wiki/?offset=4&limit=2")
        response = view(request)
        assert response.data["offset"] == 4
        assert response.data["limit"] == 2
        assert response.data["total"] == 5
        assert response.data["pages"][0]["title"] == pages[0].title

    def test_list_title_query(self, api_rf: APIRequestFactory, page: Page):
        view = PageViewSet.as_view({"get": "list"})
        request = api_rf.get(f"/api/v1/wiki/?query={quote(page.title)}")
        response = view(request)
        assert response.data["total"] == 1
        assert response.data["pages"][0]["id"] == page.id

    def test_list_path_query(self, api_rf: APIRequestFactory, page: Page):
        view = PageViewSet.as_view({"get": "list"})
        request = api_rf.get(f"/api/v1/wiki/?query={quote(page.slug)}")
        response = view(request)
        assert response.data["total"] == 1
        assert response.data["pages"][0]["id"] == page.id

    def test_list_no_results_query(self, api_rf: APIRequestFactory, page: Page):
        view = PageViewSet.as_view({"get": "list"})
        request = api_rf.get("/api/v1/wiki/?query=nope")
        response = view(request)
        assert response.data["total"] == 0

    def test_retrieve_page(self, api_rf: APIRequestFactory, page: Page):
        view = PageViewSet.as_view({"get": "retrieve"})
        request = api_rf.get(f"/api/v1/wiki/{page.slug}")
        response = view(request, slug=page.slug)
        assert response.status_code == status.HTTP_200_OK
        print(response.data)
        assert response.data["title"] == page.title

    def test_retrieve_child(self, api_rf: APIRequestFactory, grandchild_page: Page):
        view = PageViewSet.as_view({"get": "retrieve"})
        request = api_rf.get(f"/api/v1/wiki/{grandchild_page.slug}")
        response = view(request, slug=grandchild_page.slug)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == grandchild_page.title
