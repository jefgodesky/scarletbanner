import re

from bs4 import BeautifulSoup

from wiki.enums import PageType
from wiki.models import Revision, Secret, WikiPage


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
                try:
                    page = Revision.objects.get(is_latest=True, page_type=PageType.TEMPLATE.value, title=name)
                    body = page.body

                    for key, value in params.items():
                        placeholder = f"{{{{ {key} }}}}"
                        body = body.replace(placeholder, value)

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
