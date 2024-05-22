import pytest

from wiki.models import WikiPage
from wiki.permission_levels import PermissionLevel


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
def owned_wiki_page(user, owner):
    title = "Owned Page"
    body = "This is an owned page."
    return (
        WikiPage.create(
            title=title,
            body=body,
            editor=user,
            owner=owner,
        ),
        title,
        body,
        user,
        owner,
    )


@pytest.fixture
def public_read_page(user, owner):
    return (
        WikiPage.create(
            title="Public Page",
            body="This is a publicly-readable page.",
            editor=user,
            owner=owner,
        ),
        user,
        owner,
    )


@pytest.fixture
def members_read_page(user, owner):
    return (
        WikiPage.create(
            title="Public Page",
            body="This is a publicly-readable page.",
            editor=user,
            owner=owner,
            read=PermissionLevel.MEMBERS_ONLY,
        ),
        user,
        owner,
    )


@pytest.fixture
def updated_wiki_page(wiki_page, user, other):
    page, _, _, _ = wiki_page
    updated_title = "Updated Test Page"
    updated_body = "This is the updated body."
    page.update(
        title=updated_title, body=updated_body, editor=other, read=PermissionLevel.PUBLIC, write=PermissionLevel.PUBLIC
    )
    return page, updated_title, updated_body, other


@pytest.fixture
def updated_owned_wiki_page(owned_wiki_page):
    page, _, _, editor, owner = owned_wiki_page
    updated_title = "Updated Owned Test Page"
    updated_body = "This is the updated body."
    page.update(
        title=updated_title,
        body=updated_body,
        editor=editor,
        owner=editor,
        read=PermissionLevel.PUBLIC,
        write=PermissionLevel.PUBLIC,
    )
    return page, updated_title, updated_body, editor


@pytest.fixture
def revision(wiki_page, user):
    page, _, _, _ = wiki_page
    return page.original
