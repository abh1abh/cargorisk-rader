from typing import Any

import requests

# from ..core.config import settings
from ..core.logging import get_logger
from ..domain.exceptions import ModelServiceError

# from requests import requests, RequestException
log = get_logger("llm.hf")

PROMPT_SYSTEM = """You are an information-extraction assistant.
Return ONLY valid JSON matching:
{
  "source_asset_id": <int>,
  "meta": {"note":"freight-only"},
  "items": [{
    "origin": null|string, "destination": null|string,
    "mode": "sea"|"air"|"road"|null, "carrier": null|string,
    "equipment": null|"20GP"|"40GP"|"40HC"|"45HC",
    "qty": null|int, "currency": null|string,
    "rate_per_unit": null|number, "total_freight": null|number,
    "valid_from": null|"YYYY-MM-DD", "valid_to": null|"YYYY-MM-DD",
    "confidence": number, "raw_cells": {"line": string}
  }]
}
Rules:
- STRICT JSON, no markdown or commentary.
- Extract one item for **each lane/row** found in the OCR table(s).
- If a row lists multiple equipment prices (20DC/40DC/40HQ), emit **one item per equipment** where equipment ∈ {"20GP","40GP","40HC"}:
  - Map 20DC→20GP, 40DC→40GP, 40HQ→40HC.
- Set "mode" to "sea" for ocean table rows.
- Keep strings short.
- raw_cells.line MUST be a single line (no newlines), <= 120 chars (truncate if needed).
- If unsure, use null.
"""


USER_TPL = """OCR_TEXT:
{t}

Instructions:
- First, extract lanes under the 'Ocean Rates' sheet/table.
- Ignore 'Surcharges' and any explanatory 'Conditions' text.
- If there is also a Rotterdam table, extract those lanes too.
Return ONLY the JSON object; no commentary."""

class HfQwenFreightExtractor:
    def __init__(
            self, 
            base_url: str | None = None, 
            api_key: str | None = None, 
            model: str = "Qwen/Qwen2.5-7B-Instruct:together",
            timeout_sec: int = 60,
    ):
        if not api_key:
            raise RuntimeError("HF_API_KEY not set")
        self.base_url = (base_url or "https://router.huggingface.co/v1").rstrip("/") 
        self.api_key = api_key.strip()
        self.model = model.strip()
        self.timeout = timeout_sec
        self._chat_url = f"{self.base_url}/chat/completions"
        log.info("Router base: %r, model: %r", self.base_url, self.model)
    
    # Private
    def _post_chat(self, messages: list[dict], max_tokens: int = 512, temperature: float = 0.0) -> dict:
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "response_format": {"type": "json_object"},

        }
        try:
            r = requests.post(
                self._chat_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
                timeout=self.timeout,
            )
            if not r.ok:
                log.error(f"Router error {r.status_code}: {r.text}")
                r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            log.exception("HF Router network/HTTP error")
            raise ModelServiceError(f"HuggingFace router call failed: {e}") from e

    # Public
    def test(self) -> dict[str, Any]:
        data = self._post_chat(
            messages=[{"role": "user", "content": "What is the capital of France?"}],
            max_tokens=16,
        )
        # HF example reads choices[0]["message"]
        return {"ok": True, "message": data["choices"][0]["message"]}

    def extract_freight(self, ocr_text: str, source_asset_id: int | None = None) -> dict[str, Any]:
        pass
