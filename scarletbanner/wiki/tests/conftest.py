import pytest

from scarletbanner.wiki.tests.factories import (
    SecretCategoryFactory,
    SecretFactory,
    make_character,
    make_owned_page,
    make_page,
)


@pytest.fixture
def page(user):
    return make_page(user=user)


@pytest.fixture
def child_page(user):
    parent = make_page(user=user, title="Parent Page", slug="parent")
    return make_page(user=user, title="Child Page", slug="child", parent=parent)


@pytest.fixture
def grandchild_page(child_page):
    return make_page(user=child_page.editors[0], title="Grandchild Page", slug="grandchild", parent=child_page)


@pytest.fixture
def owned_page(user, owner):
    return make_owned_page(user=user, owner=owner)


@pytest.fixture
def character(user):
    return make_character(user=user)


@pytest.fixture
def secret_category():
    parent = SecretCategoryFactory(name="Parent Category")
    category = SecretCategoryFactory(parent=parent)
    SecretCategoryFactory(name="Child Category", parent=category)
    return category


@pytest.fixture
def secret(character, secret_category):
    return SecretFactory(categories=[secret_category], known_to=[character])
