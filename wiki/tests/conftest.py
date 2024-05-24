import pytest

from wiki.models import WikiPage
from wiki.permission_levels import PermissionLevel


@pytest.fixture
def wiki_page(user):
    title = "Test Page"
    slug = "test"
    body = "This is the original body."
    return (
        WikiPage.create(
            title=title,
            slug=slug,
            body=body,
            editor=user,
        ),
        title,
        slug,
        body,
        user,
    )


@pytest.fixture
def child_wiki_page(wiki_page):
    page, _, slug, _, editor = wiki_page
    title = "Child Page"
    slug = "child"
    body = "This is a child page."
    return WikiPage.create(title=title, slug=slug, body=body, editor=editor, parent=page)


@pytest.fixture
def owned_wiki_page(user, owner):
    title = "Owned Page"
    slug = "owned"
    body = "This is an owned page."
    return (
        WikiPage.create(
            title=title,
            slug=slug,
            body=body,
            editor=user,
            owner=owner,
        ),
        title,
        slug,
        body,
        user,
        owner,
    )


@pytest.fixture
def updated_wiki_page(wiki_page, user, other):
    page, _, _, _, _ = wiki_page
    updated_title = "Updated Test Page"
    updated_slug = "updated"
    updated_body = "This is the updated body."
    page.update(
        title=updated_title,
        slug=updated_slug,
        body=updated_body,
        editor=other,
        message="Test update",
        read=PermissionLevel.PUBLIC,
        write=PermissionLevel.PUBLIC,
    )
    return page, updated_title, updated_slug, updated_body, other


@pytest.fixture
def updated_owned_wiki_page(owned_wiki_page):
    page, _, _, _, editor, owner = owned_wiki_page
    updated_title = "Updated Owned Test Page"
    updated_slug = "updated-owned"
    updated_body = "This is the updated body."
    page.update(
        title=updated_title,
        slug=updated_slug,
        body=updated_body,
        editor=editor,
        owner=editor,
        message="Test update",
        read=PermissionLevel.PUBLIC,
        write=PermissionLevel.PUBLIC,
    )
    return page, updated_title, updated_slug, updated_body, editor


@pytest.fixture
def revision(wiki_page, user):
    page, _, _, _, _ = wiki_page
    return page.original
