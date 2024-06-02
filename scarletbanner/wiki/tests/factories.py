from django.contrib.auth import get_user_model
from faker import Faker
from slugify import slugify

from scarletbanner.users.tests.factories import UserFactory
from scarletbanner.wiki.enums import PermissionLevel
from scarletbanner.wiki.models import OwnedPage, Page

fake = Faker()
User = get_user_model()


def make_page(**kwargs) -> Page:
    title = kwargs.get("title", fake.sentence())
    slug = kwargs.get("slug", slugify(title))
    body = kwargs.get("body", fake.text())
    parent = kwargs.get("parent", None)
    read = kwargs.get("read", PermissionLevel.PUBLIC)
    write = kwargs.get("write", PermissionLevel.PUBLIC)
    user = kwargs.get("user", UserFactory())
    message = kwargs.get("message", "Initial text")
    return Page.create(user, title, body, message, slug, parent, read, write)


def make_owned_page(**kwargs) -> Page:
    title = kwargs.get("title", fake.sentence())
    slug = kwargs.get("slug", slugify(title))
    body = kwargs.get("body", fake.text())
    parent = kwargs.get("parent", None)
    read = kwargs.get("read", PermissionLevel.PUBLIC)
    write = kwargs.get("write", PermissionLevel.PUBLIC)
    user = kwargs.get("user", UserFactory())
    owner = kwargs.get("owner", user)
    message = kwargs.get("message", "Initial text")
    return OwnedPage.create(user, title, body, message, slug, parent, owner, read, write)
