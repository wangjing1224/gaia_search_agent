import asyncio

from langchain_core.messages import ToolMessage

from src.state.state import State
from src.tools.repl_tool import code_execution_repl
from src.interface_tools.search_interface import search_interface

tools_map = {
    "code_execution_repl": code_execution_repl,
    "search_interface": search_interface
}

async def maingraph_asytools_execution_node(state: State):
    messages = state["messages"]
    last_message = messages[-1]
    
    new_message = []
    
    if last_message.tool_calls and hasattr(last_message, "tool_calls"):
        
        tasks = []
        
        for tool_call in last_message.tool_calls:
            # 获取工具调用参数
            tool_args = tool_call["args"]
            
            # 根据工具名称调用相应的工具
            if tool_call["name"] in tools_map:
                task = tools_map[tool_call["name"]].ainvoke(tool_args)
                tasks.append(task)
            
            else:
                pass  # 未知工具，忽略
            
        # 并发执行任务，并收集结果
        if tasks:
            print(f"Executing {len(tasks)} tool calls concurrently...")
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                tool_call = last_message.tool_calls[i]
                
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
            new_message.append(new_tool_message)
    
    return{
        "messages": new_message
    }