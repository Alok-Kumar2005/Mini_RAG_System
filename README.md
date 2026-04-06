# Mini RAG System

A modern, full-stack Retrieval-Augmented Generation (RAG) web application that allows users to upload PDF documents, build context, and chat intelligently with an AI assistant. The app features state-of-the-art streaming, beautiful glassmorphism design, and intelligent context summarization.

## Features

- **Document Ingestion**: Upload PDF documents seamlessly. Content is parsed and embedded using `sentence-transformers` and stored in a blazing-fast local Qdrant Vector Database.
- **RAG-Powered Chat**: Ask questions and get answers grounded *strictly* in the provided document content.
- **Live SSE Streaming**: Watch as the AI generates its response live token-by-token. Includes "thinking" and "evaluating" status indicators.
- **Intelligent Memory**: Powered by LangGraph! Conversations are automatically truncated and summarized periodically (every 15 messages) to save tokens without losing critical context.
- **Beautiful UI**: Modern Next.js frontend with dark mode, glowing accents, real-time Markdown rendering, and sleek CSS animations.
- **Session Auth**: JWT-based authentication so your chat history is safely tied to your account.
- **Smart Chat Management**: Auto-generation of chat titles using LLMs, plus options to rename or delete conversations natively.

---

## Tech Stack

### Backend
- **Python**: Core Language
- **FastAPI**: Asynchronous, highly-performant web framework
- **LangChain & LangGraph**: AI orchestration, prompt formulation, and checkpoint memory
- **Groq API**: For lightning-fast open-source LLM inference (`langchain-groq`)
- **Qdrant**: Vector database for similarity search and embeddings
- **SQLAlchemy & aiosqlite**: Relational database managing users & chats

### Frontend
- **Next.js 16 (App Router)**: React Framework
- **TypeScript**: Strict type integrity
- **Vanilla CSS**: Custom styling leveraging CSS Variables and standard keyframe animations (No Tailwind limitations!)
- **React-Markdown**: GitHub Flavored Markdown (GFM) parsing strictly rendering beautiful HTML tables, links, and code snippets natively in chat.
- **Lucide-React**: SVG Iconography

---

## Getting Started

### Prerequisites
- Node.js (v18+)
- Python (v3.10+)
- Docker (for running Qdrant locally)
- A Groq API Key

### 1. Start Qdrant Vector Database
The backend requires a local instance of Qdrant running to store and query document embeddings. Start it quickly using Docker:

```bash
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage:z \
    qdrant/qdrant
```
This will start Qdrant and expose it on `http://localhost:6333`.

### 2. Environment Setup

Copy `.env.example` to `.env` in the root folder, and fill in the necessary keys:
```env
GROQ_API_KEY=your_groq_key_here
SECRET_KEY=your_jwt_secret
DB_PATH=app.db
QDRANT_URL=http://localhost:6333
```

### 3. Backend Installation

1. Navigate to the root directory
2. Create and activate a virtual environment:
   ```bash
   uv venv
   # On Windows
   .venv\Scripts\activate
   # On Mac/Linux
   source .venv/bin/activate
   ```
3. Install Python dependencies:
   ```bash
   uv add -r requirements.txt
   ```
4. Start the FastAPI Development Server:
   ```bash
   uv run uvicorn main:app --reload
   ```
   *The backend will be available at `http://localhost:8000`*

### 4. Frontend Installation

1. Navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Start the Next.js Development Server:
   ```bash
   npm run dev
   ```
   *The frontend will be available at `http://localhost:3000`*

---

## Usage

1. **Sign up/Login**: Create an account on the local instance.
2. **New Chat**: Click `+ New Chat` in the sidebar.
3. **Upload Context**: Click the `+` button next to the chat input to upload a PDF.
4. **Chat**: Once the PDF is processed, begin asking questions. The LLM will perform similarity search against the Qdrant DB and stream back its responses flawlessly!

---

## Architecture Note

The frontend and backend communicate asynchronously using JSON via Fetch wrapping standard async events. Streaming queries are pushed to the client using **Server-Sent Events (SSE)**.
The `langgraph` state engine manages conversation memory directly inside SQLite allowing multi-turn conversations to span seamlessly between sessions.