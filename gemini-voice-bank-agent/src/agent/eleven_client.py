from __future__ import annotations

import httpx

from .config import get_settings


class ElevenSTTClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.eleven_api_key:
            raise RuntimeError("ELEVEN_API_KEY is required")
        self.http = httpx.Client(timeout=45.0)

    def transcribe(self, audio_bytes: bytes, filename: str, content_type: str) -> str:
        response = self.http.post(
            "https://api.elevenlabs.io/v1/speech-to-text",
            headers={"xi-api-key": self.settings.eleven_api_key or ""},
            data={"model_id": self.settings.eleven_stt_model_id},
            files={"file": (filename, audio_bytes, content_type)},
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("text") or payload.get("transcript") or ""


class ElevenTTSClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.eleven_api_key:
            raise RuntimeError("ELEVEN_API_KEY is required")
        if not self.settings.eleven_voice_id:
            raise RuntimeError("ELEVEN_VOICE_ID is required")
        self.http = httpx.Client(timeout=45.0)

    def synthesize(self, text: str) -> bytes:
        response = self.http.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{self.settings.eleven_voice_id}/stream",
            headers={
                "xi-api-key": self.settings.eleven_api_key or "",
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": self.settings.eleven_tts_model_id,
                "output_format": "mp3_44100_128",
            },
        )
        response.raise_for_status()
        return response.content
