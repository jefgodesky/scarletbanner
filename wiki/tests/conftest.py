import pytest
from wiki.models import WikiPage, Revision


@pytest.fixture
def wiki_page():
    title = "Test Page"
    return WikiPage.create(title), title


@pytest.fixture
def updated_wiki_page(wiki_page):
    page, _ = wiki_page
    updated_title = "Updated Test Page"
    page.update(updated_title)
    return page, updated_title


@pytest.fixture
def revision(wiki_page):
    page, _ = wiki_page
    return Revision.objects.create(title="Test Page", page=page)
