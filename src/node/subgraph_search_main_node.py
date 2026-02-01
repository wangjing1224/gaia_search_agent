from src.llm.model import get_llm
from src.tools.tavily_tool import web_search_Tavily
from src.tools.wikipedia_search_tool import web_search_wikipedia
from src.state.subgraph_search_state import SubgraphSearchState

from langchain_core.messages import SystemMessage

llm = get_llm()

tools = [web_search_Tavily, web_search_wikipedia]

def subgraph_search_main_node(state: SubgraphSearchState):
    messages = state["messages"]
    
    original_query = state.get("current_query", "")
    
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
    You are a web search expert who answers user questions by finding accurate and matching information. You can use two tools: Tavily (for real-time/up-to-date info like weather, latest data) and Wikipedia (for fixed/authoritative background info like concept definitions, historical facts). Follow these rules strictly for all questions, no matter how simple:
    1. First confirm the core key elements in the user's question, especially the exact current time (year/month/day), as well as location, specific object and other key info;
    2. Search with these key elements, and strictly check the search results: only keep the info that completely matches the key elements (no year/month/day/location deviation) and is not expired;
    3. If the results are mismatched, expired or insufficient, re-search with modified keywords; if no valid info is found, directly state this;
    4. Summarize the valid results as simply and directly as possible, only extract the core answer, no redundant content.
    User's original query: {original_query}
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