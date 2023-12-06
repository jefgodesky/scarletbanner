import pytest
from django.contrib.auth.models import AnonymousUser, User
from rest_framework.exceptions import NotAuthenticated
from rest_framework.test import APIRequestFactory

from scarletbanner.users.tests.factories import UserFactory

from .permissions import IsAuthenticated, IsSelfOrStaff


class TestIsAuthenticated:
    @pytest.fixture
    def api_rf(self) -> APIRequestFactory:
        return APIRequestFactory()

    @staticmethod
    def run(user: User | AnonymousUser, api_rf: APIRequestFactory):
        request = api_rf.get("/fake-url/")
        request.user = user
        permission = IsAuthenticated()
        return permission.has_permission(request, None)

    def test_anon(self, api_rf: APIRequestFactory):
        with pytest.raises(NotAuthenticated):
            self.run(AnonymousUser(), api_rf)

    def test_user(self, user: User, api_rf: APIRequestFactory):
        assert self.run(user, api_rf)


class TestIsSelfOrStaff:
    @pytest.fixture
    def api_rf(self) -> APIRequestFactory:
        return APIRequestFactory()

    @staticmethod
    def run(object: User, subject: User | AnonymousUser, api_rf: APIRequestFactory):
        request = api_rf.get(f"/fake-url/{object.username}/")
        request.user = subject
        permission = IsSelfOrStaff()
        return permission.has_object_permission(request, None, object)

    def test_anon(self, user: User, api_rf: APIRequestFactory):
        assert not self.run(user, AnonymousUser(), api_rf)

    def test_self(self, user: User, api_rf: APIRequestFactory):
        assert self.run(user, user, api_rf)

    def test_other(self, user: User, api_rf: APIRequestFactory):
        other = UserFactory()
        assert not self.run(user, other, api_rf)

    def test_staff(self, user: User, api_rf: APIRequestFactory):
        staff = UserFactory(is_staff=True)
        assert self.run(user, staff, api_rf)
