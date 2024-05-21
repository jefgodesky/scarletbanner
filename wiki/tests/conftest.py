import pytest
from wiki.models import WikiPage, Revision


@pytest.fixture
def wiki_page(user):
    title = "Test Page"
    return WikiPage.create(title=title, editor=user), title, user


@pytest.fixture
def updated_wiki_page(wiki_page, user, other):
    page, _, _ = wiki_page
    updated_title = "Updated Test Page"
    page.update(title=updated_title, editor=other)
    return page, updated_title, other


@pytest.fixture
def revision(wiki_page, user):
    page, _, _ = wiki_page
    return Revision.objects.create(
        title="Test Page",
        body="This is a test.",
        editor=user,
        page=page
    )
