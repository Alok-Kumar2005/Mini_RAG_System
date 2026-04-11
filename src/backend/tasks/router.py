import json
import uuid
from typing import List, AsyncIterator
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from src.backend.database import get_db, Chat, User
from src.backend.users.controller import get_current_user
from src.backend.tasks.schemas import ChatCreate, ChatOut, MessageRequest, UploadResponse, ChatRename
from src.backend.ingestion import ingest_pdf
from src.ai_component.graph.graph import Workflow
from src.ai_component.modules.db_memory import db_config
from src.backend.tasks.controller import _get_chat_or_404, _sse, _stream_graph_events
from src.ai_component.llm import LLMClient
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.logger import logging

router = APIRouter(prefix="/api/chats", tags=["chats"])

@router.post("", response_model= ChatOut, status_code= status.HTTP_201_CREATED)
async def create_chat(body: ChatCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat = Chat(
        user_id = current_user.id,
        title = body.title
    )
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return chat

@router.get("", response_model=List[ChatOut])
async def list_chats(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Chat).where(Chat.user_id == current_user.id).order_by(Chat.created_at.desc()))
    return result.scalars().all()

@router.get("/{chat_id}", response_model=ChatOut)
async def get_chat(chat_id: str,db: AsyncSession = Depends(get_db),current_user: User = Depends(get_current_user),):
    return await _get_chat_or_404(chat_id, current_user, db)

@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(chat_id: str,db: AsyncSession = Depends(get_db),current_user: User = Depends(get_current_user)):
    chat = await _get_chat_or_404(chat_id, current_user, db)
    await db.delete(chat)
    await db.commit()


@router.post("/{chat_id}/upload", response_model=UploadResponse)
async def upload_pdf(chat_id: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
 
    chat = await _get_chat_or_404(chat_id, current_user, db)
 
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    session_id = f"chat_{chat_id}_{uuid.uuid4().hex[:8]}"
 
    try:
        chunks = await ingest_pdf(file_bytes, session_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logging.error(f"[Upload] Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail="PDF ingestion failed.")
 
    chat.session_id = session_id
    chat.pdf_filename = file.filename
    # if chat.title == "New Chat":
    #     chat.title = file.filename.replace(".pdf", "")
    await db.commit()
    await db.refresh(chat)
 
    return UploadResponse(
        session_id=session_id,
        chunks_ingested=chunks,
        message=f"Successfully ingested '{file.filename}' ({chunks} chunks).",
    )
 
@router.patch('/{chat_id}/rename', response_model= ChatOut)
async def rename_chat(chat_id: str, body: ChatRename, db: AsyncIterator = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Chat).where(Chat.id == chat_id, Chat.user_id == current_user.id))
    chat = result.scalar_one_or_none()

    if not chat:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail= "Chat not found.. ")
    chat.title = body.title
    await db.commit()
    await db.refresh(chat)
    return chat
 
# ---------------------------------------------------------------------------
# Streaming Message endpoint
# ---------------------------------------------------------------------------
 
@router.post("/{chat_id}/message")
async def send_message(
    chat_id: str,
    body: MessageRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = await _get_chat_or_404(chat_id, current_user, db)
    # logging.info(f"[Chat title] : {chat.title}")
    if chat.title == "New Chat":
        client = LLMClient(temperature= 0, max_tokens= 150)
        new_title = await client.generate_chat_title(body.content)
        chat.title = new_title
        await db.commit()
        await db.refresh(chat)
 
    async def generator():
        async for chunk in _stream_graph_events(chat, body.content):
            if await request.is_disconnected():
                logging.info(f"[Stream] Client disconnected — chat {chat_id}")
                break
            yield chunk
 
    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection":    "keep-alive",
            "X-Accel-Buffering": "no",   # critical: stops nginx from buffering SSE
        },
    )
 

@router.get("/{chat_id}/history")
async def get_history(chat_id: str,db: AsyncSession = Depends(get_db),current_user: User = Depends(get_current_user)):
    await _get_chat_or_404(chat_id, current_user, db)
 
    # async with AsyncSqliteSaver.from_conn_string(db_config.DB_PATH) as checkpointer:
    #     config = {"configurable": {"thread_id": chat_id}}
    #     checkpoint = await checkpointer.aget(config)
    async with AsyncPostgresSaver.from_conn_string(db_config.PG_CONN) as checkpointer:
        config = {"configurable": {"thread_id": chat_id}}
        checkpoint = await checkpointer.aget(config)
 
    if not checkpoint:
        return {"messages": []}
 
    channel_values = checkpoint.get("channel_values", {})
    raw_messages = channel_values.get("messages", [])
    summary = channel_values.get("summarize") or None 
    history = []
    for m in raw_messages:
        if isinstance(m, HumanMessage):
            if m.content.startswith("System Feedback:"):
                continue
            history.append({"role": "user", "content": m.content})
        elif isinstance(m, AIMessage):
            history.append({"role": "assistant", "content": m.content})

    return {"messages": history, "summary": summary}
 