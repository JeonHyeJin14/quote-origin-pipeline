import requests
from bs4 import BeautifulSoup
from typing import List

API_BASE = "https://rollcall.com/wp-json/factbase/v1/search"


def get_search_results(query: str, top_k: int = 5) -> List[str]:
    params = {
        "q": query,
        "media": "",
        "type": "",
        "sort": "date",
        "location": "all",
        "place": "all",
        "page": 1,
        "format": "json",
    }

    resp = requests.get(API_BASE, params=params, timeout=10)
    print("[ROLLCALL] status:", resp.status_code, "url:", resp.url)

    if resp.status_code != 200:
        return []

    try:
        payload = resp.json()
    except Exception:
        print("[ROLLCALL] invalid json")
        return []

    data = payload.get("data", []) or []
    print("[ROLLCALL] data_len:", len(data))

    links: List[str] = []
    seen = set()

    for idx, item in enumerate(data):
        url = item.get("factbase_url") or item.get("url") or item.get("permalink")
        if not url:
            continue

        # 트럼프 factbase면 다 허용 (나중에 타입 필터 세분화 가능)
        if "/factbase/trump/" not in url:
            continue

        base_url = url.split("#", 1)[0]
        if base_url in seen:
            continue
        seen.add(base_url)
        links.append(base_url)

        if idx < 3:
            print(f"[ROLLCALL] sample link {idx}: {base_url}")

        if len(links) >= top_k:
            break

    print("[ROLLCALL] final links:", len(links))
    return links


def fetch_transcript_text(url: str) -> str:
    """
    Rollcall transcript 페이지에서 'Full Transcript' 이하 <p>들을 이어붙여 하나의 텍스트로 반환.
    못 찾으면 페이지의 모든 <p>를 fallback으로 사용.
    """
    print("[ROLLCALL] fetch_transcript_text:", url)
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # "Full Transcript" 헤더 이후의 p 태그만 모으기
    header = soup.find(lambda t: t.name in ("h2", "h3") and "Full Transcript" in t.get_text())
    paragraphs = []

    if header:
        for sib in header.find_all_next():
            if sib.name in ("h2", "h3"):
                break
            if sib.name == "p":
                txt = sib.get_text(" ", strip=True)
                if txt:
                    paragraphs.append(txt)
    else:
        # fallback: 모든 p
        for p in soup.find_all("p"):
            txt = p.get_text(" ", strip=True)
            if txt:
                paragraphs.append(txt)

    text = "\n".join(paragraphs)
    print("[ROLLCALL] transcript chars:", len(text))
    return text
