import os

import httpx
import pytest

BASE = os.getenv("BASE", "http://localhost:8000")

# def _ensure_asset_and_embed():
#     # be self-sufficient: upload a tiny doc and embed it
#     f = {'file': ('seed.txt', b'Hello seed content for vector search', 'text/plain')}
#     r = httpx.post(f"{BASE}/upload", files=f, timeout=15)
#     r.raise_for_status()
#     asset_id = r.json()['id']
#     r = httpx.post(f"{BASE}/documents/{asset_id}/embed", timeout=60)
#     r.raise_for_status()
#     return asset_id

@pytest.mark.e2e
def test_embed_and_search_e2e(ensure_seed):
    s = httpx.get(f"{BASE}/search?q=Hello", timeout=15).json()
    s.raise_for_status()
    data = s.json()
    assert "results" in data, "Missing 'results' key in /search response"
    assert any("Hello" in (r.get("text", "") or "") for r in data["results"]), \
        "No expected text found in search results"
