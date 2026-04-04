import asyncio
from typing import Annotated, Type, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langgraph.prebuilt import InjectedState
from src.backend.ingestion import get_embedder, get_qdrant

from src.logger import logging
from src.exceptions import CustomException

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

            logging.info(f"Running PDF Search tool with query: '{query}' on session: '{session_id}'")
            
            # vector database logic
            embedder = get_embedder()
            query_vector = await asyncio.to_thread(
                embedder.encode,
                [query],
                show_progress_bar=False
            )
            query_vector = query_vector[0].tolist()

            client = get_qdrant()
            results = await client.search(
                collection_name=session_id,
                query_vector=query_vector,
                limit=5,
                with_payload=True,
            )

            if not results:
                return "No relevant information found in the document."
            
            context_parts = [
                f"[Score: {round(hit.score, 3)}]\n{hit.payload.get('text', '')}"
                for hit in results
                if hit.payload and "text" in hit.payload
            ]

            context = "\n\n---\n\n".join(context_parts)

            logging.info(f"[PDFSearchTool] Retrieved {len(results)} chunks")

            return f"Relevant excerpts from the document:\n\n{context}"

        except Exception as e:
            logging.error(f"[PDFSearchTool] Error: {e}")
            return "Something went wrong while searching the document."

    def _run(self, query: str, state: Dict[str, Any]) -> str:
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._arun(query, state))
        except Exception as e:
            logging.error(f"Error in PDF Search Tool sync method: {str(e)}")
            return f"Sorry, I encountered an error: {str(e)}"

pdf_search_tool = PDFSearchTool()