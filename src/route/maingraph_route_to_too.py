from langgraph.graph import StateGraph, START, END

from src.state.state import AgentState

def route_to_tool(state: AgentState):
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