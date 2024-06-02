import pytest

from scarletbanner.wiki.renderers import reconcile_secrets, render_secrets, render_template_pages, render_templates
from scarletbanner.wiki.tests.factories import SecretFactory, make_template


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


class TestReconcileSecrets:
    def test_reconciliation(self):
        original = (
            'before <secret show="[S1]" sid="1">first '
            '<secret show="[S2]" sid="2">inner</secret></secret>'
            'middle <secret show="[S3]" sid="3">last</secret> after'
        )
        edited = (
            'one <secret show="[S1]" sid="1">updated <secret sid="2">'
            '</secret></secret> <secret show="[S4]">new</secret> two '
            '<secret sid="3"></secret>'
        )
        expected = (
            'one <secret show="[S1]">updated <secret '
            'show="[S2]">inner</secret></secret> <secret '
            'show="[S4]">new</secret> two '
            '<secret show="[S3]">last</secret>'
        )
        assert reconcile_secrets(original, edited) == expected


@pytest.mark.django_db
class TestRenderTemplates:
    def test_no_templates(self):
        before = "Hello, world!"
        assert render_templates(before) == before

    def test_simple_template(self):
        make_template(title="Test Template", body="Hello, world!")
        before = '<template name="Test Template"></template>'
        assert render_templates(before) == "Hello, world!"

    def test_with_params(self):
        make_template(title="Test Template", body="{{ text }}")
        before = '<template name="Test Template" text="Hello, world!"></template>'
        assert render_templates(before) == "Hello, world!"

    def test_with_params_edge_cases(self):
        body = "{{ text }} {{text}} {{text }} {{ text}}"
        make_template(title="Test Template", body=body)
        before = '<template name="Test Template" text="X"></template>'
        assert render_templates(before) == "X X X X"

    def test_body(self):
        make_template(title="Test Template", body="{{ body }}")
        before = '<template name="Test Template">Hello, world!</template>'
        assert render_templates(before) == "Hello, world!"

    def test_no_include(self):
        body = "Hello, world! <noinclude>X</noinclude>"
        make_template(title="Test Template", body=body)
        before = '<template name="Test Template"></template>'
        assert render_templates(before) == "Hello, world!"

    def test_include_only(self):
        body = "<includeonly>Hello, world!</includeonly> <noinclude>X</noinclude>"
        make_template(title="Test Template", body=body)
        before = '<template name="Test Template"></template>'
        assert render_templates(before) == "Hello, world!"

    def test_nested_template(self):
        make_template(title="Inner Template", body="Hello, world!")
        make_template(title="Outer Template", body='<template name="Inner Template"></template>')
        before = '<template name="Outer Template"></template>'
        assert render_templates(before) == "Hello, world!"


class TestRenderTemplatePage:
    def test_no_tags(self):
        before = "Hello, world!"
        assert render_template_pages(before) == before

    def test_no_include(self):
        before = "Hello, world! <noinclude>X</noinclude>"
        assert render_template_pages(before) == "Hello, world! X"

    def test_include_only(self):
        before = "<includeonly>Hello, world!</includeonly> <noinclude>X</noinclude>"
        assert render_template_pages(before) == "X"
