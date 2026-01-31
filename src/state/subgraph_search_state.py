from langgraph.graph import MessagesState
from typing import Annotated, List, Union, Literal

class SubgraphSearchState(MessagesState):
    # 这里可以添加特定于子图搜索的状态字段
    current_query: str
    
    search_results: str
    
    reranked_results: str
    
    summary: str