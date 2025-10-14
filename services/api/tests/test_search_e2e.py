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
    asset_id = ensure_seed

     # 1) Text was extracted
    t = httpx.get(f"{BASE}/documents/{asset_id}/text", timeout=15).json()
    assert "hello" in (t.get("text") or "").lower(), f"text missing 'hello': {t}"

    # 2) Asset appears in semantic search
    r = httpx.get(f"{BASE}/search?q=Hello", timeout=15); r.raise_for_status()
    data = r.json()
    ids = [row.get("id") for row in data.get("results", [])]
    assert asset_id in ids, f"Seeded asset {asset_id} not in results: {ids}"