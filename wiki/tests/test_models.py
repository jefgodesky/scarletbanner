import pytest
from wiki.models import WikiPage


@pytest.mark.django_db
class TestWikiPage:
    def test_create_read(self, wiki_page):
        actual = WikiPage.objects.get(id=wiki_page.id)
        assert actual.title == "Test Page"

    def test_str(self, wiki_page):
        assert str(wiki_page) == "Test Page"

    def test_update(self, wiki_page):
        updated_title = "Updated Test Page"
        wiki_page.title = updated_title
        wiki_page.save()
        updated_page = WikiPage.objects.get(id=wiki_page.id)
        assert updated_page.title == updated_title

    def test_delete(self, wiki_page):
        wiki_page_id = wiki_page.id
        wiki_page.delete()
        with pytest.raises(WikiPage.DoesNotExist):
            WikiPage.objects.get(id=wiki_page_id)
