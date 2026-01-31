from src.node.subgraph_search_main_node import subgraph_search_main_node
from src.node.subgraph_search_rerank_node import subgraph_search_rerank_node
from src.state.subgraph_search_state import SubgraphSearchState
from src.tools.tavily_tool import web_search_Tavily
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

def create_subgraph_search_graph():
    # 1. 初始化 Graph Builder
    workflow = StateGraph(SubgraphSearchState)

    # 2. 添加节点
    # 子图搜索主节点
    workflow.add_node("subgraph_search_main", subgraph_search_main_node)
    
    # 重新排序节点
    workflow.add_node("subgraph_search_rerank", subgraph_search_rerank_node)
    
    #工具执行节点
    tools = [web_search_Tavily]
    tool_node = ToolNode(tools)
    workflow.add_node("tools", tool_node)

    # 3. 添加边 (Edges)
    # 起点 -> 子图搜索主节点
    workflow.add_edge(START, "subgraph_search_main")
    
    # 条件边：子图搜索主节点 决定是 "结束" 还是 "调用工具"
    workflow.add_conditional_edges(
        "subgraph_search_main",
        tools_condition,
    )

    # 工具执行节点 -> 重新排序节点
    workflow.add_edge("tools", "subgraph_search_rerank")

    # 重新排序节点 -> 子图搜索主节点
    workflow.add_edge("subgraph_search_rerank", "subgraph_search_main")

    # 4. 编译图
    graph = workflow.compile()
    
    return graph