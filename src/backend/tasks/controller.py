import json
from typing import AsyncIterator
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain_core.messages import HumanMessage
from src.backend.database import get_db, Chat, User
from src.ai_component.graph.graph import Workflow
from src.ai_component.modules.db_memory import db_config
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.logger import logging

async def _get_chat_or_404(chat_id: str, user: User, db: AsyncSession)-> Chat:
    result = await db.execute(select(Chat).where(Chat.id == chat_id, Chat.user_id == user.id))
    chat = result.scalar_one_or_none()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found.")
    return chat

def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"

async def _stream_graph_events(chat: Chat, user_message: str) -> AsyncIterator[str]:
    """
    Runs the LangGraph workflow with astream_events (v2) and yields SSE strings.
 
    Why astream_events v2:
      - Gives fine-grained events per node, per tool, per LLM token
      - Works correctly with subgraphs and ToolNode
      - The `name` field on each event maps to the node/tool/model name
 
    Event flow we handle:
      on_chain_start  (name="query_node")   -> status "Thinking..."
      on_chain_start  (name="judge_node")   -> status "Evaluating..."
      on_tool_start                         -> status "Searching document/web..."
      on_tool_end                           -> status "Search complete..."
      on_chat_model_stream                  -> token  (streamed text)
      on_chain_end    (name="judge_node")   -> retry event if verdict==No
      on_chain_end    (name="LangGraph")    -> done   (final event)
    """
    # checkpointer_ctx = AsyncSqliteSaver.from_conn_string(db_config.DB_PATH)
    # saver = await checkpointer_ctx.__aenter__()
    # graph = Workflow(checkpointer=saver)
    try:
        conn_string = db_config.PG_CONN + ("&" if "?" in db_config.PG_CONN else "?") + "connect_timeout=30&keepalives=1&keepalives_idle=30"
        
        async with AsyncPostgresSaver.from_conn_string(conn_string) as saver:
            await saver.setup()
            graph = Workflow(checkpointer=saver)
            config = {"configurable": {"thread_id": chat.id}}
            initial_state = {
                "messages": [HumanMessage(content=user_message)],
                "session_id": chat.session_id or "",
                "Judge_response": "",
                "Judge_reason": "",
                "max_loop": 0,
            }

            query_node_calls = 0

            async for event in graph.astream_events(initial_state, config=config, version="v2"):
                kind: str = event["event"]
                name: str = event.get("name", "")

                if kind == "on_chain_start":
                    if name == "query_node":
                        query_node_calls += 1
                        if query_node_calls == 1:
                            yield _sse({"type": "status", "message": "Thinking…"})
                    elif name == "judge_node":
                        yield _sse({"type": "status", "message": "Evaluating answer quality…"})
                    elif name == "summarizer_node":
                        yield _sse({"type": "status", "message": "Summarising conversation…"})

                elif kind == "on_tool_start":
                    tool_name = name or ""
                    friendly = {
                        "search_pdf_tool": "Searching the uploaded document…",
                        "tavily_search":   "Searching the web…",
                    }.get(tool_name, f"Running {tool_name}…")
                    yield _sse({"type": "status", "message": friendly, "tool": tool_name})

                elif kind == "on_tool_end":
                    yield _sse({"type": "status", "message": "Search complete, composing answer…"})

                elif kind == "on_chat_model_stream":
                    chunk = event["data"].get("chunk")
                    if chunk and hasattr(chunk, "content"):
                        content = chunk.content
                        if isinstance(content, str) and content:
                            yield _sse({"type": "token", "content": content})

                elif kind == "on_chain_end" and name == "judge_node":
                    output: dict = event["data"].get("output", {})
                    verdict: str = output.get("Judge_response", "")
                    reason: str  = output.get("Judge_reason", "")
                    if verdict == "No":
                        yield _sse({"type": "retry", "reason": reason, "attempt": query_node_calls})

                elif kind == "on_chain_end" and name == "summarizer_node":
                    yield _sse({"type": "status", "message": "Conversation summarised."})

                elif kind == "on_chain_end" and name == "LangGraph":
                    output: dict = event["data"].get("output", {})
                    yield _sse({
                        "type": "done",
                        "judge_verdict": output.get("Judge_response"),
                        "judge_reason":  output.get("Judge_reason"),
                    })

    except Exception as exc:
        logging.error(f"[Stream] Graph error for chat {chat.id}: {exc}")
        yield _sse({"type": "error", "message": "AI processing failed. Please try again."})