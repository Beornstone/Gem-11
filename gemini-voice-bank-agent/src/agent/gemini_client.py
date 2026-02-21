from __future__ import annotations

import json
import os
import re
from typing import Any

from google import genai
from pydantic import TypeAdapter, ValidationError

from .schema import ClarifyIntent, Intent


JSON_RE = re.compile(r"\{.*\}", re.DOTALL)
intent_adapter = TypeAdapter(Intent)


class GeminiIntentClient:
    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is required")
        self.client = genai.Client(api_key=api_key)
        self.primary_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.fallback_model = "gemini-1.5-flash"

    def classify_intent(
        self,
        transcript: str,
        payees_allowed: list[str],
        pending_transfer: dict | None,
    ) -> tuple[Intent, dict[str, Any] | None]:
        prompt = self._build_prompt(transcript, payees_allowed, pending_transfer)

        raw_text, model_used = self._generate_with_fallback(prompt)
        parsed = self._extract_and_validate(raw_text)
        if parsed is not None:
            return parsed, {"model": model_used, "raw": raw_text}

        repair_prompt = (
            "You returned invalid JSON. Return ONLY ONE corrected JSON object that matches the schema.\n"
            f"Original output:\n{raw_text}"
        )
        repaired_text, repair_model = self._generate_with_fallback(repair_prompt)
        repaired = self._extract_and_validate(repaired_text)
        if repaired is not None:
            return repaired, {"model": repair_model, "raw": repaired_text, "repair": True}

        fallback = ClarifyIntent(
            intent="CLARIFY",
            assistant_say="I didn't catch that. Please rephrase your request.",
            choices=None,
        )
        return fallback, {"error": "intent_parse_failed", "raw": repaired_text}

    def _build_prompt(
        self,
        transcript: str,
        payees_allowed: list[str],
        pending_transfer: dict | None,
    ) -> str:
        schema_description = {
            "CHECK_BALANCE": {"intent": "CHECK_BALANCE", "assistant_say": "string"},
            "TRANSFER_DRAFT": {
                "intent": "TRANSFER_DRAFT",
                "payee_label": "string",
                "amount": "number",
                "currency": "EUR",
                "assistant_say": "string",
            },
            "CONFIRM": {"intent": "CONFIRM", "assistant_say": "string"},
            "CANCEL": {"intent": "CANCEL", "assistant_say": "string"},
            "CLARIFY": {
                "intent": "CLARIFY",
                "assistant_say": "string",
                "choices": ["string"]
            },
            "HELP": {"intent": "HELP", "assistant_say": "string"},
        }
        return (
            "You are an intent classifier for a banking voice assistant.\n"
            "Return ONLY JSON. No markdown, no explanation.\n"
            "Valid intents and shape:\n"
            f"{json.dumps(schema_description)}\n"
            "Rules: if user asks to send/transfer money, use TRANSFER_DRAFT. "
            "Use exact payee label when possible. If ambiguous, choose CLARIFY.\n"
            f"payees_allowed={json.dumps(payees_allowed)}\n"
            f"pending_transfer={json.dumps(pending_transfer)}\n"
            f"transcript={json.dumps(transcript)}\n"
        )

    def _generate_with_fallback(self, prompt: str) -> tuple[str, str]:
        try:
            resp = self.client.models.generate_content(model=self.primary_model, contents=prompt)
            return (resp.text or ""), self.primary_model
        except Exception:
            resp = self.client.models.generate_content(model=self.fallback_model, contents=prompt)
            return (resp.text or ""), self.fallback_model

    def _extract_and_validate(self, text: str) -> Intent | None:
        match = JSON_RE.search(text)
        if not match:
            return None
        try:
            payload = json.loads(match.group(0))
            return intent_adapter.validate_python(payload)
        except (json.JSONDecodeError, ValidationError):
            return None
