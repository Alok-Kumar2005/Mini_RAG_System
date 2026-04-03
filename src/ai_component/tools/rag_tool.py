import asyncio
from typing import Annotated, Type, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langgraph.prebuilt import InjectedState
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
            
            await asyncio.sleep(1) 
            logging.info("PDF Search completed")
            return f"The uploaded document states that LangGraph makes Agentic RAG very easy to build. (Session: {session_id})"
            
        except Exception as e:
            logging.error(f"Error in PDF Search Tool: {str(e)}")
            return f"Sorry, I encountered an error while searching the document: {str(e)}"

    def _run(self, query: str, state: Dict[str, Any]) -> str:
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._arun(query, state))
        except Exception as e:
            logging.error(f"Error in PDF Search Tool sync method: {str(e)}")
            return f"Sorry, I encountered an error: {str(e)}"

pdf_search_tool = PDFSearchTool()