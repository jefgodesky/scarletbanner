import factory
from faker import Faker
from slugify import slugify

from scarletbanner.wiki.models import Page

fake = Faker()


class PageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Page

    title = factory.Faker("sentence")
    slug = factory.LazyAttribute(lambda x: slugify(x.title))
    body = factory.Faker("text")
