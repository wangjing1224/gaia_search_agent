import json
from langchain_core.messages import ToolMessage
from src.subgraph.search_subgraph import create_subgraph_search_graph

#实例化子图搜索图
search_graph = create_subgraph_search_graph()

async def search_graph_wrapper_node(state):
    
    # 1.解析主脑发出的 ToolCall (获取参数)
    last_message = state["messages"][-1]
    tool_call = last_message.tool_calls[0]# 假设只有一个 ToolCall
    
    # 2.准备子图输入
    query = tool_call["args"]["query"]
    subgraph_input = {
        "original_query": query,
        "messages": [],
    }
    
    # 3.调用子图
    subgraph_output = await search_graph.ainvoke(subgraph_input)
    
    # 4.处理子图输出
    subgraph_return_messages = subgraph_output.get("final_summary_messages","Search completed.")
    
    # 5.将子图返回的消息封装为 ToolMessage
    tool_msg = ToolMessage(
        content=subgraph_return_messages,
        tool_call_id = tool_call["id"],
        name = tool_call["name"],
    )
    
    return {"messages": [tool_msg]}
    