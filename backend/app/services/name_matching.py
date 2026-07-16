import re
from collections import defaultdict
from typing import TypeVar

_LEGAL_SUFFIXES = ("srl", "spa", "snc", "sas", "sc")


def normalize_name(name: str) -> str:
    """Lowercase, strip punctuation/whitespace, and drop a trailing Italian
    legal-form suffix (e.g. "Semantica Srl" / "SEMANTICA S.R.L." -> "semantica")
    so equivalent company names compare equal regardless of formatting."""
    n = name.strip().lower().replace(".", "")
    n = re.sub(r"[^\w\s]", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    for suffix in _LEGAL_SUFFIXES:
        if n.endswith(f" {suffix}"):
            n = n[: -(len(suffix) + 1)].strip()
            break
    return n


T = TypeVar("T")


def unique_normalized_index(items: list[T], name_of: "callable[[T], str]") -> dict[str, T]:
    """Build a normalize_name -> item index, dropping any key that more than
    one item maps to (an ambiguous normalized match is worse than none)."""
    groups: dict[str, list[T]] = defaultdict(list)
    for item in items:
        groups[normalize_name(name_of(item))].append(item)
    return {k: v[0] for k, v in groups.items() if len(v) == 1}
