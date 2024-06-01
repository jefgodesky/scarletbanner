import pytest

from scarletbanner.wiki.tests.factories import make_page


@pytest.fixture
def page(user):
    return make_page(user=user)
