from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.backend.database import init_db
from src.backend.users.router import router as auth_router
from src.backend.tasks.router import router as chat_router
from src.ai_component.modules.db_memory import db_config
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Init SQLAlchemy tables (users, chats)
    await init_db()
    
    # Init LangGraph checkpointer tables (checkpoints, writes, etc.)
    async with AsyncPostgresSaver.from_conn_string(db_config.PG_CONN) as saver:
        await saver.setup()
    
    yield


app = FastAPI(title="AI Document Chat API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router)


@app.get("/health")
async def health():
    return {"status": "ok"}