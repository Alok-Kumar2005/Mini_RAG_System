import os
from langchain_tavily import TavilySearch
from src.utils import utils


os.environ['TAVILY_API_KEY'] = utils.TAVILY_API_KEY

web_tool = TavilySearch(
    name="tavily_search",
    max_results=5,
    topic="general",
)