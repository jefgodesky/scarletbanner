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
