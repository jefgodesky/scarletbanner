import factory
from factory.django import DjangoModelFactory
from faker import Faker
from slugify import slugify

from scarletbanner.users.tests.factories import UserFactory
from wiki.enums import PageType, PermissionLevel
from wiki.models import Revision, Secret, SecretCategory, WikiPage

fake = Faker()


class RevisionFactory(DjangoModelFactory):
    class Meta:
        model = Revision

    title = factory.Faker("sentence")
    slug = factory.LazyAttribute(lambda x: slugify(x.title))
    body = factory.Faker("text")
    editor = factory.SubFactory(UserFactory)
    page_type = PageType.PAGE.value
    read = PermissionLevel.PUBLIC.value
    write = PermissionLevel.PUBLIC.value
    is_latest = True

    @factory.post_generation
    def set_latest(self, create, extracted, **kwargs):
        if not create:
            return

        if self.page:
            self.page.revisions.update(is_latest=False)
            self.is_latest = True
            self.save()


class WikiPageFactory(DjangoModelFactory):
    class Meta:
        model = WikiPage

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        revision_kwargs = {
            "title": kwargs.pop("title", fake.text(max_nb_chars=50)),
            "slug": kwargs.pop("slug", None),
            "body": kwargs.pop("body", fake.text()),
            "editor": kwargs.pop("editor", UserFactory()),
            "owner": kwargs.pop("owner", None),
            "page_type": kwargs.pop("page_type", PageType.PAGE.value),
            "read": kwargs.pop("read", PermissionLevel.PUBLIC.value),
            "write": kwargs.pop("write", PermissionLevel.PUBLIC.value),
            "parent": kwargs.pop("parent", None),
        }

        wiki_page = super()._create(model_class, *args, **kwargs)
        RevisionFactory(page=wiki_page, **revision_kwargs)
        return wiki_page


class CharacterFactory(WikiPageFactory):
    @factory.post_generation
    def create_revision(self, create, extracted, **kwargs):
        if not create:
            return

        player = factory.SubFactory(UserFactory)
        name = fake.name()
        slug = slugify(name)
        RevisionFactory(
            page=self,
            title=name,
            slug=slug,
            body=kwargs.pop("body", fake.text()),
            page_type=PageType.CHARACTER.value,
            editor=player,
            owner=player,
            read=kwargs.pop("read", PermissionLevel.PUBLIC.value),
            write=kwargs.pop("write", PermissionLevel.PUBLIC.value),
            parent=kwargs.pop("parent", None),
        )


class SecretCategoryFactory(DjangoModelFactory):
    class Meta:
        model = SecretCategory

    name = factory.Faker("sentence")
    parent = None


class SecretFactory(DjangoModelFactory):
    class Meta:
        model = Secret

    key = factory.Faker("sentence")
    description = factory.Faker("text")

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
            for page in extracted:
                self.known_to.add(page)
