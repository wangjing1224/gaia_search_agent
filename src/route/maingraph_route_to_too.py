from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage

from src.state.state import AgentState

def route_to_tool(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    
    # 检查最后一条消息是 HumanMessage
    if isinstance(last_message, HumanMessage):
        return "agent"  # 如果最后一条消息是用户输入，继续让 Agent 思考，而不是直接结束
    
    if not getattr(last_message, "tool_calls", None):
        return END  # 没有 ToolCall，结束对话
    
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
    elif tool_name == "load_skill":
        return "tools"
    
    return END  # 默认结束