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
    r = httpx.get(f"{BASE}/search?q=Hello", timeout=15)
    r.raise_for_status()
    data = r.json()
    results = data["results"]
    assert len(results) >= 1, f"Expected at least one search hit, got: {data}"
    assert any("Hello" in (row.get("snippet") or row.get("text") or "") for row in results), \
        f"No 'Hello' in results; first result: {results[0] if results else '[]'}"