import re

from bs4 import BeautifulSoup

from wiki.models import Secret, WikiPage


def render_secrets(original: str, character: WikiPage, editable: bool = False) -> str:
    soup = BeautifulSoup(original, "html.parser")
    sid = 0

    def process_secrets(parent):
        nonlocal sid
        secrets = parent.find_all("secret", recursive=False)
        for tag in secrets:
            expression = tag.get("show")
            sid += 1
            if expression:
                try:
                    if Secret.evaluate(expression, character):
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
