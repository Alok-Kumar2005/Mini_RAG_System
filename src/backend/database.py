import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

BASE_DIR = __import__("os").path.abspath(
    __import__("os").path.join(__import__("os").path.dirname(__file__), "..", "..")
)
DATABASE_URL = f"sqlite+aiosqlite:///{BASE_DIR}/app.db"
 
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
 
 
class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
 
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
 
    chats: Mapped[list["Chat"]] = relationship("Chat", back_populates="user", cascade="all, delete")
 
 
class Chat(Base):
    __tablename__ = "chats"
 
    id : Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False, default="New Chat")
    session_id: Mapped[str] = mapped_column(String, nullable=True)
    pdf_filename: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
 
    user: Mapped["User"] = relationship("User", back_populates="chats")
 
 
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
 
 
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session