# src/graph.py
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from src.state.state import AgentState
from src.node.nodes import call_model
from src.node.maingraph_skills_load_node import maingraph_skills_load_node
from src.tools.load_skill_tool import load_skill
from src.node.search_graph_wrapper_node import search_graph_wrapper_node
from src.node.maingraph_asytools_execution_node import maingraph_asytools_execution_node
from src.route.maingraph_route_to_too import route_to_tool
from src.route.maingraph_skills_load_node_route_to_tool import maingraph_skills_load_node_route_to_tool
    
    
def create_graph():
    # 1. 初始化 Graph Builder
    workflow = StateGraph(AgentState)

    # 2. 添加节点
    # 技能加载节点
    workflow.add_node("skills_load_node", maingraph_skills_load_node)
    
    # Agent 思考节点
    workflow.add_node("agent", call_model)
    
    # 搜索工具节点
    workflow.add_node("search_subgraph_node", search_graph_wrapper_node)
    
    # 异步工具执行节点
    workflow.add_node("async_tools_execution_node", maingraph_asytools_execution_node)
    
    # 工具执行节点 (使用 LangGraph 预构建的 ToolNode)
    tools = [load_skill]
    tool_node = ToolNode(tools)
    workflow.add_node("tools", tool_node)

    # 3. 添加边 (Edges)
    
    # 起点 -> 技能加载节点
    workflow.add_edge(START, "skills_load_node")
    
    # 条件边：技能加载节点决定是用工具还是进入 Agent 思考
    workflow.add_conditional_edges(
        "skills_load_node",
        maingraph_skills_load_node_route_to_tool,
        {
            "agent": "agent",  # 继续思考
            "tools": "tools",  # 进入工具执行节点
        }
    )

    # 条件边：Agent 决定是 "结束" 还是 "调用工具"
    workflow.add_conditional_edges(
        "agent",
        route_to_tool,
        {
            "search_subgraph_node": "search_subgraph_node",
            "async_tools_execution_node": "async_tools_execution_node",
            "agent": "agent",  # 继续思考
            "skills_load_node": "skills_load_node",  # 重新加载技能
            END: END,
        }
    )

    # 工具执行完 -> 回到 Agent 继续思考
    workflow.add_edge("search_subgraph_node", "agent")
    workflow.add_edge("async_tools_execution_node", "agent")
    workflow.add_edge("tools", "agent")
    
    # 4. 编译图
    # 这里可以使用 MemorySaver 实现长对话记忆，但为了最简启动暂不加
    graph = workflow.compile()
    
    return graph