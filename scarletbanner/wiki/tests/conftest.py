import pytest

from scarletbanner.wiki.enums import PermissionLevel
from scarletbanner.wiki.tests.factories import (
    SecretCategoryFactory,
    SecretFactory,
    make_character,
    make_file,
    make_image,
    make_owned_page,
    make_page,
    make_template,
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
def list_pages(user, admin):
    return [
        make_page(title="Public", read=PermissionLevel.PUBLIC, user=user),
        make_page(title="Members Only", read=PermissionLevel.MEMBERS_ONLY, user=user),
        make_page(title="Editors Only", read=PermissionLevel.EDITORS_ONLY, user=user),
        make_page(title="Admin Only", read=PermissionLevel.ADMIN_ONLY, user=user),
    ].reverse()


@pytest.fixture
def character(user):
    return make_character(user=user)


@pytest.fixture
def template(user):
    return make_template(user=user)


@pytest.fixture
def file(user):
    return make_file(user=user)


@pytest.fixture
def jpeg(user):
    return make_image(user=user, file_format="JPEG")


@pytest.fixture
def gif(user):
    return make_image(user=user, file_format="GIF")


@pytest.fixture
def png(user):
    return make_image(user=user, file_format="PNG")


@pytest.fixture
def secret_category():
    parent = SecretCategoryFactory(name="Parent Category")
    category = SecretCategoryFactory(parent=parent)
    SecretCategoryFactory(name="Child Category", parent=category)
    return category


@pytest.fixture
def secret(character, secret_category):
    return SecretFactory(categories=[secret_category], known_to=[character])
