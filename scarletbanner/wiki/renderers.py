import re
from urllib.parse import quote_plus, urlencode

import bleach
import markdown
from bs4 import BeautifulSoup
from django.db.models import Q
from django.urls import reverse

from scarletbanner.wiki.enums import PageType
from scarletbanner.wiki.models import Revision, Secret, WikiPage


def render_secrets(original: str, character: WikiPage, editable: bool = False) -> str:
    soup = BeautifulSoup(original, "html.parser")
    all_secrets = Secret.objects.all()
    sid = 0

    def process_secrets(parent):
        nonlocal sid, all_secrets
        secrets = parent.find_all("secret", recursive=False)
        for tag in secrets:
            expression = tag.get("show")
            sid += 1
            if expression:
                try:
                    if Secret.evaluate(expression, character, all_secrets):
                        process_secrets(tag)
                        if editable:
                            tag["sid"] = sid
                        else:
                            tag.unwrap()
                    else:
                        if editable:
                            new_tag = soup.new_tag("secret", sid=str(sid))
                            tag.replace_with(new_tag)
                        else:
                            tag.decompose()
                except Secret.DoesNotExist:
                    tag.decompose()

    process_secrets(soup)
    return re.sub(r" {2,}", " ", str(soup).strip())


def reconcile_secrets(original: str, edited: str) -> str:
    original_soup = BeautifulSoup(original, "html.parser")
    edited_soup = BeautifulSoup(edited, "html.parser")

    secrets = {tag.get("sid"): tag for tag in original_soup.find_all("secret", recursive=True)}

    def process_secrets(parent):
        for tag in parent.find_all("secret", recursive=False):
            sid = tag.get("sid")
            if sid and not tag.has_attr("show"):
                original_secret = secrets.get(sid)
                if original_secret:
                    tag.replace_with(original_secret)
            process_secrets(tag)

    process_secrets(edited_soup)

    for tag in edited_soup.find_all("secret"):
        if tag.has_attr("sid"):
            del tag["sid"]

    return str(edited_soup).strip()


def render_templates(original: str) -> str:
    def process_templates(content: str) -> str:
        soup = BeautifulSoup(content, "html.parser")

        for include_only in soup.find_all("includeonly"):
            include_only.unwrap()

        for no_include in soup.find_all("noinclude"):
            no_include.replace_with("")

        for instance in soup.find_all("template"):
            name = instance.get("name")
            if name:
                params = {attr: instance.get(attr) for attr in instance.attrs if attr != "name"}
                params["body"] = "".join(str(child) for child in instance.contents).strip()
                try:
                    page = Revision.objects.get(is_latest=True, page_type=PageType.TEMPLATE.value, title=name)
                    body = page.body

                    for key, value in params.items():
                        placeholder = re.compile(rf"{{{{\s*{key}\s*}}}}")
                        body = placeholder.sub(value, body)

                    body = process_templates(body)
                    instance.replace_with(body)
                except Revision.DoesNotExist:
                    instance.replace_with("")

        return str(soup).strip()

    return process_templates(original)


def render_template_pages(original: str) -> str:
    soup = BeautifulSoup(original, "html.parser")

    for include_only in soup.find_all("includeonly"):
        include_only.replace_with("")

    for no_include in soup.find_all("noinclude"):
        no_include.unwrap()

    return str(soup).strip()


def render_links(original: str) -> str:
    def replace_link(match) -> str:
        content = match.group(1).strip()

        if "|" in content:
            key, text = map(str.strip, content.split("|", 1))
        else:
            key = text = content.strip()

        slug_prefix = "/wiki/"
        slug = key[len(slug_prefix) :].rstrip("/") if key.startswith(slug_prefix) else key
        page = Revision.objects.filter(is_latest=True).filter(Q(title=key) | Q(slug=slug)).first()

        if page:
            url = reverse("wiki:page", kwargs={"slug": page.slug})
            return f'<a href="{url}">{text}</a>'
        else:
            payload = {"title": key}
            querystring = urlencode(payload, quote_via=quote_plus)
            url = reverse("wiki:create") + "?" + querystring
            return f'<a href="{url}" class="new">{text}</a>'

    regex = re.compile(r"\[\[(.*?)\]\]")
    return regex.sub(replace_link, original)


def render_markdown(original: str) -> str:
    allowed_content_tags = [
        "p",
        "div",
        "span",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "table",
        "thead",
        "tbody",
        "tfoot",
        "th",
        "td",
        "tr",
        "article",
        "aside",
        "section",
        "figure",
        "figcaption",
        "header",
        "footer",
        "details",
        "summary",
        "nav",
    ]
    allowed_tags = set(bleach.sanitizer.ALLOWED_TAGS.union(allowed_content_tags, {"img"}))
    allowed_attributes = bleach.sanitizer.ALLOWED_ATTRIBUTES.copy()
    allowed_attributes.update(
        {
            "*": ["class", "style", "id"],
            "a": ["href"],
            "img": ["src", "alt"],
        }
    )

    html = markdown.markdown(original, extensions=["extra", "tables", "fenced_code", "sane_lists"])
    clean_html = bleach.clean(html, tags=allowed_tags, attributes=allowed_attributes, strip=True)
    soup = BeautifulSoup(clean_html, "html.parser")

    for tag in soup.find_all():
        if tag.name in allowed_content_tags and not tag.get_text(strip=True):
            tag.decompose()
        elif not tag.get_text(strip=True):
            tag.extract()

    return str(soup).strip()


def render(original: str, character: WikiPage) -> str:
    redacted = render_secrets(original, character)
    templated = render_templates(redacted)
    linked = render_links(templated)
    return render_markdown(linked)
