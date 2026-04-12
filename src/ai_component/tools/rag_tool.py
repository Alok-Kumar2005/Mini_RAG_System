import asyncio
from typing import Annotated, Type, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langgraph.prebuilt import InjectedState
from src.backend.ingestion import get_embedder, get_qdrant

from src.logger import logging


class PDFSearchInput(BaseModel):
    query: str = Field(..., description="The query to search within the uploaded PDF document.")
    state: Annotated[dict, InjectedState]


class PDFSearchTool(BaseTool):
    name: str = "search_pdf_tool"
    description: str = """Use this tool to search the uploaded PDF document for information to answer the user's question."""
    args_schema: Type[BaseModel] = PDFSearchInput

    async def _arun(self, query: str, state: Dict[str, Any]) -> str:
        try:
            session_id = state.get("session_id")

            if not session_id:
                return "Error: No active document session found. Please upload a PDF first."

            logging.info(f"[PDFSearchTool] Query: '{query}' | Session: '{session_id}'")

            embedder = get_embedder()
            query_vector = await asyncio.to_thread(
                embedder.embed_query,
                query,
            )

            client = get_qdrant()
            results = await client.query_points(
                collection_name=session_id,
                query=query_vector,
                limit=5,
                with_payload=True,
            )

            points = list(results.points)

            if not points:
                return "No relevant information found in the document."

            context_parts = [
                f"[Score: {round(hit.score, 3)}]\n{hit.payload.get('text', '')}"
                for hit in points
                if hit.payload and "text" in hit.payload
            ]

            if not context_parts:
                return "No relevant information found in the document."

            context = "\n\n---\n\n".join(context_parts)
            logging.info(f"[PDFSearchTool] Retrieved {len(context_parts)} chunks")
            return f"Relevant excerpts from the document:\n\n{context}"

        except Exception as e:
            logging.error(f"[PDFSearchTool] Error: {e!r}")
            return "Something went wrong while searching the document."

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Use async version of this tool.")


pdf_search_tool = PDFSearchTool()