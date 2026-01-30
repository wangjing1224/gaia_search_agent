# src/graph.py
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from src.state.state import AgentState
from src.node.nodes import call_model
from src.tools.search import get_tools

def create_graph():
    # 1. 初始化 Graph Builder
    workflow = StateGraph(AgentState)

    # 2. 添加节点
    # Agent 思考节点
    workflow.add_node("agent", call_model)
    
    # 工具执行节点 (使用 LangGraph 预构建的 ToolNode)
    tools = get_tools()
    tool_node = ToolNode(tools)
    workflow.add_node("tools", tool_node)

    # 3. 添加边 (Edges)
    # 起点 -> Agent
    workflow.add_edge(START, "agent")

    # 条件边：Agent 决定是 "结束" 还是 "调用工具"
    workflow.add_conditional_edges(
        "agent",
        tools_condition,
    )

    # 工具执行完 -> 回到 Agent 继续思考
    workflow.add_edge("tools", "agent")

    # 4. 编译图
    # 这里可以使用 MemorySaver 实现长对话记忆，但为了最简启动暂不加
    graph = workflow.compile()
    
    return graph