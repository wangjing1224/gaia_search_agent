from langgraph.graph import MessagesState
from src.state.search_result import SearchResult
from typing import Annotated, List, Union, Literal

import operator

class SubgraphSearchState(MessagesState):
    # 这里可以添加特定于子图搜索的状态字段
    current_query: str
    
    search_results: Annotated[List[SearchResult],operator.add]
    
    reranked_results: List[SearchResult]
    
    summary: str