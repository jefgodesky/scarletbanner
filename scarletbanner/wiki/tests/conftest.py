import pytest

from scarletbanner.wiki.tests.factories import make_page


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
