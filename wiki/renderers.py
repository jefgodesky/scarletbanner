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
    soup = BeautifulSoup(original, "html.parser")

    for template_call in soup.find_all("template"):
        name = template_call.get("name")
        if name:
            params = {attr: template_call.get(attr) for attr in template_call.attrs if attr != "name"}
            try:
                page = Revision.objects.get(is_latest=True, page_type=PageType.TEMPLATE.value, title=name)
                content = page.body
                template_soup = BeautifulSoup(content, "html.parser")

                for no_include in template_soup.find_all("noinclude"):
                    no_include.replace_with("")

                content = str(template_soup).strip()

                for key, value in params.items():
                    placeholder = f"{{{{ {key} }}}}"
                    content = content.replace(placeholder, value)

                template_call.replace_with(content)
            except Revision.DoesNotExist:
                template_call.replace_with("")

    return str(soup).strip()
