import pytest

from scarletbanner.wiki.tests.factories import PageFactory


@pytest.fixture
def page():
    return PageFactory()
