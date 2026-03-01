from src.state.state import AgentState

def maingraph_skills_load_node_route_to_tool(state: AgentState):
    skills_load_messages = state["skills_load_messages"][-1]
    
    # 如果技能加载消息中包含工具调用，则路由到工具执行节点，否则继续进入 Agent 思考节点
    if hasattr(skills_load_messages, "tool_calls") and skills_load_messages.tool_calls:
        return "tools"
    
    return "agent"