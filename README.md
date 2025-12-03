# quote-origin-pipeline

Refactored into a modular package for easier extension and maintenance.

## Package layout (`qdd2/`)
- `config.py`: model names, labels, default domains, headers, and timeouts.
- `models.py`: lazy loaders for NER, KeyBERT, translation, and sentence encoders.
- `text_utils.py`: cleaning, normalization, sentence splitting, and quote extraction helpers.
- `entities.py`: NER execution + BIO merging.
- `keywords.py`: KeyBERT extraction with NER-aware re-ranking.
- `translation.py`: Korean→English translation helper.
- `name_resolution.py`: Wikidata lookup and person-name resolution with translation fallback.
- `search_client.py`: Google CSE client, HTML/PDF handling.
- `snippet_matcher.py`: snippet span selection using SBERT similarity.
- `query_builder.py`: build ko/en search queries from entities + keywords.
- `pipeline.py`: convenience wrapper combining extraction + query building.

## Compatibility shims
Legacy entrypoints are kept at the root:
- `find_original.py`, `generate_query.py`, `direct_quote.py`, `per_name.py`
  now re-export functions from `qdd2/` so existing imports keep working.

## Usage
```python
from qdd2.pipeline import build_queries_from_text

result = build_queries_from_text(text, article_date="2025-11-01")
print(result["keywords"])
print(result["queries"])
```

Or import individual helpers:
```python
from qdd2.keywords import extract_keywords_with_ner
from qdd2.query_builder import generate_search_query
```
