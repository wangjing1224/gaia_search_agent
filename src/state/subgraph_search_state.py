from langgraph.graph import MessagesState
from src.state.search_result import SearchResult
from typing import Annotated, List, Union, Literal

import operator

# 自定义一个reducer函数，用于管理search_results的状态更新，不仅可追加，还可以进行清空
def search_results_reducer(current: List[SearchResult], update: Union[List[SearchResult], str]) -> List[SearchResult]:
    if update == "clear":
        return []
    else:
        return current + update

class SubgraphSearchState(MessagesState):
    # 这里可以添加特定于子图搜索的状态字段
    current_query: str
    
    search_results: Annotated[List[SearchResult], search_results_reducer]
    
    reranked_results: List[SearchResult]
    
    summary: str