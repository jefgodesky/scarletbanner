import pytest
from slugify import slugify

from scarletbanner.wiki.enums import PermissionLevel
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
        assert page.read == PermissionLevel.PUBLIC.value
        assert page.write == PermissionLevel.PUBLIC.value

    def test_create_default_message(self):
        page = Page.create("Test Page", "This is a test.")
        history = page.history.first()
        assert history.history_change_reason == "Initial text"

    def test_create_message(self):
        page = Page.create("Test Page", "This is a test.", "Test")
        history = page.history.first()
        assert history.history_change_reason == "Test"
