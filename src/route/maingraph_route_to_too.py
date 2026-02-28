from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage

from src.state.state import AgentState

def route_to_tool(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    thinking_process_is_error = state.get("thinking_process_is_error", None)
    
    if thinking_process_is_error is not None:
        if thinking_process_is_error:
            return "agent"  # 思维过程有误，进入 Agent 思考
        else:
            return "skills_load_node"  # 思维过程正确，加载的技能有误,重新进入技能加载节点
    
    # 检查最后一条消息是否包含 ToolCall
    if not last_message.tool_calls:
        return END  # 没有 ToolCall，结束对话
    
    # 有 ToolCall,获取工具名称
    tool_name = last_message.tool_calls[0]["name"]
    
    # 根据工具名称路由到对应的工具节点
    if tool_name == "search_interface":
        return "search_subgraph_node"
    elif tool_name == "code_execution_repl":
        return "async_tools_execution_node"
    
    return END  # 默认结束