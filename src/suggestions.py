"""Search-box suggestions: catalog product names + everything searched/logged before."""
from __future__ import annotations

import re

import streamlit as st

from src import storage
from src.catalog import CATALOG, display_name

_SPEC = re.compile(r"\b\d+\s?(gb|tb)\b|\((.*?)\)", re.IGNORECASE)


def _short(name: str) -> str:
    """'Apple iPhone 17 256GB (Black)' -> 'Apple iPhone 17'"""
    return re.sub(r"\s+", " ", _SPEC.sub("", name)).strip(" -,")


@st.cache_data(ttl=300, show_spinner=False)
def get_suggestions(extra: tuple = ()) -> list[str]:
    names: dict[str, str] = {}   # lower-case -> display form (dedupes case variants)
    for p in CATALOG:
        full = display_name(p)
        for n in (full, _short(full)):
            if n:
                names.setdefault(n.lower(), n)
    for n in list(storage.past_searches()) + list(extra):
        n = storage.fix_mojibake(n).strip()
        if n and len(n) <= 90:
            names.setdefault(n.lower(), n)
    return sorted(names.values(), key=str.lower)