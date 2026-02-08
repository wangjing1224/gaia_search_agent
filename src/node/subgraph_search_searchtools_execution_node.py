import asyncio

from langchain_core.messages import ToolMessage
from src.state.subgraph_search_state import SubgraphSearchState
from src.state.search_result import SearchResult

from src.tools.arxiv_search_tool import paper_search_arxiv
from src.tools.bocha_search_tool import web_search_bocha
from src.tools.pubmed_search_tool import paper_search_pubmed
from src.tools.serpapi_search_tool import web_search_serpapi

from typing import List

tools_map = {
    "paper_search_arxiv": paper_search_arxiv,
    "web_search_bocha": web_search_bocha,
    "paper_search_pubmed": paper_search_pubmed,
    "web_search_serpapi": web_search_serpapi
}

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
            if tool_call["name"] in tools_map:
                task = tools_map[tool_call["name"]].ainvoke(tool_args)
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
                
                current_results: List[SearchResult] = []
                
                # 处理异常情况
                if isinstance(result, Exception):
                    error_result:SearchResult = {
                        "title": "Tool Execution Error",
                        "content": f"Error executing tool {tool_call['name']}: {str(result)}",
                        "url": "None",
                        "source": "System"
                    }
                    current_results.append(error_result)
                    fake_tool_content = f"Tool {tool_call['name']} execution failed."
                else:
                    # 正常结果处理
                    if isinstance(result, list):
                        # 工具返回的是结果列表
                        current_results = result
                    else:
                        # 防止工具返回非列表结果
                        current_results = []
                    fake_tool_content = f"Tool {tool_call['name']} executed successfully."
                # 汇总搜索结果
                search_results_list.extend(current_results)
                
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