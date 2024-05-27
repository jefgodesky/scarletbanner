import pytest

from wiki.enums import PageType, PermissionLevel
from wiki.tests.factories import CharacterFactory, SecretCategoryFactory, SecretFactory, WikiPageFactory


@pytest.fixture
def wiki_page(user):
    return WikiPageFactory(editor=user)


@pytest.fixture
def parent_wiki_page(user):
    return WikiPageFactory(slug="parent", editor=user)


@pytest.fixture
def child_wiki_page(parent_wiki_page):
    return WikiPageFactory(parent=parent_wiki_page, slug="child", editor=parent_wiki_page.created_by)


@pytest.fixture
def grandchild_wiki_page(child_wiki_page):
    return WikiPageFactory(parent=child_wiki_page, slug="grandchild", editor=child_wiki_page.created_by)


@pytest.fixture
def owned_wiki_page(user, owner):
    return WikiPageFactory(editor=user, owner=owner)


@pytest.fixture
def updated_wiki_page(wiki_page, user, other):
    page = wiki_page
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
    return page


@pytest.fixture
def character(user):
    return CharacterFactory(editor=user, owner=user)


@pytest.fixture
def revision(wiki_page, user):
    return wiki_page.original


@pytest.fixture
def secret_category():
    parent = SecretCategoryFactory(name="Parent Category")
    category = SecretCategoryFactory(parent=parent)
    SecretCategoryFactory(name="Child Category", parent=category)
    return category


@pytest.fixture
def secret(character, secret_category):
    return SecretFactory(categories=[secret_category], known_to=[character])
