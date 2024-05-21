import pytest
from wiki.models import WikiPage, Revision


@pytest.fixture
def wiki_page():
    return WikiPage.objects.create(title="Test Page")


@pytest.fixture
def revision(wiki_page):
    return Revision.objects.create(title="Test Page", page=wiki_page)
