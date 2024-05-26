import pytest
from django.db.utils import IntegrityError

from wiki.enums import PageType, PermissionLevel
from wiki.models import Revision, Secret, SecretCategory, WikiPage


@pytest.mark.django_db
class TestWikiPage:
    def test_create_read(self, wiki_page):
        page, title, slug, body, _ = wiki_page
        actual = WikiPage.objects.get(id=page.id)
        assert actual.title == title
        assert actual.slug == slug
        assert actual.body == body
        assert actual.owner is None
        assert actual.read == PermissionLevel.PUBLIC
        assert actual.write == PermissionLevel.PUBLIC

    def test_create_read_character(self, character):
        page, player = character
        actual = WikiPage.objects.get(id=page.id)
        assert actual.title == page.title
        assert actual.slug == page.slug
        assert actual.page_type == PageType.CHARACTER
        assert actual.owner == player

    def test_create_child(self, child_wiki_page):
        assert isinstance(child_wiki_page.parent, WikiPage)

    def test_str(self, wiki_page):
        page, title, _, _, _ = wiki_page
        assert str(page) == title

    def test_get_type(self, character, other):
        page, player = character
        all_characters = WikiPage.get_type(PageType.CHARACTER)
        player_characters = WikiPage.get_type(PageType.CHARACTER, owner=player)
        other_characters = WikiPage.get_type(PageType.CHARACTER, owner=other)
        assert len(all_characters) == 1
        assert len(player_characters) == 1
        assert len(other_characters) == 0
        assert all_characters[0] == page
        assert player_characters[0] == page

    def test_update(self, updated_wiki_page):
        page, title, slug, body, _ = updated_wiki_page
        assert page.title == title
        assert page.body == body
        assert page.slug == slug
        assert page.owner is None
        assert page.parent is None
        assert page.read == PermissionLevel.PUBLIC
        assert page.write == PermissionLevel.PUBLIC

    def test_update_type(self, wiki_page):
        page, _, _, _, user = wiki_page
        page.update(
            page_type=PageType.CHARACTER,
            title=page.title,
            slug=page.slug,
            body=page.body,
            editor=user,
            message="Update page type",
            read=PermissionLevel.PUBLIC,
            write=PermissionLevel.PUBLIC,
        )
        assert page.page_type == PageType.CHARACTER

    def test_update_child(self, wiki_page):
        page, _, _, _, editor = wiki_page
        parent = WikiPage.create(
            page_type=PageType.PAGE,
            title="Parent",
            slug="parent",
            body="This is the parent page.",
            read=PermissionLevel.PUBLIC,
            write=PermissionLevel.PUBLIC,
            editor=editor,
        )
        page.patch(slug="parent/test", parent=parent, editor=editor, message="Patching test")
        assert page.parent == parent

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
        page, title, _, body, editor = wiki_page
        updated_title = "Updated Title"
        updated_slug = "updated"
        page.patch(editor, message="Patching test", title=updated_title, slug=updated_slug)
        assert page.title == updated_title
        assert page.body == body

    def test_patch_type(self, wiki_page):
        page, _, _, _, user = wiki_page
        page.patch(
            page_type=PageType.CHARACTER,
            editor=user,
            message="Update page type",
        )
        assert page.page_type == PageType.CHARACTER

    def test_destroy(self, wiki_page):
        page, _, _, _, editor = wiki_page
        wiki_page_id = page.id
        page.destroy(editor)
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
        assert grandparent.slug == "test"
        assert grandparent.children[0] == grandchild_wiki_page
        assert grandchild_wiki_page.parent == grandparent
        assert grandchild_wiki_page.slug == "test/grandchild"

    def test_unique_slug_element(self, grandchild_wiki_page):
        assert grandchild_wiki_page.unique_slug_element == "grandchild"
        assert grandchild_wiki_page.parent.unique_slug_element == "child"
        assert grandchild_wiki_page.parent.parent.unique_slug_element == "test"

    def test_latest(self, revision):
        page = revision.page
        assert page.latest == revision

    def test_original(self, updated_wiki_page):
        page, _, _, _, _ = updated_wiki_page
        orig = page.revisions.order_by("timestamp", "id").first()
        assert page.original == orig

    def test_updated(self, updated_wiki_page):
        page, _, _, _, _ = updated_wiki_page
        assert page.updated == page.latest.timestamp

    def test_updated_owned(self, updated_owned_wiki_page):
        page, _, _, _, user = updated_owned_wiki_page
        assert page.owner == user

    def test_created(self, updated_wiki_page):
        page, _, _, _, _ = updated_wiki_page
        assert page.created == page.original.timestamp

    def test_created_by(self, updated_wiki_page):
        page, _, _, _, _ = updated_wiki_page
        assert page.created_by == page.original.editor

    def test_editors(self, updated_wiki_page):
        page, _, _, _, editor = updated_wiki_page
        assert len(page.editors) == 2
        assert page.editors[0] == page.created_by
        assert page.editors[1] == editor

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
        actual = Revision.objects.get(id=revision.id)
        assert actual.title == "Test Page"
        assert actual.slug == "test"
        assert actual.body == "This is the original body."
        assert actual.message == "Initial text"
        assert actual.owner is None
        assert actual.parent is None
        assert actual.read == PermissionLevel.PUBLIC.value
        assert actual.write == PermissionLevel.PUBLIC.value

    def test_create_with_owner(self, owned_wiki_page):
        page, _, _, _, _, owner = owned_wiki_page
        assert page.original.owner == owner

    def test_str(self, revision):
        assert str(revision) == "test"

    def test_unique_slug(self, wiki_page):
        page, _, _, _, editor = wiki_page
        with pytest.raises(IntegrityError):
            WikiPage.create(title="Test Page", slug=page.slug, body="Test", editor=editor)

    def test_unique_slug_does_not_stop_update(self, wiki_page):
        page, _, _, _, editor = wiki_page
        page.patch(title="Updated Title", editor=editor, message="Update title.")
        assert page.title == "Updated Title"
        assert page.slug == "test"

    def test_set_slug_default(self, revision):
        revision.slug = ""
        revision.set_slug()
        assert revision.slug == "test-page"

    def test_set_slug_param(self, revision):
        revision.slug = ""
        revision.set_slug("test")
        assert revision.slug == "test"

    def test_set_slug_slugify(self, revision):
        revision.slug = ""
        revision.set_slug("Test Page")
        assert revision.slug == "test-page"

    def test_set_slug_child(self, child_wiki_page):
        rev = child_wiki_page.latest
        rev.slug = ""
        rev.set_slug("Child Page")
        assert rev.slug == "test/child-page"


@pytest.mark.django_db
class TestSecretCategory:
    def test_create_read(self, secret_category):
        assert isinstance(secret_category, SecretCategory)
        assert secret_category.name == "Secret Category"
        assert secret_category.parent.name == "Parent Category"
        assert secret_category.children.count() == 1
        assert secret_category.children.first().name == "Child Category"

    def test_str(self, secret_category):
        assert str(secret_category) == "Secret Category"


@pytest.mark.django_db
class TestSecret:
    def test_create_read(self, secret):
        assert isinstance(secret, Secret)
        assert secret.key == "Test Secret"
        assert secret.description == "This is a test secret."
        assert secret.categories.count() == 1
        assert secret.categories.first().name == "Secret Category"
        assert secret.known_to.count() == 1
        assert isinstance(secret.known_to.first(), WikiPage)
        assert secret.known_to.first().page_type == PageType.CHARACTER

    def test_str(self, secret):
        assert str(secret) == "Test Secret"

    def test_knows(self, secret, character):
        sage, player = character
        fool = WikiPage.create(
            page_type=PageType.CHARACTER,
            title="Jon Snow",
            slug="jon-snow",
            body="Knows nothing.",
            editor=player,
            owner=player,
        )
        assert secret.knows(sage)
        assert not secret.knows(fool)
