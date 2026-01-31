# src/graph.py
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from src.state.state import AgentState
from src.node.nodes import call_model
from src.tools.search import get_tools
from src.interface_tools.search_interface import search_interface
from src.node.search_graph_wrapper_node import search_graph_wrapper_node

def route_to_tool(state):
    messages = state["messages"]
    last_message = messages[-1]
    
    # 检查最后一条消息是否包含 ToolCall
    if not last_message.tool_calls:
        return END  # 没有 ToolCall，结束对话
    
    # 有 ToolCall,获取工具名称
    tool_name = last_message.tool_calls[0]["name"]
    
    # 根据工具名称路由到对应的工具节点
    if tool_name == "search_interface":
        return "search_subgraph_node"
    
    return END  # 默认结束
    
    
def create_graph():
    # 1. 初始化 Graph Builder
    workflow = StateGraph(AgentState)

    # 2. 添加节点
    # Agent 思考节点
    workflow.add_node("agent", call_model)
    
    # 搜索工具节点
    workflow.add_node("search_subgraph_node", search_graph_wrapper_node)
    
    # 工具执行节点 (使用 LangGraph 预构建的 ToolNode)
    tools = [search_interface]
    tool_node = ToolNode(tools)
    workflow.add_node("tools", tool_node)

    # 3. 添加边 (Edges)
    # 起点 -> Agent
    workflow.add_edge(START, "agent")

    # 条件边：Agent 决定是 "结束" 还是 "调用工具"
    workflow.add_conditional_edges(
        "agent",
        route_to_tool,
        {
            "search_subgraph_node": "search_subgraph_node",
            END: END,
        }
    )

    # 工具执行完 -> 回到 Agent 继续思考
    workflow.add_edge("search_subgraph_node", "agent")

    # 4. 编译图
    # 这里可以使用 MemorySaver 实现长对话记忆，但为了最简启动暂不加
    graph = workflow.compile()
    
    return graph