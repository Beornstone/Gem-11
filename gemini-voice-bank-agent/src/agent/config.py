from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str | None = field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    eleven_api_key: str | None = field(default_factory=lambda: os.getenv("ELEVEN_API_KEY"))
    eleven_voice_id: str | None = field(default_factory=lambda: os.getenv("ELEVEN_VOICE_ID"))
    eleven_stt_model_id: str = field(default_factory=lambda: os.getenv("ELEVEN_STT_MODEL_ID", "scribe_v2"))
    eleven_tts_model_id: str = field(default_factory=lambda: os.getenv("ELEVEN_TTS_MODEL_ID", "eleven_flash_v2_5"))


def get_settings() -> Settings:
    return Settings()
