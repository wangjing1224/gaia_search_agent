from langchain_core.messages import ToolMessage
from src.tools.tavily_tool import web_search_Tavily
from src.state.subgraph_search_state import SubgraphSearchState

def subgraph_search_tools_execution_node(state: SubgraphSearchState):
    messages = state["messages"]
    last_message = messages[-1]
    
    if isinstance(last_message, ToolMessage):
        # 提取工具调用信息
        tool_call_id = last_message.tool_call_id
        tool_name = last_message.name
        tool_args = last_message.content  # 假设内容包含参数信息
        
        # 这里只处理 web_search_Tavily 工具作为示例
        if tool_name == "web_search_Tavily":
            # 调用工具
            search_results = web_search_Tavily.invoke({"query": tool_args})
            
            fake_tool_content = f"Search executed successfully. Found relevant results for query: {tool_args}. Data has been stored in 'raw_search_results'."
            
            # 创建新的 ToolMessage 作为工具输出
            tool_msg = ToolMessage(
                content=fake_tool_content,
                tool_call_id=tool_call_id,
                name=tool_name,
            )
            
    
    return {
        "messages": [tool_msg],
        "search_results": search_results
    }