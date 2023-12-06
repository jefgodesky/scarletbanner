import pytest
from django.contrib.auth.models import AnonymousUser
from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate

from scarletbanner.users.api.views import UserViewSet
from scarletbanner.users.models import User
from scarletbanner.users.tests.factories import UserFactory


class TestUserViewSet:
    @pytest.fixture
    def api_rf(self) -> APIRequestFactory:
        return APIRequestFactory()

    @staticmethod
    def post_data(data: dict, action: str, api_rf: APIRequestFactory):
        django_request = api_rf.post("/fake-url/", data, format="json")
        drf_request = Request(django_request, parsers=[JSONParser()])
        view = UserViewSet()
        view.action = action
        view.request = drf_request
        view.kwargs = {}
        view.format_kwarg = None

        try:
            if action == "create":
                return view.create(drf_request)
        except ValidationError as ve:
            return Response(ve.detail, status=ve.status_code)

    @staticmethod
    def delete(username: str, user: User | AnonymousUser, api_rf: APIRequestFactory):
        view = UserViewSet.as_view({"delete": "destroy"})
        request = api_rf.delete(f"/fake-url/{username}/")
        if not user.is_anonymous:
            force_authenticate(request, user=user)
        response = view(request, username=username)
        return response

    def test_get_queryset(self, user: User, api_rf: APIRequestFactory):
        view = UserViewSet()
        request = api_rf.get("/fake-url/")
        request.user = user

        view.request = request

        assert user in view.get_queryset()

    @pytest.mark.django_db
    def test_create_success(self, api_rf: APIRequestFactory):
        data = {"username": "tester", "password": "testpassword123", "email": "tester@testing.com"}
        response = self.post_data(data, "create", api_rf)
        assert response.status_code == 201
        assert User.objects.filter(username=data["username"]).exists()

    @pytest.mark.django_db
    def test_create_invalid_data(self, api_rf: APIRequestFactory):
        data = {"username": "", "email": "nope"}
        response = self.post_data(data, "create", api_rf)
        assert response.status_code == 400
        assert not User.objects.filter(username=data["username"]).exists()

    @pytest.mark.django_db
    def test_destroy_not_found(self, user: User, api_rf: APIRequestFactory):
        response = self.delete("not-a-user", user, api_rf)
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_destroy_anon(self, user: User, api_rf: APIRequestFactory):
        with transaction.atomic():
            response = self.delete(user.username, AnonymousUser(), api_rf)
        user.refresh_from_db()
        assert response.status_code == 401
        assert user.is_active is True

    @pytest.mark.django_db
    def test_destroy_self(self, user: User, api_rf: APIRequestFactory):
        with transaction.atomic():
            response = self.delete(user.username, user, api_rf)
        user.refresh_from_db()
        assert response.status_code == 200
        assert user.is_active is False

    @pytest.mark.django_db
    def test_destroy_other(self, user: User, api_rf: APIRequestFactory):
        with transaction.atomic():
            other = UserFactory()
            response = self.delete(user.username, other, api_rf)
        user.refresh_from_db()
        assert response.status_code == 403
        assert user.is_active is True

    @pytest.mark.django_db
    def test_destroy_staff(self, user: User, api_rf: APIRequestFactory):
        with transaction.atomic():
            staff = UserFactory(is_staff=True)
            response = self.delete(user.username, staff, api_rf)
        user.refresh_from_db()
        assert response.status_code == 200
        assert user.is_active is False

    def test_me(self, user: User, api_rf: APIRequestFactory):
        view = UserViewSet()
        request = api_rf.get("/fake-url/")
        request.user = user

        view.request = request

        response = view.me(request)  # type: ignore

        assert response.data == {
            "username": user.username,
            "url": f"http://testserver/api/v1/users/{user.username}/",
            "name": user.name,
        }
