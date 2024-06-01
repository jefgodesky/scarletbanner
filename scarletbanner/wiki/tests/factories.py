from django.contrib.auth import get_user_model
import factory
from faker import Faker
from slugify import slugify

from scarletbanner.users.tests.factories import UserFactory
from scarletbanner.wiki.enums import PermissionLevel
from scarletbanner.wiki.models import Page

fake = Faker()
User = get_user_model()


def make_page(**kwargs) -> Page:
    title = kwargs.get("title", fake.sentence())
    slug = kwargs.get("slug", slugify(title))
    body = kwargs.get("body", fake.text())
    read = kwargs.get("read", PermissionLevel.PUBLIC)
    write = kwargs.get("write", PermissionLevel.PUBLIC)
    user = kwargs.get("user", UserFactory())
    message = kwargs.get("message", "Initial text")
    return Page.create(user, title, body, message, slug, read, write)
