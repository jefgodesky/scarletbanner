import pytest

from wiki.models import WikiPage


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
def owned_wiki_page(user, other):
    title = "Owned Page"
    body = "This is an owned page."
    return (
        WikiPage.create(
            title=title,
            body=body,
            editor=user,
            owner=other,
        ),
        title,
        body,
        user,
        other,
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
    return page.original
