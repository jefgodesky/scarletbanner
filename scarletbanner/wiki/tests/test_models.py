import pytest
from django.contrib.auth import get_user_model
from slugify import slugify

from scarletbanner.wiki.enums import PermissionLevel
from scarletbanner.wiki.models import Page
from scarletbanner.wiki.tests.factories import make_page
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
        assert page.title == updated_title
        assert page.body == updated_body
        assert page.history.first().history_change_reason == message

    def test_editors(self, user, other, page):
        page.update(other, "Updated Page", "This is a test.", "Test")
        assert page.editors.count() == 2
        assert all(isinstance(editor, User) for editor in page.editors)

    @pytest.mark.parametrize(
        "permission, reader_fixture, expected",
        [
            (PermissionLevel.PUBLIC, None, True),
            (PermissionLevel.PUBLIC, "other", True),
            (PermissionLevel.PUBLIC, "user", True),
            (PermissionLevel.PUBLIC, "admin", True),
            (PermissionLevel.MEMBERS_ONLY, None, False),
            (PermissionLevel.MEMBERS_ONLY, "other", True),
            (PermissionLevel.MEMBERS_ONLY, "user", True),
            (PermissionLevel.MEMBERS_ONLY, "admin", True),
            (PermissionLevel.EDITORS_ONLY, None, False),
            (PermissionLevel.EDITORS_ONLY, "other", False),
            (PermissionLevel.EDITORS_ONLY, "user", True),
            (PermissionLevel.EDITORS_ONLY, "admin", True),
            (PermissionLevel.ADMIN_ONLY, None, False),
            (PermissionLevel.ADMIN_ONLY, "other", False),
            (PermissionLevel.ADMIN_ONLY, "user", False),
            (PermissionLevel.ADMIN_ONLY, "admin", True),
        ],
    )
    def test_can_read(self, request, permission, reader_fixture, expected, user):
        page = make_page(user=user, read=permission)
        reader = (
            None
            if reader_fixture is None
            else user
            if reader_fixture == "user"
            else request.getfixturevalue(reader_fixture)
        )
        assert page.can_read(reader) == expected

    @pytest.mark.parametrize(
        "before, after, reader_fixture, expected",
        [
            (PermissionLevel.PUBLIC, PermissionLevel.PUBLIC, None, True),
            (PermissionLevel.PUBLIC, PermissionLevel.MEMBERS_ONLY, None, False),
            (PermissionLevel.PUBLIC, PermissionLevel.EDITORS_ONLY, None, False),
            (PermissionLevel.PUBLIC, PermissionLevel.ADMIN_ONLY, None, False),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.PUBLIC, None, False),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.MEMBERS_ONLY, None, False),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.EDITORS_ONLY, None, False),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.ADMIN_ONLY, None, False),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.PUBLIC, None, False),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.MEMBERS_ONLY, None, False),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.EDITORS_ONLY, None, False),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.ADMIN_ONLY, None, False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.PUBLIC, None, False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.MEMBERS_ONLY, None, False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.EDITORS_ONLY, None, False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.ADMIN_ONLY, None, False),
            (PermissionLevel.PUBLIC, PermissionLevel.PUBLIC, "other", True),
            (PermissionLevel.PUBLIC, PermissionLevel.MEMBERS_ONLY, "other", True),
            (PermissionLevel.PUBLIC, PermissionLevel.EDITORS_ONLY, "other", False),
            (PermissionLevel.PUBLIC, PermissionLevel.ADMIN_ONLY, "other", False),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.PUBLIC, "other", True),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.MEMBERS_ONLY, "other", True),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.EDITORS_ONLY, "other", False),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.ADMIN_ONLY, "other", False),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.PUBLIC, "other", False),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.MEMBERS_ONLY, "other", False),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.EDITORS_ONLY, "other", False),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.ADMIN_ONLY, "other", False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.PUBLIC, "other", False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.MEMBERS_ONLY, "other", False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.EDITORS_ONLY, "other", False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.ADMIN_ONLY, "other", False),
            (PermissionLevel.PUBLIC, PermissionLevel.PUBLIC, "user", True),
            (PermissionLevel.PUBLIC, PermissionLevel.MEMBERS_ONLY, "user", True),
            (PermissionLevel.PUBLIC, PermissionLevel.EDITORS_ONLY, "user", True),
            (PermissionLevel.PUBLIC, PermissionLevel.ADMIN_ONLY, "user", False),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.PUBLIC, "user", True),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.MEMBERS_ONLY, "user", True),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.EDITORS_ONLY, "user", True),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.ADMIN_ONLY, "user", False),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.PUBLIC, "user", True),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.MEMBERS_ONLY, "user", True),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.EDITORS_ONLY, "user", True),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.ADMIN_ONLY, "user", False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.PUBLIC, "user", False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.MEMBERS_ONLY, "user", False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.EDITORS_ONLY, "user", False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.ADMIN_ONLY, "user", False),
            (PermissionLevel.PUBLIC, PermissionLevel.PUBLIC, "admin", True),
            (PermissionLevel.PUBLIC, PermissionLevel.MEMBERS_ONLY, "admin", True),
            (PermissionLevel.PUBLIC, PermissionLevel.EDITORS_ONLY, "admin", True),
            (PermissionLevel.PUBLIC, PermissionLevel.ADMIN_ONLY, "admin", True),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.PUBLIC, "admin", True),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.MEMBERS_ONLY, "admin", True),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.EDITORS_ONLY, "admin", True),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.ADMIN_ONLY, "admin", True),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.PUBLIC, "admin", True),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.MEMBERS_ONLY, "admin", True),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.EDITORS_ONLY, "admin", True),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.ADMIN_ONLY, "admin", True),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.PUBLIC, "admin", True),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.MEMBERS_ONLY, "admin", True),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.EDITORS_ONLY, "admin", True),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.ADMIN_ONLY, "admin", True),
        ],
    )
    def test_can_write(self, request, before, after, reader_fixture, expected, user):
        page = make_page(user=user, write=before)
        reader = (
            None
            if reader_fixture is None
            else user
            if reader_fixture == "user"
            else request.getfixturevalue(reader_fixture)
        )
        assert page.can_write(after, reader) == expected
