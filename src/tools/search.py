# src/tools/search.py
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool

def get_tools():
    """
    返回工具列表
    """
    # max_results=3 避免上下文过长
    search_tool = TavilySearchResults(max_results=3)
    return [search_tool]