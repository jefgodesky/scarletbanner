import pytest

from wiki.models import Revision, WikiPage
from wiki.permission_levels import PermissionLevel


@pytest.mark.django_db
class TestWikiPage:
    def test_create_read(self, wiki_page):
        page, title, body, _ = wiki_page
        actual = WikiPage.objects.get(id=page.id)
        assert actual.title == title
        assert actual.body == body
        assert actual.owner is None
        assert actual.read == PermissionLevel.PUBLIC.value
        assert actual.write == PermissionLevel.PUBLIC.value

    def test_str(self, wiki_page):
        page, title, _, _ = wiki_page
        assert str(page) == title

    def test_update(self, updated_wiki_page):
        page, title, body, _ = updated_wiki_page
        assert page.title == title
        assert page.body == body
        assert page.owner is None
        assert page.read == PermissionLevel.PUBLIC.value
        assert page.write == PermissionLevel.PUBLIC.value

    def test_patch(self, wiki_page):
        page, title, body, editor = wiki_page
        updated_title = "Updated Title"
        page.patch(editor, title=updated_title)
        assert page.title == updated_title
        assert page.body == body

    def test_delete(self, wiki_page):
        page, _, _, _ = wiki_page
        wiki_page_id = page.id
        page.delete()
        with pytest.raises(WikiPage.DoesNotExist):
            WikiPage.objects.get(id=wiki_page_id)
            Revision.objects.get(wiki_page=wiki_page_id)

    def test_latest(self, revision):
        page = revision.page
        assert page.latest == revision

    def test_original(self, updated_wiki_page):
        page, _, _, _ = updated_wiki_page
        orig = page.revisions.order_by("timestamp", "id").first()
        assert page.original == orig

    def test_updated(self, updated_wiki_page):
        page, _, _, _ = updated_wiki_page
        assert page.updated == page.latest.timestamp

    def test_updated_owned(self, updated_owned_wiki_page):
        page, _, _, user = updated_owned_wiki_page
        assert page.owner == user

    def test_created(self, updated_wiki_page):
        page, _, _, _ = updated_wiki_page
        assert page.created == page.original.timestamp

    def test_created_by(self, updated_wiki_page):
        page, _, _, _ = updated_wiki_page
        assert page.created_by == page.original.editor

    def test_editors(self, updated_wiki_page):
        page, _, _, editor = updated_wiki_page
        expected = [page.created_by, editor]
        assert page.editors == expected


@pytest.mark.django_db
class TestRevision:
    def test_create_read(self, revision):
        actual = Revision.objects.get(id=revision.id)
        assert actual.title == "Test Page"
        assert actual.body == "This is the original body."
        assert actual.owner is None
        assert actual.read == PermissionLevel.PUBLIC.value
        assert actual.write == PermissionLevel.PUBLIC.value

    def test_create_with_owner(self, owned_wiki_page):
        page, _, _, _, owner = owned_wiki_page
        assert page.original.owner == owner

    def test_str(self, revision):
        assert str(revision) == "Test Page"
