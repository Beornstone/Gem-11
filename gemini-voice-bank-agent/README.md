# gemini-voice-bank-agent

Minimal local demo: voice/text banking assistant with FastAPI + Gemini intent classification.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY=...
uvicorn src.main:app --reload --port 8000
```

Open http://localhost:8000/demo

## API

`POST /api/agent/turn`

Request:

```json
{ "session_id": "abc", "transcript": "transfer 50 to James" }
```

Response:

```json
{
  "assistant_say": "...",
  "intent": { "intent": "TRANSFER_DRAFT", "payee_label": "James (Son)", "amount": 50, "currency": "EUR", "assistant_say": "..." },
  "ui_action": { "type": "OPEN_TRANSFER", "payee_label": "James (Son)", "amount": 50, "currency": "EUR" },
  "debug": {}
}
```
