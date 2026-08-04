
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import AIConfig
from models import ChatMessage as ChatMessageModel
from models import ChatState

router = APIRouter(prefix="/agent", tags=["agent"])


class ChatMessage(BaseModel):
    role: str  # system / user / assistant / tool
    content: str = ""
    tool_calls: list | None = None
    tool_call_id: str | None = None


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    thinking: bool = False


class ChatResponse(BaseModel):
    reply: str
    tool_calls_log: list[dict] = []


class HistoryMessage(BaseModel):
    role: str  # user / assistant
    content: str = ""


class StatePayload(BaseModel):
    thinking: bool = False


def _get_state(db: Session) -> ChatState:
    st = db.get(ChatState, 1)
    if not st:
        st = ChatState(id=1, thinking=False)
        db.add(st)
        db.commit()
        db.refresh(st)
    return st


@router.get("/state")
def get_state(db: Session = Depends(get_db)):
    st = _get_state(db)
    return {"thinking": st.thinking}


@router.post("/state")
def set_state(payload: StatePayload, db: Session = Depends(get_db)):
    st = _get_state(db)
    st.thinking = payload.thinking
    st.updated_at = datetime.now()
    db.commit()
    return {"thinking": st.thinking}


@router.get("/history")
def list_history(db: Session = Depends(get_db)):
    msgs = (
        db.query(ChatMessageModel)
        .order_by(ChatMessageModel.created_at, ChatMessageModel.id)
        .all()
    )
    return [
        {"id": m.id, "role": m.role, "content": m.content}
        for m in msgs
    ]


@router.post("/history", status_code=201)
def add_history(payload: HistoryMessage, db: Session = Depends(get_db)):
    if payload.role not in ("user", "assistant"):
        raise HTTPException(400, "role 只能是 user 或 assistant")
    m = ChatMessageModel(role=payload.role, content=payload.content)
    db.add(m)
    db.commit()
    return {"id": m.id, "role": m.role, "content": m.content}


@router.delete("/history", status_code=204)
def clear_history(db: Session = Depends(get_db)):
    db.query(ChatMessageModel).delete()
    db.commit()


@router.get("/tools")
def list_tools():
    from agent.tools import TOOL_SCHEMAS

    return [t["function"]["name"] for t in TOOL_SCHEMAS]


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    cfg = db.query(AIConfig).filter(AIConfig.is_default == True).first()  # noqa: E712
    if not cfg:
        raise HTTPException(
            400, "尚未配置 AI 提供商。请到 设置 → AI 提供商 添加并设为默认。"
        )
    if not cfg.model:
        raise HTTPException(400, "该提供商未填写模型名，请先在设置中配置。")

    from agent.client import run_agent_loop

    result = run_agent_loop(
        cfg, [m.model_dump() for m in payload.messages], thinking=payload.thinking
    )
    return ChatResponse(reply=result["reply"], tool_calls_log=result["tool_calls_log"])


@router.post("/chat/stream")
def chat_stream(payload: ChatRequest, db: Session = Depends(get_db)):
    cfg = db.query(AIConfig).filter(AIConfig.is_default == True).first()  # noqa: E712
    if not cfg:
        raise HTTPException(
            400, "尚未配置 AI 提供商。请到 设置 → AI 提供商 添加并设为默认。"
        )
    if not cfg.model:
        raise HTTPException(400, "该提供商未填写模型名，请先在设置中配置。")

    import json

    from agent.client import stream_agent_loop

    def event_stream():
        try:
            for evt in stream_agent_loop(
                cfg,
                [m.model_dump() for m in payload.messages],
                thinking=payload.thinking,
            ):
                yield f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"
        except Exception as e:  # noqa: BLE001
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)[:200]}, ensure_ascii=False)}\n\n"
        finally:
            yield "data: {\"type\": \"end\"}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
