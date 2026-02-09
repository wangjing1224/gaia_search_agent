from langchain_core.tools import tool
from pydantic import BaseModel, Field

class search_interface_args(BaseModel):
    query: str = Field(..., description="The search query string. KEYWORDS only. Avoid conversational filler. Example: 'Tesla stock price 2023' instead of 'Please tell me what the stock price of Tesla was in 2023'.")
    
@tool('search_interface', args_schema=search_interface_args)
def search_interface(query: str) -> str:
    """
    Primary web search tool. Use this for:
    1. Finding current events, news, or specific facts (dates, names).
    2. Verifying information.
    3. Answering questions about entities not in your internal knowledge.
    
    Use specific, high-value keywords.
    
    Args:
        query: The search query string. KEYWORDS only. Avoid conversational filler. Example: 'Tesla stock price 2023' instead of 'Please tell me what the stock price of Tesla was in 2023'.
    Returns:
        The search results.
    """
    
    # 这里我们不直接实现搜索逻辑，而是将查询传递给子图中的工具执行节点，由那里来调用具体的搜索工具。
    # 这样可以保持接口的简洁，同时利用子图的能力来处理复杂的工具调用和结果整合。
    return ""