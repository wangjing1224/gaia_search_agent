from langchain_core.tools import tool
from pydantic import BaseModel, Field

class search_interface_args(BaseModel):
    query: str = Field(..., description="The search query.")
    depth: str = Field(..., description="The depth of the search. Options are 'brief' or 'detailed'.", default="brief")
    
@tool('search_interface', args_schema=search_interface_args)
def search_interface(query: str, depth: str = "brief") -> str:
    """
    Perform a web search with specified depth.
    When user's query is related to web search, use this tool to fetch relevant information.
    Do not make up search results. Always use this tool for web search related queries.
    
    Args:
        query: The search query.
        depth: The depth of the search. Options are 'brief' or 'detailed'. Default is 'brief'.
    Returns:
        The search results.
    """
    # This is a placeholder implementation.
    # Replace with actual search logic as needed.
    if depth == "detailed":
        return f"Detailed search results for query: {query}"
    else:
        return f"Brief search results for query: {query}"