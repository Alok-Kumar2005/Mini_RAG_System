from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from src.utils import utils
import os

os.environ['TAVILY_API_KEY'] = utils.TAVILY_API_KEY

_tavily = TavilySearch(max_results=5, topic="general")

@tool("tavily_search", description="Search the internet for current information on any topic.")
async def web_tool(query: str) -> str:
    return await _tavily.ainvoke(query)