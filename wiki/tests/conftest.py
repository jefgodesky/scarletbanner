import pytest
from wiki.models import WikiPage


@pytest.fixture
def wiki_page():
    return WikiPage.objects.create(title="Test Page")
