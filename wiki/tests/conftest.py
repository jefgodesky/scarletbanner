import pytest

from wiki.enums import PageType, PermissionLevel
from wiki.models import SecretCategory, WikiPage


@pytest.fixture
def wiki_page(user):
    title = "Test Page"
    slug = "test"
    body = "This is the original body."
    page = WikiPage.create(title=title, slug=slug, body=body, editor=user)
    return page, title, slug, body, user


@pytest.fixture
def child_wiki_page(wiki_page):
    page, _, slug, _, editor = wiki_page
    title = "Child Page"
    slug = "child"
    body = "This is a child page."
    child = WikiPage.create(title=title, slug=slug, body=body, editor=editor, parent=page)
    return child


@pytest.fixture
def grandchild_wiki_page(child_wiki_page):
    title = "Grandchild Page"
    slug = "grandchild"
    body = "This is a grandchild page."
    grandchild = WikiPage.create(
        title=title, slug=slug, body=body, editor=child_wiki_page.editors[0], parent=child_wiki_page
    )
    return grandchild


@pytest.fixture
def owned_wiki_page(user, owner):
    title = "Owned Page"
    slug = "owned"
    body = "This is an owned page."
    page = WikiPage.create(title=title, slug=slug, body=body, editor=user, owner=owner)
    return page, title, slug, body, user, owner


@pytest.fixture
def updated_wiki_page(wiki_page, user, other):
    page, _, _, _, _ = wiki_page
    updated_title = "Updated Test Page"
    updated_slug = "updated"
    updated_body = "This is the updated body."
    page.update(
        page_type=PageType.PAGE,
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
        page_type=PageType.PAGE,
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
def character(user):
    title = "John Doe"
    slug = "john-doe"
    body = "This is a character page."
    page = WikiPage.create(page_type=PageType.CHARACTER, title=title, slug=slug, body=body, editor=user, owner=user)
    return page, user


@pytest.fixture
def revision(wiki_page, user):
    page, _, _, _, _ = wiki_page
    return page.original


@pytest.fixture
def secret_category():
    parent = SecretCategory.objects.create(name="Parent Category")
    category = SecretCategory.objects.create(name="Secret Category", parent=parent)
    SecretCategory.objects.create(name="Child Category", parent=category)
    return category
