import pytest
from wiki.models import WikiPage, Revision


@pytest.fixture
def wiki_page():
    return WikiPage.create("Test Page")


@pytest.fixture
def revision(wiki_page):
    return Revision.objects.create(title="Test Page", page=wiki_page)
