import pytest
from django.contrib.auth import get_user_model
from slugify import slugify

from scarletbanner.wiki.enums import PermissionLevel
from scarletbanner.wiki.models import (
    Character,
    File,
    OwnedPage,
    Page,
    Secret,
    SecretCategory,
    SecretEvaluator,
    Template,
)
from scarletbanner.wiki.tests.factories import SecretFactory, make_character, make_owned_page, make_page
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

    def test_create_child(self, child_page):
        assert isinstance(child_page, Page)
        assert isinstance(child_page.parent, Page)
        assert child_page.slug == "parent/child"

    def test_unique_slug(self, page):
        with pytest.raises(ValueError):
            Page.create(page.editors[0], "Second Page", "This is a test.", "Test", page.slug)

    def test_unique_slug_element(self, grandchild_page):
        assert grandchild_page.unique_slug_element == "grandchild"
        assert grandchild_page.parent.unique_slug_element == "child"
        assert grandchild_page.parent.parent.unique_slug_element == "parent"

    def test_update(self, user, page):
        updated_title = "Updated Page"
        updated_body = "This is a test."
        message = "Test"
        page.update(editor=user, title=updated_title, body=updated_body, message=message)
        assert page.title == updated_title
        assert page.body == updated_body
        assert page.history.first().history_change_reason == message

    def test_patch(self, user, page):
        updated_title = "Updated Page"
        message = "Test patching"
        body_before = page.body
        page.update(editor=user, title=updated_title, message=message)
        assert page.title == updated_title
        assert page.body == body_before

    def test_update_parent(self, page, child_page):
        page.update(parent=child_page.parent, editor=page.editors[0], message="Test")
        assert page.parent == child_page.parent
        assert page.slug.startswith(child_page.parent.slug + "/")

    def test_update_cannot_lock_self_out_write(self, user, page):
        before = page.history.count()
        updated_title = "Updated Page"
        page.update(
            editor=user, title=updated_title, body="Test", message="Lock out", write=PermissionLevel.ADMIN_ONLY
        )
        assert page.title != updated_title
        assert page.history.count() == before

    def test_update_can_make_editors_only_write(self, user, other, page):
        updated_title = "Updated Page"
        page.update(
            editor=other, title=updated_title, body="Test", message="Editors only", write=PermissionLevel.EDITORS_ONLY
        )
        assert page.title == updated_title
        assert other in page.editors
        assert page.can_read(other)

    def test_update_cannot_lock_self_out_read(self, user, page):
        before = page.history.count()
        updated_title = "Updated Page"
        page.update(editor=user, title=updated_title, body="Test", message="Lock out", read=PermissionLevel.ADMIN_ONLY)
        assert page.title != updated_title
        assert page.history.count() == before

    def test_update_can_make_editors_only_read(self, user, other, page):
        updated_title = "Updated Page"
        page.update(
            editor=other, title=updated_title, body="Test", message="Editors only", read=PermissionLevel.EDITORS_ONLY
        )
        assert page.title == updated_title
        assert other in page.editors
        assert page.can_read(other)

    def test_destroy(self, page):
        pk = page.pk
        page.destroy(page.editors[0])
        with pytest.raises(Page.DoesNotExist):
            Page.objects.get(pk=pk)

    def test_destroy_grandparent(self, grandchild_page):
        grandchild_page.parent.parent.destroy(grandchild_page.editors[0])
        grandchild_page.refresh_from_db()
        assert grandchild_page.parent.parent is None
        assert grandchild_page.parent.slug == "child"
        assert grandchild_page.parent.children.first() == grandchild_page
        assert isinstance(grandchild_page.parent, Page)
        assert grandchild_page.slug == "child/grandchild"

    def test_destroy_middle(self, grandchild_page):
        grandparent = grandchild_page.parent.parent
        grandchild_page.parent.destroy(grandchild_page.editors[0])
        grandchild_page.refresh_from_db()
        assert grandparent.slug == "parent"
        assert grandparent.children.first() == grandchild_page
        assert grandchild_page.parent == grandparent
        assert grandchild_page.slug == "parent/grandchild"

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
        page.read = after.value
        assert page.can_write(after, reader) == expected


@pytest.mark.django_db
class TestOwnedPage:
    def test_create(self, owned_page):
        assert isinstance(owned_page, OwnedPage)
        assert isinstance(owned_page.owner, User)
        assert isstring(owned_page.title)
        assert isstring(owned_page.slug)
        assert isstring(owned_page.body)

    @pytest.mark.parametrize(
        "permission, reader_fixture, expected",
        [
            (PermissionLevel.OWNER_ONLY, None, False),
            (PermissionLevel.OWNER_ONLY, "other", False),
            (PermissionLevel.OWNER_ONLY, "user", False),
            (PermissionLevel.OWNER_ONLY, "owner", True),
            (PermissionLevel.OWNER_ONLY, "admin", True),
        ],
    )
    def test_can_read(self, request, permission, reader_fixture, expected, user, owner):
        page = make_owned_page(user=user, owner=owner, read=permission)
        reader = (
            None
            if reader_fixture is None
            else user
            if reader_fixture == "user"
            else page.owner
            if reader_fixture == "owner"
            else request.getfixturevalue(reader_fixture)
        )
        assert page.can_read(reader) == expected

    @pytest.mark.parametrize(
        "before, after, reader_fixture, expected",
        [
            (PermissionLevel.PUBLIC, PermissionLevel.OWNER_ONLY, None, False),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.OWNER_ONLY, None, False),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.OWNER_ONLY, None, False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.OWNER_ONLY, None, False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.OWNER_ONLY, None, False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.PUBLIC, None, False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.MEMBERS_ONLY, None, False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.EDITORS_ONLY, None, False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.ADMIN_ONLY, None, False),
            (PermissionLevel.PUBLIC, PermissionLevel.OWNER_ONLY, "other", False),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.OWNER_ONLY, "other", False),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.OWNER_ONLY, "other", False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.OWNER_ONLY, "other", False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.OWNER_ONLY, "other", False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.PUBLIC, "other", False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.MEMBERS_ONLY, "other", False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.EDITORS_ONLY, "other", False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.ADMIN_ONLY, "other", False),
            (PermissionLevel.PUBLIC, PermissionLevel.OWNER_ONLY, "user", False),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.OWNER_ONLY, "user", False),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.OWNER_ONLY, "user", False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.OWNER_ONLY, "user", False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.OWNER_ONLY, "user", False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.PUBLIC, "user", False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.MEMBERS_ONLY, "user", False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.EDITORS_ONLY, "user", False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.ADMIN_ONLY, "user", False),
            (PermissionLevel.PUBLIC, PermissionLevel.OWNER_ONLY, "owner", True),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.OWNER_ONLY, "owner", True),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.OWNER_ONLY, "owner", True),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.OWNER_ONLY, "owner", True),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.OWNER_ONLY, "owner", False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.PUBLIC, "owner", True),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.MEMBERS_ONLY, "owner", True),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.EDITORS_ONLY, "owner", True),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.ADMIN_ONLY, "owner", False),
            (PermissionLevel.PUBLIC, PermissionLevel.OWNER_ONLY, "admin", True),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.OWNER_ONLY, "admin", True),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.OWNER_ONLY, "admin", True),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.OWNER_ONLY, "admin", True),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.OWNER_ONLY, "admin", True),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.PUBLIC, "admin", True),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.MEMBERS_ONLY, "admin", True),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.EDITORS_ONLY, "admin", True),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.ADMIN_ONLY, "admin", True),
        ],
    )
    def test_can_write(self, request, before, after, reader_fixture, expected, user, owner):
        page = make_owned_page(user=user, owner=owner, write=before)
        reader = (
            None
            if reader_fixture is None
            else user
            if reader_fixture == "user"
            else owner
            if reader_fixture == "owner"
            else request.getfixturevalue(reader_fixture)
        )
        page.read = after.value
        assert page.can_write(after, reader) == expected


@pytest.mark.django_db
class TestCharacter:
    def test_create(self, character):
        assert isinstance(character, Character)
        assert isinstance(character.player, User)


@pytest.mark.django_db
class TestTemplate:
    def test_create(self, template):
        assert isinstance(template, Template)


@pytest.mark.django_db
class TestFile:
    def test_create(self, file):
        assert isinstance(file, File)
        assert file.attachment is not None
        assert file.attachment.name == "uploads/test.txt"
        assert file.attachment.size == 18
        assert file.size == "18 B"
        assert file.content_type == "text/plain"

    def test_human_readable(self):
        assert File.get_human_readable_size(500) == "500 B"
        assert File.get_human_readable_size(5000) == "4.9 kB"
        assert File.get_human_readable_size(5000000) == "4.8 MB"
        assert File.get_human_readable_size(5000000000) == "4.7 GB"


@pytest.mark.django_db
class TestSecretCategory:
    def test_create_read(self, secret_category):
        assert isinstance(secret_category, SecretCategory)
        assert isstring(secret_category.name)
        assert isstring(secret_category.parent.name)
        assert secret_category.children.count() == 1
        assert isstring(secret_category.children.first().name)

    def test_str(self, secret_category):
        assert str(secret_category) == secret_category.name


@pytest.mark.django_db
class TestSecret:
    def test_create_read(self, secret):
        assert isinstance(secret, Secret)
        assert isstring(secret.key)
        assert isstring(secret.description)
        assert secret.categories.count() == 1
        assert isstring(secret.categories.first().name)
        assert secret.known_to.count() == 1
        assert isinstance(secret.known_to.first(), Character)

    def test_str(self, secret):
        assert str(secret) == secret.key

    def test_knows(self, secret, character):
        fool = make_character()
        assert secret.knows(secret.known_to.first())
        assert not secret.knows(fool)

    def test_evaluate(self):
        expression, alice, bob, charlie = TestSecretEvaluator.setup()
        assert not Secret.evaluate(expression, alice)
        assert Secret.evaluate(expression, bob)
        assert Secret.evaluate(expression, charlie)


@pytest.mark.django_db
class TestSecretEvaluator:
    def test_evaluate(self):
        expression, alice, bob, charlie = TestSecretEvaluator.setup()
        assert not SecretEvaluator(alice).eval(expression)
        assert SecretEvaluator(bob).eval(expression)
        assert SecretEvaluator(charlie).eval(expression)

    @staticmethod
    def setup():
        alice = make_character()
        bob = make_character()
        charlie = make_character()

        secrets = [
            SecretFactory(),
            SecretFactory(),
            SecretFactory(),
        ]

        secrets[0].known_to.set([alice, bob])
        secrets[1].known_to.set([bob])
        secrets[2].known_to.set([charlie])

        keys = [secret.key for secret in secrets]
        expression = f"([{keys[0]}] and [{keys[1]}]) or [{keys[2]}]"
        return expression, alice, bob, charlie
