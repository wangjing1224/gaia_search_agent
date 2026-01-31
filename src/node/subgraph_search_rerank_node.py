from src.state.subgraph_search_state import SubgraphSearchState
from langchain_core.messages import ToolMessage

def subgraph_search_rerank_node(state: SubgraphSearchState):
    # 这里可以添加重新排序的逻辑
    messages = state["messages"]
    last_message = messages[-1]
    
    if isinstance(last_message,ToolMessage) :
        # 简单讲检索的内容取出来，再放回去
        search_content = last_message.content
        
        reranked_content = f"Reranked Results based on: {search_content}"
        
        return {
            "search_results": search_content,
            "reranked_results": reranked_content,
        }
    
    return {}