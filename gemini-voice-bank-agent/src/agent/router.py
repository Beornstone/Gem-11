from __future__ import annotations

from fastapi import APIRouter

from .gemini_client import GeminiIntentClient
from .schema import (
    CancelIntent,
    CheckBalanceIntent,
    ClarifyIntent,
    ConfirmIntent,
    HelpIntent,
    OpenBalanceAction,
    OpenTransferAction,
    HighlightSendAction,
    GoHomeAction,
    TransferDraftIntent,
    TurnRequest,
    TurnResponse,
)
from .session_store import session_store

router = APIRouter()


def get_client() -> GeminiIntentClient:
    return GeminiIntentClient()


@router.post("/api/agent/turn", response_model=TurnResponse)
def agent_turn(req: TurnRequest) -> TurnResponse:
    state = session_store.get(req.session_id)
    client = get_client()
    intent, debug = client.classify_intent(
        transcript=req.transcript,
        payees_allowed=state.payees_allowed,
        pending_transfer=state.pending_transfer,
    )

    ui_action = None
    assistant_say = intent.assistant_say

    if isinstance(intent, CheckBalanceIntent):
        state.screen = "balance"
        assistant_say = "Your balance is €1,234.56."
        ui_action = OpenBalanceAction(type="OPEN_BALANCE")
    elif isinstance(intent, TransferDraftIntent):
        if intent.payee_label not in state.payees_allowed:
            intent = ClarifyIntent(
                intent="CLARIFY",
                assistant_say="I can only transfer to saved payees. Which one should I use?",
                choices=state.payees_allowed,
            )
            assistant_say = intent.assistant_say
        elif intent.amount <= 0 or intent.amount > 10000:
            intent = ClarifyIntent(
                intent="CLARIFY",
                assistant_say="Amount must be greater than 0 and at most 10000 EUR.",
                choices=None,
            )
            assistant_say = intent.assistant_say
        else:
            state.pending_transfer = {
                "payee_label": intent.payee_label,
                "amount": intent.amount,
                "currency": intent.currency,
            }
            state.screen = "transfer"
            ui_action = OpenTransferAction(type="OPEN_TRANSFER", **state.pending_transfer)
    elif isinstance(intent, ConfirmIntent):
        if state.pending_transfer:
            assistant_say = "Review and press Send."
            ui_action = HighlightSendAction(type="HIGHLIGHT_SEND")
        else:
            intent = ClarifyIntent(
                intent="CLARIFY",
                assistant_say="There is no pending transfer to confirm.",
                choices=None,
            )
            assistant_say = intent.assistant_say
    elif isinstance(intent, CancelIntent):
        state.pending_transfer = None
        state.screen = "home"
        ui_action = GoHomeAction(type="GO_HOME")
    elif isinstance(intent, HelpIntent):
        assistant_say = intent.assistant_say

    return TurnResponse(
        assistant_say=assistant_say,
        intent=intent,
        ui_action=ui_action,
        debug=debug,
    )
