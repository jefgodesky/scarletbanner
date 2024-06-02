import factory
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from factory.django import DjangoModelFactory
from faker import Faker
from slugify import slugify

from scarletbanner.users.tests.factories import UserFactory
from scarletbanner.wiki.enums import PermissionLevel
from scarletbanner.wiki.models import Character, File, OwnedPage, Page, Secret, SecretCategory, Template

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
    elif issubclass(cls, File):
        file_name = kwargs.get("file_name", "test.txt")
        file_contents = kwargs.get("file_contents", b"Test file content.")
        attachment = kwargs.get("attachment", SimpleUploadedFile(file_name, file_contents))
        return cls.create(user, title, body, message, slug, parent, attachment, read, write)
    else:
        return cls.create(user, title, body, message, slug, parent, read, write)


def make_page(**kwargs) -> Page:
    return make_page_instance(Page, **kwargs)


def make_owned_page(**kwargs) -> OwnedPage:
    return make_page_instance(OwnedPage, **kwargs)


def make_character(**kwargs) -> Character:
    return make_page_instance(Character, **kwargs)


def make_template(**kwargs) -> Template:
    return make_page_instance(Template, **kwargs)


def make_file(**kwargs) -> File:
    return make_page_instance(File, **kwargs)


class SecretCategoryFactory(DjangoModelFactory):
    class Meta:
        model = SecretCategory

    name = factory.Faker("sentence")
    parent = None

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        instance.save()


class SecretFactory(DjangoModelFactory):
    class Meta:
        model = Secret

    key = factory.Faker("sentence")
    description = factory.Faker("text")

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        instance.save()

    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for category in extracted:
                self.categories.add(category)

    @factory.post_generation
    def known_to(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for character in extracted:
                self.known_to.add(character)
