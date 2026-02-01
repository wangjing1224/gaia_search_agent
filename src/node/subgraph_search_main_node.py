from src.llm.model import get_llm
from src.tools.tavily_tool import web_search_Tavily
from src.tools.wikipedia_search_tool import wikipedia_search_tool
from src.state.subgraph_search_state import SubgraphSearchState

from langchain_core.messages import SystemMessage

llm = get_llm()

tools = [web_search_Tavily, wikipedia_search_tool]

def subgraph_search_main_node(state: SubgraphSearchState):
    messages = state["messages"]
    reranked_results = state.get("reranked_results", [])
    
    # 拼接rerank结果
    reranked_results_str = ""
    for i, res in enumerate(reranked_results):
        title = res.get("title","")
        url = res.get("url","")
        content = res.get("content","")
        source = res.get("source","")
        reranked_results_str += f"{i+1}. Title: {title}\n   URL: {url}\n   Content: {content}\n   Source: {source}\n\n"
    
    SEARCH_SYSTEM_PROMPT = f"""
    You are a expert of searching the web for information to help answer user queries.
    Your goal is to find the most relevant and accurate information from the web based on the user's query.
    1.If the search results are not resilient enough, you may try another search with modified query or increased depth.
    2.Please read the search results carefully 
    3.Summarize the key points from the search results to help answer the user's query.
    Here are the reranked search results:
    {reranked_results_str}
    """
    
    # 1. 准备系统提示和消息
    system_message = SystemMessage(content=SEARCH_SYSTEM_PROMPT)
    # 2. 绑定工具到语言模型
    llm_with_tools = llm.bind_tools(tools)
    # 3. 调用 LLM + 工具
    response = llm_with_tools.invoke([system_message] + messages)
    
    if not response.tool_calls:
        return {
            "messages": [response],
            "summary" :response.content
        }
    
    return {"messages": [response]}