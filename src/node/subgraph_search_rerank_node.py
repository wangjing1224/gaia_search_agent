from src.state.subgraph_search_state import SubgraphSearchState
from langchain_core.messages import ToolMessage

def subgraph_search_rerank_node(state: SubgraphSearchState):
    # 这里可以添加重新排序的逻辑
    search_content = state["search_results"]
        
    reranked_content = f"Reranked Results based on: {search_content}"
    
    return {
        "reranked_results": reranked_content,
    }