import pytest
from slugify import slugify

from scarletbanner.wiki.models import Page
from scarletbanner.wiki.tests.utils import isstring


@pytest.mark.django_db
class TestPage:
    def test_create(self, page):
        assert isinstance(page, Page)
        assert isstring(page.title)
        assert isstring(page.slug)
        assert isstring(page.body)
        assert page.slug == slugify(page.title)
