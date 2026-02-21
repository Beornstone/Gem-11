import httpx
from fastapi.testclient import TestClient

from src.main import app
from src.agent import router
from src.agent.schema import (
    TransferDraftIntent,
    ConfirmIntent,
    CancelIntent,
    CheckBalanceIntent,
)


class StubGeminiClient:
    def __init__(self, intent):
        self.intent = intent

    def classify_intent(self, transcript, payees_allowed, pending_transfer):
        return self.intent, {"stub": True}


def test_transfer_draft_and_confirm_flow():
    router.get_client = lambda: StubGeminiClient(
        TransferDraftIntent(
            intent="TRANSFER_DRAFT",
            payee_label="James (Son)",
            amount=25,
            currency="EUR",
            assistant_say="Drafting transfer",
        )
    )
    client = TestClient(app)
    r = client.post("/api/agent/turn", json={"session_id": "s1", "transcript": "send 25"})
    body = r.json()
    assert body["ui_action"]["type"] == "OPEN_TRANSFER"

    router.get_client = lambda: StubGeminiClient(
        ConfirmIntent(intent="CONFIRM", assistant_say="confirming")
    )
    r2 = client.post("/api/agent/turn", json={"session_id": "s1", "transcript": "confirm"})
    body2 = r2.json()
    assert body2["ui_action"]["type"] == "HIGHLIGHT_SEND"
    assert body2["assistant_say"] == "Review and press Send."


def test_check_balance_and_cancel():
    client = TestClient(app)
    router.get_client = lambda: StubGeminiClient(
        CheckBalanceIntent(intent="CHECK_BALANCE", assistant_say="balance")
    )
    rb = client.post("/api/agent/turn", json={"session_id": "s2", "transcript": "balance"})
    assert rb.json()["ui_action"]["type"] == "OPEN_BALANCE"

    router.get_client = lambda: StubGeminiClient(
        CancelIntent(intent="CANCEL", assistant_say="cancel")
    )
    rc = client.post("/api/agent/turn", json={"session_id": "s2", "transcript": "cancel"})
    assert rc.json()["ui_action"]["type"] == "GO_HOME"


def test_voice_stt_returns_502_on_upstream_failure(monkeypatch):
    monkeypatch.setenv("ELEVEN_API_KEY", "test-key")
    client = TestClient(app)

    def fake_post(*args, **kwargs):
        return httpx.Response(status_code=500, request=httpx.Request("POST", "https://api.elevenlabs.io"))

    monkeypatch.setattr(httpx.Client, "post", fake_post)
    res = client.post(
        "/api/voice/stt",
        files={"audio": ("sample.webm", b"bytes", "audio/webm")},
    )

    assert res.status_code == 502
    assert "STT upstream failure" in res.json()["detail"]


def test_voice_tts_returns_audio_mpeg(monkeypatch):
    monkeypatch.setenv("ELEVEN_API_KEY", "test-key")
    monkeypatch.setenv("ELEVEN_VOICE_ID", "voice-123")
    client = TestClient(app)

    def fake_post(*args, **kwargs):
        return httpx.Response(
            status_code=200,
            content=b"mp3-bytes",
            request=httpx.Request("POST", "https://api.elevenlabs.io"),
        )

    monkeypatch.setattr(httpx.Client, "post", fake_post)
    res = client.post("/api/voice/tts", json={"text": "hello"})

    assert res.status_code == 200
    assert res.headers["content-type"].startswith("audio/mpeg")
    assert res.content == b"mp3-bytes"
