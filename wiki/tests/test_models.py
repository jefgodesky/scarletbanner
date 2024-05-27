import pytest
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

from wiki.enums import PageType, PermissionLevel
from wiki.models import Revision, Secret, SecretCategory, WikiPage

User = get_user_model()


def is_string(variable) -> bool:
    return isinstance(variable, str) and len(variable) > 0


@pytest.mark.django_db
class TestWikiPage:
    def test_create_read(self, wiki_page):
        assert is_string(wiki_page.title)
        assert is_string(wiki_page.slug)
        assert is_string(wiki_page.body)
        assert wiki_page.read == PermissionLevel.PUBLIC
        assert wiki_page.write == PermissionLevel.PUBLIC

    def test_create_read_character(self, character):
        assert character.page_type == PageType.CHARACTER
        assert isinstance(character.owner, User)

    def test_create_child(self, child_wiki_page):
        assert isinstance(child_wiki_page, WikiPage)

    def test_str(self, wiki_page):
        assert is_string(wiki_page.title)

    def test_get_type(self, character, other):
        all_characters = WikiPage.get_type(PageType.CHARACTER)
        player_characters = WikiPage.get_type(PageType.CHARACTER, owner=character.owner)
        other_characters = WikiPage.get_type(PageType.CHARACTER, owner=other)
        assert len(all_characters) == 1
        assert len(player_characters) == 1
        assert len(other_characters) == 0
        assert all_characters[0] == character
        assert player_characters[0] == character

    def test_update(self, updated_wiki_page):
        assert updated_wiki_page.revisions.count() == 2

    def test_update_type(self, wiki_page):
        wiki_page.update(
            page_type=PageType.CHARACTER,
            title=wiki_page.title,
            slug=wiki_page.slug,
            body=wiki_page.body,
            editor=wiki_page.created_by,
            message="Update page type",
            read=PermissionLevel.PUBLIC,
            write=PermissionLevel.PUBLIC,
        )
        assert wiki_page.page_type == PageType.CHARACTER

    def test_update_child(self, wiki_page):
        parent = WikiPage.create(
            page_type=PageType.PAGE,
            title="Parent",
            slug="parent",
            body="This is the parent page.",
            read=PermissionLevel.PUBLIC,
            write=PermissionLevel.PUBLIC,
            editor=wiki_page.created_by,
        )
        wiki_page.patch(slug="parent/test", parent=parent, editor=wiki_page.created_by, message="Patching test")
        assert wiki_page.parent == parent

    def test_update_not_allowed(self, user, other):
        page = WikiPage.create(title="Test", body="Test", editor=user, write=PermissionLevel.EDITORS_ONLY)
        page.update(
            page_type=PageType.PAGE,
            title="Updated",
            slug="updated",
            body="Updated",
            editor=other,
            message="Test update",
            write=PermissionLevel.PUBLIC,
            read=PermissionLevel.PUBLIC,
        )
        assert page.title == "Test"

    def test_update_no_lockout(self, user):
        page = WikiPage.create(title="Test", body="Test", editor=user)
        page.update(
            page_type=PageType.PAGE,
            title="Updated",
            slug="updated",
            body="Updated",
            editor=user,
            message="Test update",
            write=PermissionLevel.OWNER_ONLY,
            read=PermissionLevel.PUBLIC,
        )
        assert page.title == "Test"

    def test_patch(self, wiki_page):
        body = wiki_page.body
        updated_title = "Updated Title"
        updated_slug = "updated"
        wiki_page.patch(wiki_page.created_by, message="Patching test", title=updated_title, slug=updated_slug)
        assert wiki_page.title == updated_title
        assert wiki_page.body == body

    def test_patch_type(self, wiki_page):
        wiki_page.patch(
            page_type=PageType.CHARACTER,
            editor=wiki_page.created_by,
            message="Update page type",
        )
        assert wiki_page.page_type == PageType.CHARACTER

    def test_destroy(self, wiki_page):
        wiki_page_id = wiki_page.id
        wiki_page.destroy(wiki_page.created_by)
        with pytest.raises(WikiPage.DoesNotExist):
            WikiPage.objects.get(id=wiki_page_id)
            Revision.objects.get(wiki_page=wiki_page_id)

    def test_destroy_grandparent(self, grandchild_wiki_page):
        grandchild_wiki_page.parent.parent.destroy(grandchild_wiki_page.editors[0])
        assert grandchild_wiki_page.parent.parent is None
        assert grandchild_wiki_page.parent.slug == "child"
        assert grandchild_wiki_page.parent.children[0] == grandchild_wiki_page
        assert isinstance(grandchild_wiki_page.parent, WikiPage)
        assert grandchild_wiki_page.slug == "child/grandchild"

    def test_destroy_middle(self, grandchild_wiki_page):
        grandparent = grandchild_wiki_page.parent.parent
        grandchild_wiki_page.parent.destroy(grandchild_wiki_page.editors[0])
        assert grandparent.slug == "parent"
        assert grandparent.children[0] == grandchild_wiki_page
        assert grandchild_wiki_page.parent == grandparent
        assert grandchild_wiki_page.slug == "parent/grandchild"

    def test_unique_slug_element(self, grandchild_wiki_page):
        assert grandchild_wiki_page.unique_slug_element == "grandchild"
        assert grandchild_wiki_page.parent.unique_slug_element == "child"
        assert grandchild_wiki_page.parent.parent.unique_slug_element == "parent"

    def test_latest(self, revision):
        assert revision.page.latest == revision

    def test_original(self, updated_wiki_page):
        orig = updated_wiki_page.revisions.order_by("timestamp", "id").first()
        assert updated_wiki_page.original == orig

    def test_updated(self, updated_wiki_page):
        assert updated_wiki_page.updated == updated_wiki_page.latest.timestamp

    def test_created(self, updated_wiki_page):
        assert updated_wiki_page.created == updated_wiki_page.original.timestamp

    def test_created_by(self, updated_wiki_page):
        assert updated_wiki_page.created_by == updated_wiki_page.original.editor

    def test_editors(self, updated_wiki_page):
        assert len(updated_wiki_page.editors) == 2
        assert updated_wiki_page.editors[0] == updated_wiki_page.created_by
        assert updated_wiki_page.editors[1] == updated_wiki_page.revisions.all()[0].editor

    def test_children(self, child_wiki_page):
        assert len(child_wiki_page.parent.children) == 1
        assert child_wiki_page.parent.children[0] == child_wiki_page

    @pytest.mark.parametrize(
        "permission, reader_fixture, expected",
        [
            (PermissionLevel.PUBLIC, None, True),
            (PermissionLevel.PUBLIC, "other", True),
            (PermissionLevel.PUBLIC, "user", True),
            (PermissionLevel.PUBLIC, "owner", True),
            (PermissionLevel.PUBLIC, "admin", True),
            (PermissionLevel.MEMBERS_ONLY, None, False),
            (PermissionLevel.MEMBERS_ONLY, "other", True),
            (PermissionLevel.MEMBERS_ONLY, "user", True),
            (PermissionLevel.MEMBERS_ONLY, "owner", True),
            (PermissionLevel.MEMBERS_ONLY, "admin", True),
            (PermissionLevel.EDITORS_ONLY, None, False),
            (PermissionLevel.EDITORS_ONLY, "other", False),
            (PermissionLevel.EDITORS_ONLY, "user", True),
            (PermissionLevel.EDITORS_ONLY, "owner", True),
            (PermissionLevel.EDITORS_ONLY, "admin", True),
            (PermissionLevel.OWNER_ONLY, None, False),
            (PermissionLevel.OWNER_ONLY, "other", False),
            (PermissionLevel.OWNER_ONLY, "user", False),
            (PermissionLevel.OWNER_ONLY, "owner", True),
            (PermissionLevel.OWNER_ONLY, "admin", True),
            (PermissionLevel.ADMIN_ONLY, None, False),
            (PermissionLevel.ADMIN_ONLY, "other", False),
            (PermissionLevel.ADMIN_ONLY, "user", False),
            (PermissionLevel.ADMIN_ONLY, "owner", False),
            (PermissionLevel.ADMIN_ONLY, "admin", True),
        ],
    )
    def test_can_read(self, request, permission, reader_fixture, expected, user, owner):
        page = WikiPage.create(title="Test", slug="test", body="Test", editor=user, owner=owner, read=permission)
        reader = None if reader_fixture is None else request.getfixturevalue(reader_fixture)
        assert page.can_read(reader) == expected

    @pytest.mark.parametrize(
        "before, after, reader_fixture, expected",
        [
            (PermissionLevel.PUBLIC, PermissionLevel.PUBLIC, None, True),
            (PermissionLevel.PUBLIC, PermissionLevel.MEMBERS_ONLY, None, False),
            (PermissionLevel.PUBLIC, PermissionLevel.EDITORS_ONLY, None, False),
            (PermissionLevel.PUBLIC, PermissionLevel.OWNER_ONLY, None, False),
            (PermissionLevel.PUBLIC, PermissionLevel.ADMIN_ONLY, None, False),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.PUBLIC, None, False),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.MEMBERS_ONLY, None, False),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.EDITORS_ONLY, None, False),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.OWNER_ONLY, None, False),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.ADMIN_ONLY, None, False),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.PUBLIC, None, False),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.MEMBERS_ONLY, None, False),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.EDITORS_ONLY, None, False),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.OWNER_ONLY, None, False),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.ADMIN_ONLY, None, False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.PUBLIC, None, False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.MEMBERS_ONLY, None, False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.EDITORS_ONLY, None, False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.OWNER_ONLY, None, False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.ADMIN_ONLY, None, False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.PUBLIC, None, False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.MEMBERS_ONLY, None, False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.EDITORS_ONLY, None, False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.OWNER_ONLY, None, False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.ADMIN_ONLY, None, False),
            (PermissionLevel.PUBLIC, PermissionLevel.PUBLIC, "other", True),
            (PermissionLevel.PUBLIC, PermissionLevel.MEMBERS_ONLY, "other", True),
            (PermissionLevel.PUBLIC, PermissionLevel.EDITORS_ONLY, "other", False),
            (PermissionLevel.PUBLIC, PermissionLevel.OWNER_ONLY, "other", False),
            (PermissionLevel.PUBLIC, PermissionLevel.ADMIN_ONLY, "other", False),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.PUBLIC, "other", True),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.MEMBERS_ONLY, "other", True),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.EDITORS_ONLY, "other", False),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.OWNER_ONLY, "other", False),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.ADMIN_ONLY, "other", False),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.PUBLIC, "other", False),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.MEMBERS_ONLY, "other", False),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.EDITORS_ONLY, "other", False),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.OWNER_ONLY, "other", False),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.ADMIN_ONLY, "other", False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.PUBLIC, "other", False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.MEMBERS_ONLY, "other", False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.EDITORS_ONLY, "other", False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.OWNER_ONLY, "other", False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.ADMIN_ONLY, "other", False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.PUBLIC, "other", False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.MEMBERS_ONLY, "other", False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.EDITORS_ONLY, "other", False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.OWNER_ONLY, "other", False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.ADMIN_ONLY, "other", False),
            (PermissionLevel.PUBLIC, PermissionLevel.PUBLIC, "user", True),
            (PermissionLevel.PUBLIC, PermissionLevel.MEMBERS_ONLY, "user", True),
            (PermissionLevel.PUBLIC, PermissionLevel.EDITORS_ONLY, "user", True),
            (PermissionLevel.PUBLIC, PermissionLevel.OWNER_ONLY, "user", False),
            (PermissionLevel.PUBLIC, PermissionLevel.ADMIN_ONLY, "user", False),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.PUBLIC, "user", True),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.MEMBERS_ONLY, "user", True),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.EDITORS_ONLY, "user", True),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.OWNER_ONLY, "user", False),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.ADMIN_ONLY, "user", False),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.PUBLIC, "user", True),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.MEMBERS_ONLY, "user", True),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.EDITORS_ONLY, "user", True),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.OWNER_ONLY, "user", False),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.ADMIN_ONLY, "user", False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.PUBLIC, "user", False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.MEMBERS_ONLY, "user", False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.EDITORS_ONLY, "user", False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.OWNER_ONLY, "user", False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.ADMIN_ONLY, "user", False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.PUBLIC, "user", False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.MEMBERS_ONLY, "user", False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.EDITORS_ONLY, "user", False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.OWNER_ONLY, "user", False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.ADMIN_ONLY, "user", False),
            (PermissionLevel.PUBLIC, PermissionLevel.PUBLIC, "owner", True),
            (PermissionLevel.PUBLIC, PermissionLevel.MEMBERS_ONLY, "owner", True),
            (PermissionLevel.PUBLIC, PermissionLevel.EDITORS_ONLY, "owner", True),
            (PermissionLevel.PUBLIC, PermissionLevel.OWNER_ONLY, "owner", True),
            (PermissionLevel.PUBLIC, PermissionLevel.ADMIN_ONLY, "owner", False),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.PUBLIC, "owner", True),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.MEMBERS_ONLY, "owner", True),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.EDITORS_ONLY, "owner", True),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.OWNER_ONLY, "owner", True),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.ADMIN_ONLY, "owner", False),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.PUBLIC, "owner", True),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.MEMBERS_ONLY, "owner", True),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.EDITORS_ONLY, "owner", True),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.OWNER_ONLY, "owner", True),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.ADMIN_ONLY, "owner", False),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.PUBLIC, "owner", True),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.MEMBERS_ONLY, "owner", True),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.EDITORS_ONLY, "owner", True),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.OWNER_ONLY, "owner", True),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.ADMIN_ONLY, "owner", False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.PUBLIC, "owner", False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.MEMBERS_ONLY, "owner", False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.EDITORS_ONLY, "owner", False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.OWNER_ONLY, "owner", False),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.ADMIN_ONLY, "owner", False),
            (PermissionLevel.PUBLIC, PermissionLevel.PUBLIC, "admin", True),
            (PermissionLevel.PUBLIC, PermissionLevel.MEMBERS_ONLY, "admin", True),
            (PermissionLevel.PUBLIC, PermissionLevel.EDITORS_ONLY, "admin", True),
            (PermissionLevel.PUBLIC, PermissionLevel.OWNER_ONLY, "admin", True),
            (PermissionLevel.PUBLIC, PermissionLevel.ADMIN_ONLY, "admin", True),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.PUBLIC, "admin", True),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.MEMBERS_ONLY, "admin", True),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.EDITORS_ONLY, "admin", True),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.OWNER_ONLY, "admin", True),
            (PermissionLevel.MEMBERS_ONLY, PermissionLevel.ADMIN_ONLY, "admin", True),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.PUBLIC, "admin", True),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.MEMBERS_ONLY, "admin", True),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.EDITORS_ONLY, "admin", True),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.OWNER_ONLY, "admin", True),
            (PermissionLevel.EDITORS_ONLY, PermissionLevel.ADMIN_ONLY, "admin", True),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.PUBLIC, "admin", True),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.MEMBERS_ONLY, "admin", True),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.EDITORS_ONLY, "admin", True),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.OWNER_ONLY, "admin", True),
            (PermissionLevel.OWNER_ONLY, PermissionLevel.ADMIN_ONLY, "admin", True),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.PUBLIC, "admin", True),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.MEMBERS_ONLY, "admin", True),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.EDITORS_ONLY, "admin", True),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.OWNER_ONLY, "admin", True),
            (PermissionLevel.ADMIN_ONLY, PermissionLevel.ADMIN_ONLY, "admin", True),
        ],
    )
    def test_can_write(self, request, before, after, reader_fixture, expected, user, owner):
        page = WikiPage.create(title="Test", slug="test", body="Test", editor=user, owner=owner, write=before)
        reader = None if reader_fixture is None else request.getfixturevalue(reader_fixture)
        assert page.can_write(after, reader) == expected


@pytest.mark.django_db
class TestRevision:
    def test_create_read(self, revision):
        assert is_string(revision.title)
        assert is_string(revision.slug)
        assert is_string(revision.body)
        assert revision.read == PermissionLevel.PUBLIC.value
        assert revision.write == PermissionLevel.PUBLIC.value

    def test_create_with_owner(self, owned_wiki_page):
        assert isinstance(owned_wiki_page.owner, User)

    def test_str(self, revision):
        assert str(revision) == revision.slug

    def test_unique_slug(self, wiki_page):
        with pytest.raises(IntegrityError):
            WikiPage.create(title="Test Page", slug=wiki_page.slug, body="Test", editor=wiki_page.created_by)

    def test_unique_slug_does_not_stop_update(self, wiki_page):
        updated_title = "Updated Title"
        slug = wiki_page.slug
        wiki_page.patch(title=updated_title, editor=wiki_page.created_by, message="Update title.")
        assert wiki_page.title == updated_title
        assert wiki_page.slug == slug

    def test_set_slug_default(self, revision):
        revision.title = "Test Page"
        revision.slug = ""
        revision.set_slug()
        assert revision.slug == "test-page"

    def test_set_slug_param(self, revision):
        revision.title = "Test Page"
        revision.slug = ""
        revision.set_slug("test")
        assert revision.slug == "test"

    def test_set_slug_slugify(self, revision):
        revision.title = "Test Page"
        revision.slug = ""
        revision.set_slug("Test Page Title")
        assert revision.slug == "test-page-title"

    def test_set_slug_child(self, child_wiki_page):
        rev = child_wiki_page.latest
        rev.title = "Child Page"
        rev.slug = ""
        rev.set_slug("Child Page")
        assert rev.slug == f"{child_wiki_page.parent.slug}/child-page"


@pytest.mark.django_db
class TestSecretCategory:
    def test_create_read(self, secret_category):
        assert isinstance(secret_category, SecretCategory)
        assert is_string(secret_category.name)
        assert is_string(secret_category.parent.name)
        assert secret_category.children.count() == 1
        assert is_string(secret_category.children.first().name)

    def test_str(self, secret_category):
        assert str(secret_category) == secret_category.name


@pytest.mark.django_db
class TestSecret:
    def test_create_read(self, secret):
        assert isinstance(secret, Secret)
        assert is_string(secret.key)
        assert is_string(secret.description)
        assert secret.categories.count() == 1
        assert is_string(secret.categories.first().name)
        assert secret.known_to.count() == 1
        assert isinstance(secret.known_to.first(), WikiPage)
        assert secret.known_to.first().page_type == PageType.CHARACTER

    def test_str(self, secret):
        assert str(secret) == secret.key

    def test_knows(self, secret, character):
        fool = WikiPage.create(
            page_type=PageType.CHARACTER,
            title="Jon Snow",
            slug="jon-snow",
            body="Knows nothing.",
            editor=character.created_by,
            owner=character.created_by,
        )
        assert secret.knows(character)
        assert not secret.knows(fool)
