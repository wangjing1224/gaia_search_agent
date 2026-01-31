from src.state.subgraph_search_state import SubgraphSearchState

def subgraph_search_rerank_node(state: SubgraphSearchState):
    # 这里可以添加重新排序的逻辑
    # 目前只是简单地返回原始消息
    messages = state["messages"]
    return {"messages": messages}