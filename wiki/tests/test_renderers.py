import pytest

from wiki.renderers import render_secrets
from wiki.tests.factories import SecretFactory


@pytest.mark.django_db
class TestRenderSecrets:
    def test_no_secrets(self, character):
        before = "Hello, world!"
        assert render_secrets(before, character) == before

    def test_hide_unknown_secret(self, character):
        SecretFactory(key="Test Secret")
        before = 'This comes before. <secret show="[Test Secret]">This is secret!</secret> This comes after.'
        assert render_secrets(before, character) == "This comes before. This comes after."

    def test_show_known_secret(self, character):
        secret = SecretFactory(key="Test Secret")
        secret.known_to.set([character])
        before = 'This comes before. <secret show="[Test Secret]">This is secret!</secret> This comes after.'
        assert render_secrets(before, character) == "This comes before. This is secret! This comes after."

    def test_nested_secrets_outer(self, character):
        s1 = SecretFactory(key="S1")
        SecretFactory(key="S2")
        s1.known_to.set([character])
        before = '<secret show="[S1]">before <secret show="[S2]">inner</secret> after</secret>'
        after = "before after"
        assert render_secrets(before, character) == after

    def test_nested_secrets_both(self, character):
        s1 = SecretFactory(key="S1")
        s2 = SecretFactory(key="S2")
        s1.known_to.set([character])
        s2.known_to.set([character])
        before = '<secret show="[S1]">before <secret show="[S2]">inner</secret> after</secret>'
        after = "before inner after"
        assert render_secrets(before, character) == after

    def test_editable(self, character):
        s1 = SecretFactory(key="S1")
        s1.known_to.set([character])
        SecretFactory(key="S2")
        before = 'Public <secret show="[S1]">known</secret> <secret show="[S2]">not known</secret>'
        expected = 'Public <secret show="[S1]" sid="1">known</secret> <secret sid="2"></secret>'
        print(render_secrets(before, character, editable=True))
        assert render_secrets(before, character, editable=True) == expected
