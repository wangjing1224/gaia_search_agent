import asyncio

from langchain_core.messages import ToolMessage
from src.tools.tavily_tool import web_search_Tavily
from src.state.subgraph_search_state import SubgraphSearchState
from src.tools.wikipedia_search_tool import web_search_wikipedia

async def subgraph_search_tools_execution_node(state: SubgraphSearchState):
    messages = state["messages"]
    last_message = messages[-1]
    
    new_message = []
    search_results_list = []
    
    if last_message.tool_calls and hasattr(last_message, "tool_calls"):
        
        tasks = []
        tool_call_map = []
        
        for tool_call in last_message.tool_calls:
            # 获取工具调用参数
            tool_args = tool_call["args"]
            
            # 根据工具名称调用相应的工具
            if tool_call["name"] == "web_search_Tavily":
                # 异步调用工具
                task = web_search_Tavily.ainvoke(tool_args.get("query",""))
                tasks.append(task)
                tool_call_map.append(tool_call)
            
            elif tool_call["name"] == "web_search_wikipedia":
                task = web_search_wikipedia.ainvoke(tool_args.get("query",""))
                tasks.append(task)
                tool_call_map.append(tool_call)
            
            else:
                pass  # 未知工具，忽略
            
            # 并发执行任务，并收集结果
            if tasks:
                print(f"Executing {len(tasks)} tool calls concurrently...")
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, result in enumerate(results):
                    tool_call = tool_call_map[i]
                    
                    # 处理异常情况
                    if isinstance(result, Exception):
                        print(f"Tool {tool_call['name']} execution failed: {result}")
                        result_content = [{"source": tool_call['name'], "content": f"Error: {str(result)}", "title": "Error", "url": ""}]
                        result_content = result
                    
                    # 收集搜索结果
                    if isinstance(result_content, list):
                        search_results_list.extend(result_content)
                    else:
                        search_results_list.append(result_content)
                    
                    # 构造 ToolMessage
                    fake_tool_content = f"Tool {tool_call['name']} executed successfully."
                    tool_message = ToolMessage(
                        content=fake_tool_content,
                        tool_call_id=tool_call["id"],
                        name=tool_call["name"], 
                    )
                    
                    new_message.append(tool_message)
                    
    # 返回包含工具调用结果的新消息列表和搜索结果        
    return {
        "messages": new_message,
        "search_results": search_results_list
    }