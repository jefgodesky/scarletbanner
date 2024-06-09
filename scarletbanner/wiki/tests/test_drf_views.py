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

        expected_link_header = (
            '<http://testserver/api/v1/wiki/?offset=2&limit=2>; rel="next", '
            '<http://testserver/api/v1/wiki/?offset=0&limit=2>; rel="first", '
            '<http://testserver/api/v1/wiki/?offset=4&limit=2>; rel="last"'
        )
        request = api_rf.get("/api/v1/wiki/?offset=0&limit=2")
        response = view(request)
        assert response.headers["Link"] == expected_link_header
        assert response.data["offset"] == 0
        assert response.data["limit"] == 2
        assert response.data["total"] == 5
        assert response.data["pages"][0]["title"] == pages[4].title
        assert response.data["pages"][1]["title"] == pages[3].title

        expected_link_header = (
            '<http://testserver/api/v1/wiki/?offset=0&limit=2>; rel="prev", '
            '<http://testserver/api/v1/wiki/?offset=4&limit=2>; rel="next", '
            '<http://testserver/api/v1/wiki/?offset=0&limit=2>; rel="first", '
            '<http://testserver/api/v1/wiki/?offset=4&limit=2>; rel="last"'
        )
        request = api_rf.get("/api/v1/wiki/?offset=2&limit=2")
        response = view(request)
        assert response.headers["Link"] == expected_link_header
        assert response.data["offset"] == 2
        assert response.data["limit"] == 2
        assert response.data["total"] == 5
        assert response.data["pages"][0]["title"] == pages[2].title
        assert response.data["pages"][1]["title"] == pages[1].title

        expected_link_header = (
            '<http://testserver/api/v1/wiki/?offset=2&limit=2>; rel="prev", '
            '<http://testserver/api/v1/wiki/?offset=0&limit=2>; rel="first", '
            '<http://testserver/api/v1/wiki/?offset=4&limit=2>; rel="last"'
        )
        request = api_rf.get("/api/v1/wiki/?offset=4&limit=2")
        response = view(request)
        assert response.headers["Link"] == expected_link_header
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

    @pytest.mark.parametrize(
        "reader_fixture, count, expected",
        [
            (None, 1, ["Public"]),
            ("other", 2, ["Members Only", "Public"]),
            ("user", 3, ["Editors Only", "Members Only", "Public"]),
            ("admin", 4, ["Admin Only", "Editors Only", "Members Only", "Public"]),
        ],
    )
    def test_list_permissions(self, api_rf: APIRequestFactory, list_pages, reader_fixture, count, expected, request):
        reader = None if reader_fixture is None else request.getfixturevalue(reader_fixture)
        view = PageViewSet.as_view({"get": "list"})
        request = api_rf.get("/api/v1/wiki/")
        request.user = reader
        response = view(request)
        actual = [page["title"] for page in response.data["pages"]]
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total"] == count
        assert actual == expected

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

    @pytest.mark.parametrize(
        "reader_fixture, index, expected_status",
        [
            (None, 0, status.HTTP_401_UNAUTHORIZED),
            (None, 1, status.HTTP_401_UNAUTHORIZED),
            (None, 2, status.HTTP_401_UNAUTHORIZED),
            (None, 3, status.HTTP_200_OK),
            ("other", 0, status.HTTP_403_FORBIDDEN),
            ("other", 1, status.HTTP_403_FORBIDDEN),
            ("other", 2, status.HTTP_200_OK),
            ("other", 3, status.HTTP_200_OK),
            ("user", 0, status.HTTP_403_FORBIDDEN),
            ("user", 1, status.HTTP_200_OK),
            ("user", 2, status.HTTP_200_OK),
            ("user", 3, status.HTTP_200_OK),
            ("admin", 0, status.HTTP_200_OK),
            ("admin", 1, status.HTTP_200_OK),
            ("admin", 2, status.HTTP_200_OK),
            ("admin", 3, status.HTTP_200_OK),
        ],
    )
    def test_retrieve_permissions(
        self, api_rf: APIRequestFactory, list_pages, reader_fixture, index, expected_status, request
    ):
        reader = None if reader_fixture is None else request.getfixturevalue(reader_fixture)
        view = PageViewSet.as_view({"get": "retrieve"})
        request = api_rf.get("/api/v1/wiki/")
        request.user = reader
        print(list_pages)
        response = view(request, slug=list_pages[index].slug)
        assert response.status_code == expected_status
        if expected_status == status.HTTP_200_OK:
            assert response.data["title"] == list_pages[index].title
            assert "detail" not in response.data
        else:
            assert isinstance(response.data["detail"], str)
            assert "title" not in response.data
