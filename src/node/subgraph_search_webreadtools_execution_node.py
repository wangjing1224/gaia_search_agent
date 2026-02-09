import asyncio

from langchain_core.messages import ToolMessage
from src.state.subgraph_search_state import SubgraphSearchState

from src.tools.jinreader_read_tool import web_read_jina

tools_map = {
    "web_read_jina": web_read_jina
}

async def subgraph_search_webreadtools_execution_node(state: SubgraphSearchState):
    last_message = state["messages"][-1]
    
    return_tool_messages = []
    
    if last_message.tool_calls and hasattr(last_message, "tool_calls"):
        
        tasks = []
        tool_call_map = []
        
        for tool_call in last_message.tool_calls:
            # 获取工具调用参数
            tool_args = tool_call["args"]
            
            # 根据工具名称调用相应的工具
            if tool_call["name"] in tools_map:
                task = tools_map[tool_call["name"]].ainvoke(tool_args)
                tasks.append(task)
                tool_call_map.append(tool_call)
            
            else:
                pass  # 未知工具，忽略
            
        # 并发执行任务，并收集结果
        if tasks:
            print(f"Executing {len(tasks)} web reading tool calls concurrently...")
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                tool_call = tool_call_map[i]
                
                tool_content = ""
                
                # 处理异常情况
                if isinstance(result, Exception):
                    tool_content = f"Tool Execution Error: {str(result)}"
                else:
                    # 正常结果
                    if isinstance(result, str):
                        # 如果结果是字符串，直接使用
                        tool_content = result
            
            # 构造新的 ToolMessage
            new_tool_message = ToolMessage(
                content=tool_content,
                tool_call_id = tool_call["id"],
                name = tool_call["name"],
            )
            
            return_tool_messages.append(new_tool_message)
    
    return {
        "messages": return_tool_messages  # 将新的 ToolMessage 添加到状态中
    }
                    
    