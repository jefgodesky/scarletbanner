import pytest

from scarletbanner.users.models import User
from scarletbanner.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> User:
    return UserFactory()


@pytest.fixture
def owner(db) -> User:
    return UserFactory()


@pytest.fixture
def other(db) -> User:
    return UserFactory()


@pytest.fixture
def admin(db) -> User:
    return UserFactory(is_staff=True, is_superuser=True)
