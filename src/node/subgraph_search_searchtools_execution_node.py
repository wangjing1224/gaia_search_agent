from langchain_core.messages import ToolMessage
from src.tools.tavily_tool import web_search_Tavily
from src.state.subgraph_search_state import SubgraphSearchState

def subgraph_search_tools_execution_node(state: SubgraphSearchState):
    messages = state["messages"]
    last_message = messages[-1]
    
    new_message = []
    search_results_list = []
    
    if last_message.tool_calls:
        
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]
            
            if tool_name == "web_search_Tavily":
                query = tool_args.get("query", "")
                
                search_results = web_search_Tavily.invoke(query)
                
                search_results_list.append(search_results)
                
                fake_tool_content = f"Search executed successfully for query: {tool_args.get('query')}. Data stored in internal state."
                
                tool_msg = ToolMessage(
                    content=fake_tool_content,
                    tool_call_id=tool_id,
                    name=tool_name,
                )
                
                new_message.append(tool_msg)
            else:
                pass  # 未知工具，忽略
            
    
    return {
        "messages": new_message,
        "search_results": "\n\n".join(search_results_list)
    }