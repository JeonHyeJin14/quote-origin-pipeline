"""
Search-query construction utilities.
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from qdd2.name_resolution import resolve_person_name_en
from qdd2.translation import translate_ko_to_en

logger = logging.getLogger(__name__)


def _normalize_token(tok: str) -> str:
    """Normalize token for deduplication: lowercase, strip punctuation/extra spaces."""
    normalized = re.sub(r"[^\w\s]", " ", tok).lower()
    return " ".join(normalized.split()).strip()


def _dedupe_preserve(seq: List[str]) -> List[str]:
    """Remove duplicates while preserving order and ignoring empty tokens (punct/space-insensitive)."""
    seen = set()
    out: List[str] = []
    for item in seq:
        if not item:
            continue
        norm = _normalize_token(item)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        out.append(item)
    return out


def generate_search_query(
    entities_by_type: Dict[str, List[str]],
    keywords: List[Tuple[str, float]],
    top_k: int = 3,
    quote_sentence: Optional[str] = None,
    article_date: Optional[str] = None,  # YYYY-MM-DD
    rollcall_mode: bool = False,
    use_wikidata: bool = True,
) -> Dict[str, Optional[str]]:
    """
    Build Korean/English search queries using entities + keywords.

    rollcall_mode=True:
        query = [speaker_en] [article_date_en] [top keyword en]
    default:
        query = speaker + location tokens + keyword tokens + optional quoted sentence
    """
    per_list = entities_by_type.get("PER", [])
    if not per_list:
        return {"ko": None, "en": None}

    speaker_ko = per_list[0]
    if use_wikidata:
        speaker_en = resolve_person_name_en(speaker_ko)
    else:
        try:
            speaker_en = translate_ko_to_en(speaker_ko)
        except Exception:
            speaker_en = speaker_ko

    loc_list = entities_by_type.get("LOC", [])[:2]
    loc_list = _dedupe_preserve(loc_list)
    locs_ko = " ".join(loc_list)
    locs_en_tokens: List[str] = []
    for loc in loc_list:
        try:
            loc_en_full = translate_ko_to_en(loc)
            loc_en_first = loc_en_full.split(",")[0]
            loc_en_first = " ".join(loc_en_first.split()[:2])
            if loc_en_first:
                locs_en_tokens.append(loc_en_first)
        except Exception:
            logger.warning("Location translation failed, falling back to original: %s", loc)
            locs_en_tokens.append(loc)

    top_kws_ko = [kw for kw, _ in keywords[:top_k]]
    top_kws_ko = _dedupe_preserve(top_kws_ko)
    kws_en_tokens: List[str] = []
    for kw_ko in top_kws_ko:
        try:
            kw_en_full = translate_ko_to_en(kw_ko)
            kw_en_trim = " ".join(kw_en_full.split()[:3])
            if kw_en_trim:
                kws_en_tokens.append(kw_en_trim)
        except Exception:
            logger.warning("Keyword translation failed, falling back to original: %s", kw_ko)
            kws_en_tokens.append(kw_ko)

    quote_en_full: Optional[str] = None
    if quote_sentence:
        try:
            quote_en_full = translate_ko_to_en(quote_sentence)
        except Exception:
            quote_en_full = None

    if rollcall_mode and article_date:
        try:
            dt = datetime.strptime(article_date, "%Y-%m-%d")
            date_en = dt.strftime("%B %d %Y")
        except Exception:
            date_en = article_date

        kw_ko_main = top_kws_ko[0] if top_kws_ko else ""
        kw_en_main = ""
        if kw_ko_main:
            try:
                kw_en_full = translate_ko_to_en(kw_ko_main)
                kw_en_main = kw_en_full.split()[0]
            except Exception:
                kw_en_main = kw_ko_main

        parts_en = [speaker_en]
        if date_en:
            parts_en.append(date_en)
        if kw_en_main:
            parts_en.append(kw_en_main)
        query_en = " ".join(parts_en).strip()

        parts_ko = [speaker_ko, article_date]
        if kw_ko_main:
            parts_ko.append(kw_ko_main)
        query_ko = " ".join(parts_ko).strip()

        return {"ko": query_ko or None, "en": query_en or None}

    query_en_tokens: List[str] = _dedupe_preserve([speaker_en] + locs_en_tokens + kws_en_tokens)
    if quote_en_full:
        query_en_tokens.append(quote_en_full)
    query_en = " ".join(query_en_tokens).strip()

    query_ko_parts = [speaker_ko]
    if locs_ko:
        query_ko_parts.append(locs_ko)
    if top_kws_ko:
        query_ko_parts.append(" ".join(top_kws_ko))
    if quote_sentence:
        query_ko_parts.append(quote_sentence)
    query_ko = " ".join(_dedupe_preserve(" ".join(query_ko_parts).split())).strip()

    return {"ko": query_ko or None, "en": query_en or None}
