from src.node.subgraph_search_main_node import subgraph_search_main_node
from src.node.subgraph_search_rerank_node import subgraph_search_rerank_node
from src.node.subgraph_search_searchtools_execution_node import subgraph_search_tools_execution_node
from src.state.subgraph_search_state import SubgraphSearchState
from src.tools.tavily_tool import web_search_Tavily
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

def route_to_search_tool(state: SubgraphSearchState):
    messages = state["messages"]
    last_message = messages[-1]
    
    # 检查最后一条消息是否包含 ToolCall
    if not last_message.tool_calls:
        return END  # 没有 ToolCall，结束子图搜索
    
    # 有 ToolCall,获取工具名称
    tool_name = last_message.tool_calls[0]["name"]
    
    # 根据工具名称路由到对应的工具节点
    if tool_name == "web_search_Tavily" or tool_name == "web_search_wikipedia":
        return "search_tools_execution_node"
    else:
        return "tools"
    

def create_subgraph_search_graph():
    # 1. 初始化 Graph Builder
    workflow = StateGraph(SubgraphSearchState)

    # 2. 添加节点
    # 子图搜索主节点
    workflow.add_node("subgraph_search_main", subgraph_search_main_node)
    
    # 重新排序节点
    workflow.add_node("subgraph_search_rerank", subgraph_search_rerank_node)
    
    #工具执行节点
    tools = []
    tool_node = ToolNode(tools)
    workflow.add_node("tools", tool_node)
    
    workflow.add_node("search_tools_execution_node", subgraph_search_tools_execution_node)

    # 3. 添加边 (Edges)
    # 起点 -> 子图搜索主节点
    workflow.add_edge(START, "subgraph_search_main")
    
    # 条件边：子图搜索主节点 决定是 "结束" 还是 "调用工具"
    workflow.add_conditional_edges(
        "subgraph_search_main",
        route_to_search_tool,
        {
            "search_tools_execution_node": "search_tools_execution_node",
            "tools": "tools",
            END: END,
        }
    )

    # 工具执行节点 -> 重新排序节点
    workflow.add_edge("tools", "subgraph_search_rerank")
    workflow.add_edge("search_tools_execution_node", "subgraph_search_rerank")

    # 重新排序节点 -> 子图搜索主节点
    workflow.add_edge("subgraph_search_rerank", "subgraph_search_main")

    # 4. 编译图
    graph = workflow.compile()
    
    return graph