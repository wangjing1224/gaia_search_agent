import json
import asyncio
from langchain_core.messages import ToolMessage
from src.subgraph.search_subgraph import create_subgraph_search_graph
from src.state.state import AgentState

#实例化子图搜索图
search_graph = create_subgraph_search_graph()

async def search_graph_wrapper_node(state: AgentState):
    
    # 解析主脑发出的 ToolCall (获取参数)
    last_message = state["messages"][-1]
    
    if not last_message.tool_calls:
        return {"messages": []}  # 没有工具调用，返回空消息列表
    
    tasks = []
    tool_call_map = []
    
    for tool_call in last_message.tool_calls:
        # 获取工具调用参数
        query = tool_call["args"].get("query", "")
        background = tool_call["args"].get("background", "")
        user_message = f"Search specifically for: {query}\nThe query background: {background}"
        tool_call_map.append(tool_call)
        
        if query:
            # 准备子图输入
            subgraph_input = {
                "current_query": query,
                "messages": [("user", user_message)],
                "search_results": [],  # 初始没有搜索结果，交给子图去
                "rerank_results": [],  # 初始没有重排序结果，交给子图去
                "summary": ""
            }
            tasks.append(search_graph.ainvoke(subgraph_input))
    
    # 并发执行子图任务
    print(f"Executing {len(tasks)} search graph calls concurrently...")
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 处理子图返回结果
    return_messages = []
    for i, result in enumerate(results):
        tool_call = tool_call_map[i]
        
        if isinstance(result, Exception):
            tool_content = f"Search Graph Execution Error: {str(result)}"
        else:
            subgraph_return_messages = result.get("summary","")
            tool_content = f"Search results summary: {subgraph_return_messages}"
        
        # 构造新的 ToolMessage
        new_tool_message = ToolMessage(
            content=tool_content,
            tool_call_id = tool_call["id"],
            name = tool_call["name"],
        )
        return_messages.append(new_tool_message)
        
    return {"messages": return_messages}
    
    