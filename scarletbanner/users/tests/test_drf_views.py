import pytest
from django.contrib.auth.models import AnonymousUser
from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from scarletbanner.users.api.serializers import UserCreateSerializer, UserPublicSerializer, UserSerializer
from scarletbanner.users.api.views import UserViewSet
from scarletbanner.users.models import User
from scarletbanner.users.tests.factories import UserFactory


class TestUserViewSet:
    @pytest.fixture
    def api_rf(self) -> APIRequestFactory:
        return APIRequestFactory()

    @staticmethod
    def request(
        url: str,
        action: str,
        method: str,
        subj: User | AnonymousUser,
        api_rf: APIRequestFactory,
        obj: User = None,
        data: dict = None,
    ):
        view = UserViewSet()
        req_method = getattr(api_rf, method)
        dj_request = req_method(url, data, format="json") if data is not None else req_method(url)
        view.action = action
        view.request = Request(dj_request, parsers=[JSONParser()])
        view.request.user = subj
        view.kwargs = {"username": obj.username} if obj is not None else {}
        view.format_kwarg = None
        view.request.url_kwargs = view.kwargs
        return view

    def get_serializer(self, action: str, subj: User | AnonymousUser, api_rf: APIRequestFactory, obj: User = None):
        url = "/fake-url/" if obj is None else f"/fake-url/{obj.username}/"
        view = self.request(url, action, "get", subj, api_rf, obj)
        return view.get_serializer_class()

    def create(self, data: dict, api_rf: APIRequestFactory):
        view = self.request("/fake-url/", "create", "post", AnonymousUser(), api_rf, None, data)
        return view.create(view.request)

    def destroy(self, subj: User | AnonymousUser, obj: User, api_rf: APIRequestFactory):
        url = f"/fake-url/{obj.username}/"
        view = self.request(url, "destroy", "delete", subj, api_rf, obj)
        return view.destroy(view.request)

    def test_get_queryset(self, user: User, api_rf: APIRequestFactory):
        view = self.request("/fake-url/", "retrieve", "get", AnonymousUser(), api_rf)
        assert user in view.get_queryset()

    def test_get_serializer_create(self, api_rf: APIRequestFactory):
        serializer = self.get_serializer("create", AnonymousUser(), api_rf)
        assert serializer is UserCreateSerializer

    def test_get_serializer_anon(self, user: User, api_rf: APIRequestFactory):
        serializer = self.get_serializer("retrieve", AnonymousUser(), api_rf, user)
        assert serializer is UserPublicSerializer

    def test_get_serializer_self(self, user: User, api_rf: APIRequestFactory):
        serializer = self.get_serializer("retrieve", user, api_rf, user)
        assert serializer is UserSerializer

    def test_get_serializer_other(self, user: User, api_rf: APIRequestFactory):
        other = UserFactory()
        serializer = self.get_serializer("retrieve", other, api_rf, user)
        assert serializer is UserPublicSerializer

    def test_get_serializer_staff(self, user: User, api_rf: APIRequestFactory):
        staff = UserFactory(is_staff=True)
        serializer = self.get_serializer("retrieve", staff, api_rf, user)
        assert serializer is UserSerializer

    @pytest.mark.django_db
    def test_create_success(self, api_rf: APIRequestFactory):
        data = {"username": "tester", "password": "testpassword123", "email": "tester@testing.com"}
        response = self.create(data, api_rf)
        assert response.status_code == 201
        assert User.objects.filter(username=data["username"]).exists()

    @pytest.mark.django_db
    def test_create_invalid_data(self, api_rf: APIRequestFactory):
        data = {"username": "", "email": "nope"}
        with pytest.raises(ValidationError):
            response = self.create(data, api_rf)
            assert response.status_code == 400
            assert not User.objects.filter(username=data["username"]).exists()

    @pytest.mark.django_db
    def test_destroy_anon(self, user: User, api_rf: APIRequestFactory):
        with transaction.atomic():
            with pytest.raises(PermissionDenied):
                response = self.destroy(AnonymousUser(), user, api_rf)
                user.refresh_from_db()
                assert response.status_code == 401
                assert user.is_active is True

    @pytest.mark.django_db
    def test_destroy_self(self, user: User, api_rf: APIRequestFactory):
        with transaction.atomic():
            response = self.destroy(user, user, api_rf)
        user.refresh_from_db()
        assert response.status_code == 200
        assert user.is_active is False

    @pytest.mark.django_db
    def test_destroy_other(self, user: User, api_rf: APIRequestFactory):
        with transaction.atomic():
            with pytest.raises(PermissionDenied):
                other = UserFactory()
                response = self.destroy(other, user, api_rf)
                user.refresh_from_db()
                assert response.status_code == 403
                assert user.is_active is True

    @pytest.mark.django_db
    def test_destroy_staff(self, user: User, api_rf: APIRequestFactory):
        with transaction.atomic():
            staff = UserFactory(is_staff=True)
            response = self.destroy(staff, user, api_rf)
        user.refresh_from_db()
        assert response.status_code == 200
        assert user.is_active is False

    def test_me(self, user: User, api_rf: APIRequestFactory):
        view = self.request("/fake-url/", "me", "get", user, api_rf)
        response = view.me(view.request)

        assert response.data == {
            "username": user.username,
            "url": f"http://testserver/api/v1/users/{user.username}/",
            "name": user.name,
        }
