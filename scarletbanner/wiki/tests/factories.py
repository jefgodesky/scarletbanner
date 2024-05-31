import factory
from faker import Faker
from slugify import slugify

from scarletbanner.users.tests.factories import UserFactory
from scarletbanner.wiki.models import Page

fake = Faker()


class PageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Page

    title = factory.Faker("sentence")
    slug = factory.LazyAttribute(lambda x: slugify(x.title))
    body = factory.Faker("text")

    @factory.post_generation
    def set_version_info(self, create, extracted, **kwargs):
        user = kwargs.pop("user", UserFactory())
        print("Hello")
        self.stamp_revision(user, "Initial text")

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        instance.save()
