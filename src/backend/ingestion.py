import io
import uuid
import asyncio
from typing import List

from pypdf import PdfReader
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

from src.utils import utils
from src.logger import logging


# -----------------------------
# GLOBAL SINGLETONS
# -----------------------------
_embedder: SentenceTransformer | None = None
_qdrant: AsyncQdrantClient | None = None


def get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        logging.info(f"Loading embedding model: {utils.EMBEDDING_MODEL}")
        _embedder = SentenceTransformer(utils.EMBEDDING_MODEL)
    return _embedder


def get_qdrant() -> AsyncQdrantClient:
    global _qdrant
    if _qdrant is None:
        _qdrant = AsyncQdrantClient(
            url=utils.QDRANT_URL,
            api_key=utils.QDRANT_API_KEY,
        )
    return _qdrant


# -----------------------------
# TEXT CHUNKING
# -----------------------------
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


# -----------------------------
# PDF INGESTION PIPELINE
# -----------------------------
async def ingest_pdf(file_bytes: bytes, session_id: str) -> int:
    try:
        # -----------------------------
        # Extract text from PDF
        # -----------------------------
        reader = PdfReader(io.BytesIO(file_bytes))

        texts = []
        for page in reader.pages:
            texts.append(page.extract_text() or "")

        full_text = "\n".join(texts)

        if not full_text.strip():
            raise ValueError("Could not extract any text from the PDF.")

        # -----------------------------
        # Chunking
        # -----------------------------
        chunks = chunk_text(full_text)
        logging.info(f"[Ingestion] {len(chunks)} chunks created for session {session_id}")

        # -----------------------------
        # Embedding (NON-BLOCKING)
        # -----------------------------
        embedder = get_embedder()

        vectors = await asyncio.to_thread(
            embedder.encode,
            chunks,
            show_progress_bar=False
        )
        vectors = vectors.tolist()

        # -----------------------------
        # Qdrant setup
        # -----------------------------
        client = get_qdrant()

        # Dynamically detect embedding dimension
        embedding_dim = len(vectors[0])

        # Create collection if not exists
        try:
            await client.get_collection(session_id)
        except Exception:
            await client.create_collection(
                collection_name=session_id,
                vectors_config=VectorParams(
                    size=embedding_dim,
                    distance=Distance.COSINE,
                ),
            )
            logging.info(f"[Ingestion] Created Qdrant collection: {session_id}")

        # -----------------------------
        # Prepare points
        # -----------------------------
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vec,
                payload={
                    "text": chunk,
                    "chunk_index": i,
                    "session_id": session_id,
                },
            )
            for i, (chunk, vec) in enumerate(zip(chunks, vectors))
        ]

        # -----------------------------
        # Upsert to Qdrant
        # -----------------------------
        try:
            await client.upsert(
                collection_name=session_id,
                points=points
            )
        except Exception as e:
            logging.error(f"[Ingestion] Qdrant upsert failed: {e}")
            raise

        logging.info(f"[Ingestion] Upserted {len(points)} points into '{session_id}'")

        return len(points)

    except Exception as e:
        logging.error(f"[Ingestion] Failed for session {session_id}: {e}")
        raise