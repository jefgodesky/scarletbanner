import pytest
from wiki.models import WikiPage, Revision


@pytest.mark.django_db
class TestWikiPage:
    def test_create_read(self, wiki_page):
        page, title, _ = wiki_page
        actual = WikiPage.objects.get(id=page.id)
        assert actual.title == title

    def test_str(self, wiki_page):
        page, title, _ = wiki_page
        assert str(page) == title

    def test_update(self, updated_wiki_page):
        page, title, _ = updated_wiki_page
        assert page.title == title

    def test_delete(self, wiki_page):
        page, _, _ = wiki_page
        wiki_page_id = page.id
        page.delete()
        with pytest.raises(WikiPage.DoesNotExist):
            WikiPage.objects.get(id=wiki_page_id)
            Revision.objects.get(wiki_page=wiki_page_id)

    def test_latest(self, revision):
        page = revision.page
        assert page.latest == revision

    def test_original(self, updated_wiki_page):
        page, _, _ = updated_wiki_page
        orig = page.revisions.order_by('timestamp', 'id').first()
        assert page.original == orig

    def test_updated(self, updated_wiki_page):
        page, _, _ = updated_wiki_page
        assert page.updated == page.latest.timestamp

    def test_created(self, updated_wiki_page):
        page, _, _ = updated_wiki_page
        assert page.created == page.original.timestamp

    def test_created_by(self, updated_wiki_page):
        page, _, _ = updated_wiki_page
        assert page.created_by == page.original.editor

    def test_editors(self, updated_wiki_page):
        page, _, second = updated_wiki_page
        expected = [page.created_by, second]
        assert page.editors == expected


@pytest.mark.django_db
class TestRevision:
    def test_create_read(self, revision):
        actual = Revision.objects.get(id=revision.id)
        assert actual.title == "Test Page"
        assert actual.body == "This is a test."

    def test_str(self, revision):
        assert str(revision) == "Test Page"
