from django.contrib.auth import get_user_model
from faker import Faker
from slugify import slugify

from scarletbanner.users.tests.factories import UserFactory
from scarletbanner.wiki.enums import PermissionLevel
from scarletbanner.wiki.models import Character, OwnedPage, Page

fake = Faker()
User = get_user_model()


def make_page_instance(cls, **kwargs):
    title = kwargs.get("title", fake.sentence())
    slug = kwargs.get("slug", slugify(title))
    body = kwargs.get("body", fake.text())
    parent = kwargs.get("parent", None)
    read = kwargs.get("read", PermissionLevel.PUBLIC)
    write = kwargs.get("write", PermissionLevel.PUBLIC)
    user = kwargs.get("user", UserFactory())
    message = kwargs.get("message", "Initial text")

    if issubclass(cls, OwnedPage):
        owner = kwargs.get("owner", user)
        return cls.create(user, title, body, message, slug, parent, owner, read, write)
    else:
        return cls.create(user, title, body, message, slug, parent, read, write)


def make_page(**kwargs) -> Page:
    return make_page_instance(Page, **kwargs)


def make_owned_page(**kwargs) -> OwnedPage:
    return make_page_instance(OwnedPage, **kwargs)


def make_character(**kwargs) -> Character:
    return make_page_instance(Character, **kwargs)
