from langgraph.graph import StateGraph, START, END

from src.state.subgraph_search_state import SubgraphSearchState

def route_to_search_tool(state: SubgraphSearchState):
    messages = state["messages"]
    last_message = messages[-1]
    
    # 检查最后一条消息是否包含 ToolCall
    if not last_message.tool_calls:
        return END  # 没有 ToolCall，结束子图搜索
    
    # 有 ToolCall,获取工具名称
    tool_name = last_message.tool_calls[0]["name"]
    
    # 根据工具名称路由到对应的工具节点
    if tool_name == "paper_search_arxiv" or tool_name == "web_search_bocha" or tool_name == "paper_search_pubmed" or tool_name == "web_search_serpapi":
        return "search_tools_execution_node"
    
    elif tool_name == "web_read_jina":
        return "web_read_tools_execution_node"
    
    else:
        return END # 未知工具，结束子图搜索