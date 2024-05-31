from typing import Any


def isstring(candidate: Any) -> bool:
    return isinstance(candidate, str) and len(candidate) > 0
