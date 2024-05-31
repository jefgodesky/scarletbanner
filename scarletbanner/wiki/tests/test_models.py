import pytest
from django.contrib.auth import get_user_model
from slugify import slugify

from scarletbanner.wiki.enums import PermissionLevel
from scarletbanner.wiki.models import Page
from scarletbanner.wiki.tests.utils import isstring

User = get_user_model()


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

    def test_create_default_message(self, user):
        page = Page.create(user, "Test Page", "This is a test.")
        history = page.history.first()
        assert history.history_change_reason == "Initial text"

    def test_create_message(self, user):
        page = Page.create(user, "Test Page", "This is a test.", "Test")
        history = page.history.first()
        assert history.history_change_reason == "Test"

    def test_update(self, user, page):
        updated_title = "Updated Page"
        updated_body = "This is a test."
        message = "Test"
        page.update(user, updated_title, updated_body, message)
        history = page.history.first()
        assert page.title == updated_title
        assert page.body == updated_body
        assert history.history_change_reason == message

    def test_editors(self, user, page):
        page.update(user, "Updated Page", "This is a test.", "Test")
        assert page.editors.count() == 2
        assert all(isinstance(editor, User) for editor in page.editors)
