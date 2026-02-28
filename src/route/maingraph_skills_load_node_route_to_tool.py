from src.state.state import AgentState

def maingraph_skills_load_node_route_to_tool(state: AgentState):
    skills_load_messages = state["skills_load_messages"][-1]
    
    if not skills_load_messages.tool_calls:
        return "agent"  # 没有工具调用，继续进入 Agent 思考 
    
    return "tools"  # 有工具调用，进入工具执行节点