import datetime
from src.llm.model import get_llm
from src.tools.arxiv_search_tool import paper_search_arxiv
from src.tools.bocha_search_tool import web_search_bocha
from src.tools.jinreader_read_tool import web_read_jina
from src.tools.pubmed_search_tool import paper_search_pubmed
from src.tools.serpapi_search_tool import web_search_serpapi
from src.state.subgraph_search_state import SubgraphSearchState

from langchain_core.messages import SystemMessage

llm = get_llm()

tools = [paper_search_arxiv, web_search_bocha, web_read_jina, paper_search_pubmed, web_search_serpapi]

current_date = datetime.datetime.now().strftime("%Y-%m-%d")

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
    You are a precision-focused Search Analyst. Your goal is to extract EXACT facts from search results to answer the user's specific query.
    Current Date: {current_date}

    ### DATA ANALYSIS RULES
    1. Fact Verification: 
       - If the user asks for a specific year, name, or location, you must find explicit evidence.
       - Do not approximate. If the text says "late 2010s", do not convert it to "2018" unless explicitly stated.
    
    2. Handling Riddles & Indirect Descriptions:
       - The query might describe a person/event without naming them (e.g., "The author who wrote...").
       - Use the search results to identify the entity FIRST, then answer the specific question about them.
    
    3. Citation & Sources:
       - You are provided with "Reranked Search Results".
       - Base your summary ONLY on these results. Do not use your internal knowledge base for specific facts (like dates or news) as they might be outdated.
       - If the search results contain the answer, extract it clearly.
       - If the search results represent a conflict (Source A says X, Source B says Y), mention the conflict.

    4. Output Style:
       - Provide a concise summary that directly answers the "Search Task".
       - Include key details (Years, Full Names, Locations) found in the text.
       - If the answer is NOT in the search results, explicitly state: "Information not found in search results."

    User's specific search query: {original_query}
    
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