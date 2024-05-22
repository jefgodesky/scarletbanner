import pytest

from wiki.models import Revision, WikiPage


@pytest.fixture
def wiki_page(user):
    title = "Test Page"
    body = "This is the original body."
    return (
        WikiPage.create(
            title=title,
            body=body,
            editor=user,
        ),
        title,
        body,
        user,
    )


@pytest.fixture
def updated_wiki_page(wiki_page, user, other):
    page, _, _, _ = wiki_page
    updated_title = "Updated Test Page"
    updated_body = "This is the updated body."
    page.update(title=updated_title, body=updated_body, editor=other)
    return page, updated_title, updated_body, other


@pytest.fixture
def revision(wiki_page, user):
    page, _, _, _ = wiki_page
    return Revision.objects.create(
        title="Test Page",
        body="This is a test.",
        editor=user,
        page=page,
    )
