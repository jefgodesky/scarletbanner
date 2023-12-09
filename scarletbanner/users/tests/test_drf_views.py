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

    def retrieve(self, subj: User | AnonymousUser, obj: User, api_rf: APIRequestFactory):
        url = f"/fake-url/{obj.username}/"
        view = self.request(url, "retrieve", "get", subj, api_rf, obj)
        return view.retrieve(view.request)

    def list(self, user: User | AnonymousUser, api_rf: APIRequestFactory):
        num = 3
        users = [UserFactory() for _ in range(num)]
        if not user.is_anonymous:
            users.insert(0, user)
        view = self.request("/fake-url/", "list", "get", user, api_rf)
        users = sorted(users, key=lambda u: u.date_joined)
        return view.list(view.request), users

    def update(self, subj: User | AnonymousUser, obj: User, update: dict, api_rf: APIRequestFactory):
        url = f"/fake-url/{obj.username}/"
        view = self.request(url, "update", "put", subj, api_rf, obj, update)
        return view.update(view.request)

    def destroy(self, subj: User | AnonymousUser, obj: User, api_rf: APIRequestFactory):
        url = f"/fake-url/{obj.username}/"
        view = self.request(url, "destroy", "delete", subj, api_rf, obj)
        return view.destroy(view.request)

    @staticmethod
    def assert_public(user, data):
        assert data["username"] == user.username
        assert data["url"] == f"http://testserver/api/v1/users/{user.username}/"
        assert data["is_active"] == user.is_active
        assert data["is_staff"] == user.is_staff
        assert "name" not in data
        assert "email" not in data

    @staticmethod
    def assert_full(user, data):
        assert data["username"] == user.username
        assert data["name"] == user.name
        assert data["email"] == user.email
        assert data["url"] == f"http://testserver/api/v1/users/{user.username}/"
        assert data["is_active"] == user.is_active
        assert data["is_staff"] == user.is_staff

    def assert_update_success(self, subj: User | AnonymousUser, obj: User, api_rf: APIRequestFactory):
        update = obj.get_dict()
        update["username"] = "tester" if update["username"] != "tester" else "other"
        response = self.update(subj, obj, update, api_rf)
        obj.refresh_from_db()
        assert response.status_code == 200
        assert obj.username == update["username"]
        self.assert_full(obj, response.data)

    def assert_update_failure(
        self, subj: User | AnonymousUser, obj: User, expected_status: int, api_rf: APIRequestFactory
    ):
        update = obj.get_dict()
        update["username"] = "tester" if update["username"] != "tester" else "other"
        with pytest.raises(PermissionDenied):
            response = self.update(subj, obj, update, api_rf)
            obj.refresh_from_db()
            assert response.status_code == 403
            assert obj.username != update["username"]

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
    def test_retrieve_anon(self, user: User, api_rf):
        response = self.retrieve(AnonymousUser(), user, api_rf)
        assert response.status_code == 200
        self.assert_public(user, response.data)

    @pytest.mark.django_db
    def test_retrieve_self(self, user: User, api_rf):
        response = self.retrieve(user, user, api_rf)
        assert response.status_code == 200
        self.assert_full(user, response.data)

    @pytest.mark.django_db
    def test_retrieve_other(self, user: User, api_rf):
        other = UserFactory()
        response = self.retrieve(other, user, api_rf)
        assert response.status_code == 200
        self.assert_public(user, response.data)

    @pytest.mark.django_db
    def test_retrieve_staff(self, user: User, api_rf: APIRequestFactory):
        staff = UserFactory(is_staff=True)
        response = self.retrieve(staff, user, api_rf)
        assert response.status_code == 200
        self.assert_full(user, response.data)

    @pytest.mark.django_db
    def test_list_anon(self, api_rf: APIRequestFactory):
        response, users = self.list(AnonymousUser(), api_rf)
        assert response.status_code == 200
        assert len(response.data) == len(users)
        for i in range(len(users)):
            self.assert_public(users[i], response.data[i])

    @pytest.mark.django_db
    def test_list_user(self, user: User, api_rf: APIRequestFactory):
        response, users = self.list(user, api_rf)
        assert response.status_code == 200
        assert len(response.data) == len(users)
        for i in range(len(users)):
            if users[i].username == user.username:
                self.assert_full(users[i], response.data[i])
            else:
                self.assert_public(users[i], response.data[i])

    @pytest.mark.django_db
    def test_list_staff(self, api_rf: APIRequestFactory):
        staff = UserFactory(is_staff=True)
        response, users = self.list(staff, api_rf)
        assert response.status_code == 200
        assert len(response.data) == len(users)
        for i in range(len(users)):
            self.assert_full(users[i], response.data[i])

    @pytest.mark.django_db
    def test_update_anon(self, user: User, api_rf: APIRequestFactory):
        self.assert_update_failure(AnonymousUser(), user, 401, api_rf)

    @pytest.mark.django_db
    def test_update_self(self, user: User, api_rf: APIRequestFactory):
        self.assert_update_success(user, user, api_rf)

    @pytest.mark.django_db
    def test_update_other(self, user: User, api_rf: APIRequestFactory):
        other = UserFactory()
        self.assert_update_failure(other, user, 403, api_rf)

    @pytest.mark.django_db
    def test_update_staff(self, user: User, api_rf: APIRequestFactory):
        staff = UserFactory(is_staff=True)
        self.assert_update_success(staff, user, api_rf)

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
            "email": user.email,
            "is_active": True,
            "is_staff": False,
        }
