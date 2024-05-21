import pytest
from wiki.models import WikiPage, Revision


@pytest.mark.django_db
class TestWikiPage:
    def test_create_read(self, wiki_page):
        actual = WikiPage.objects.get(id=wiki_page.id)
        assert actual.title == "Test Page"

    def test_str(self, wiki_page):
        assert str(wiki_page) == "Test Page"

    def test_update(self, wiki_page):
        updated_title = "Updated Test Page"
        wiki_page.update(title=updated_title)
        updated_page = WikiPage.objects.get(id=wiki_page.id)
        assert updated_page.title == updated_title

    def test_delete(self, wiki_page):
        wiki_page_id = wiki_page.id
        wiki_page.delete()
        with pytest.raises(WikiPage.DoesNotExist):
            WikiPage.objects.get(id=wiki_page_id)
            Revision.objects.get(wiki_page=wiki_page_id)

    def test_latest(self, revision):
        page = revision.page
        assert page.latest.id == revision.id

    def test_latest_title(self, wiki_page):
        updated_title = "Updated Test Page"
        wiki_page.update(title=updated_title)
        actual = WikiPage.objects.get(id=wiki_page.id)
        assert actual.title == updated_title


@pytest.mark.django_db
class TestRevision:
    def test_create_read(self, revision):
        actual = Revision.objects.get(id=revision.id)
        assert actual.title == "Test Page"

    def test_str(self, revision):
        assert str(revision) == "Test Page"
