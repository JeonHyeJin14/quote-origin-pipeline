from qdd2.translation import translate_ko_to_en
from qdd2.pipeline import build_queries_from_text
from qdd2.search_client import google_cse_search
from qdd2.rollcall_search import get_search_results
from qdd2.snippet_matcher import find_best_span_from_candidates_debug
from qdd2.text_utils import split_sentences


def normalize_search_results(res):
    if isinstance(res, list):
        return res
    if isinstance(res, dict):
        if "results" in res and isinstance(res["results"], list):
            return res["results"]
        return list(res.values())
    return []


def extract_candidates_from_results(search_results):
    candidates = []
    for r in search_results:
        snippet = r.get("snippet") or ""
        sents = split_sentences(snippet)
        candidates.extend(sents)
    return candidates


def find_origin(quote_id: str, quote_content: str, use_rollcall: bool = False):
    print("DEBUG TYPE QUOTE_CONTENT =", type(quote_content))
    print("DEBUG QUOTE_CONTENT =", quote_content)

    if not isinstance(quote_content, str):
        quote_content = str(quote_content)

    quote_en = translate_ko_to_en(quote_content)

    pipeline_result = build_queries_from_text(quote_content)
    print("DEBUG TYPE pipeline_result =", type(pipeline_result))
    print("DEBUG pipeline_result =", pipeline_result)

    queries = pipeline_result.get("queries", {})
    query = queries.get("en") or queries.get("ko")

    if not query:
        return {
            "quote_id": quote_id,
            "quote_content": quote_content,
            "candidate_index": None,
            "original_span": None,
            "similarity_score": None,
        }

    raw_results = get_search_results(query) if use_rollcall else google_cse_search(query)
    search_results = normalize_search_results(raw_results)

    if not search_results:
        return {
            "quote_id": quote_id,
            "quote_content": quote_content,
            "candidate_index": None,
            "original_span": None,
            "similarity_score": None,
        }

    candidates = extract_candidates_from_results(search_results)

    if not candidates:
        return {
            "quote_id": quote_id,
            "quote_content": quote_content,
            "candidate_index": None,
            "original_span": None,
            "similarity_score": None,
        }

    best_idx, best_score, best_span = find_best_span_from_candidates_debug(
        quote_text=quote_en,
        candidates=candidates,
    )

    return {
        "quote_id": quote_id,
        "quote_content": quote_content,
        "candidate_index": best_idx,
        "original_span": best_span,
        "similarity_score": float(best_score),
    }
