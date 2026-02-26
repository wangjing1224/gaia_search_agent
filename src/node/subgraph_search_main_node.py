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

tools = [
    paper_search_arxiv,
    web_search_bocha,
    web_read_jina,
    paper_search_pubmed,
    web_search_serpapi,
]


def subgraph_search_main_node(state: SubgraphSearchState):
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")

    messages = state["messages"]

    original_query = state.get("current_query", "")

    search_loop_count = state.get("search_loop_count", 0)

    reranked_results = state.get("reranked_results", [])

    # 获取最后一次rerank结果。如果没有rerank结果或者rerank当前的loop数和搜索循环数不一致，说明当前没有有效的rerank结果
    latest_rerank_result = reranked_results[-1] if reranked_results else {}

    no_rerank_prompt = ""  # 没有rerank结果的提示语，初始为空
    rerank_history_str = ""  # 历史rerank结果记录，初始为空,同样也表示历史搜索记录
    current_time_prompt = f"The current date is {current_date}."  # 当前时间提示，提示模型当前的时间，帮助模型判断信息是否过时
    tools_selection_prompt = """
    ### 5. TOOL SELECTION STRATEGY (STRICT ORDER)
    
    PHASE 1: BROAD SEARCH
    - ALWAYS start with `web_search_bocha`. It is your primary radar.
    - If the query is about a Chinese entity, use Chinese keywords.
    - If the query is International/Technical, try English keywords.

    PHASE 2: DEEP READING (The "Jina" Trigger)
    - Look at the `web_search_bocha` results.
    - Is there a result where the Title matches the user's intent, but the Snippet is cut off?
    - YES -> Call `web_read_jina` on that specific URL immediately.
    - Do NOT search again if you have a promising URL waiting to be read.

    PHASE 3: PRECISION FALLBACK (The "SerpApi" Trigger)
    - If `web_search_bocha` returns NOTHING relevant after 1-2 attempts:
    - Switch to `web_search_serpapi`.
    - CRITICAL: Translate the query to English before calling SerpApi for international topics.
    
    PHASE 4: ACADEMIC SEARCH
    - Only use `paper_search_arxiv` (CS/Math/Physics) or `paper_search_pubmed` (Bio/Med) if the user explicitly asks for "papers", "studies", or "scientific research".
    """

    # 获取最后一次rerank结果。如果没有rerank结果或者rerank当前的loop数和搜索循环数不一致，说明当前没有有效的rerank结果
    if (
        not reranked_results
        or latest_rerank_result.get("loop", -1) != search_loop_count
    ):
        # 如果是第一次搜索,即search_loop_count为0，说明还没有进行过搜索，更没有rerank结果，此时应该提示模型开始第一次搜索
        if not reranked_results:
            # 第一次搜索，提示模型分析用户查询，想出一个精准的搜索查询来寻找相关信息
            if search_loop_count == 0:
                no_rerank_prompt = "This is your first search. Please analyze the user's query and come up with a precise search query to find relevant information."
            # 如果不是第一次搜索，说明之前的搜索没有得到有用的结果，需要提示模型换个搜索关键词或者换个角度继续搜索
            else:
                no_rerank_prompt = "Your previous search did not yield useful results. You must review the search tool histories to analyze the search query. Please try a different search query or approach to find relevant information."
        else:
            # 如果有rerank结果，但rerank当前的loop数和搜索循环数不一致，说明上一次搜索没有得到有用的结果，需要提示模型换个搜索关键词或者换个角度继续搜索
            if latest_rerank_result.get("loop", -1) != search_loop_count:
                no_rerank_prompt = "Your previous search did not yield useful results. You must review the search tool histories and the the historical search results to analyze the search query. Please try a different search query or approach to find relevant information."

    # 如果有历史rerank结果，拼接成字符串，作为提示语的一部分，告诉模型之前搜索过什么，得到过什么结果，帮助模型调整搜索策略
    for rerank_result in reranked_results:
        # 获取每一次rerank的搜索循环数和对应的rerank结果项，拼接成字符串记录下来
        # 当前第几轮搜索循环
        loop = rerank_result.get("loop", -1)
        rerank_result_items = rerank_result.get("rerank_result_items", [])
        rerank_history_str += f"Search Loop {loop}:\n"
        for i, item in enumerate(rerank_result_items):
            current_loop_query = item.get("query", "")
            rerank_history_str += f"  Query: {current_loop_query}\n"
            current_loop_rerankitems = item.get("rerank_items", [])
            for j, rerank_item in enumerate(current_loop_rerankitems):
                title = rerank_item.get("title", "")
                url = rerank_item.get("url", "")
                content = rerank_item.get("content", "")
                source = rerank_item.get("source", "")
                rerank_history_str += f"Result {j+1}:\n   Title: {title}\n   URL: {url}\n   Content: {content}\n   Source: {source}\n\n"

    # 构造系统提示，包含当前时间提示、没有rerank结果的提示（如果有的话）、历史rerank结果记录（如果有的话）以及原始查询，告诉模型当前的搜索状态和历史搜索记录，帮助模型调整搜索策略
    SEARCH_SYSTEM_PROMPT = f"""
    You are a Tier-1 Investigative Reporter. Your mission is to find EXACT facts for a specific query.
    {current_time_prompt}
    
    User's Search Task: {original_query}
    
    History of your investigation:
    {rerank_history_str}

    ### EXECUTION PROTOCOL
    1. **Analyze the Gap**: Look at the history. What did you try? Why did it fail?
       - If previous results were irrelevant -> CHANGE your keywords. Simplify them. Use English if Chinese failed.
       - If you found a link but no content -> USE `web_read_jina`.
       
    2. **Fact Extraction (The Gold Standard)**:
       - You answer MUST be grounded in the "Reranked Search Results".
       - If the text says "born in the late 90s", DO NOT guess "1998". Search specifically for "birth year of [Name]".
       - Dealing with Aliases: If the user asks about "The company founded by X", and search says "X founded Alibaba", your next step (if needed) is to verify details about Alibaba.

    3. **Stop Condition**:
       - If you found the EXACT answer to the `original_query`, output the Summary immediately.
       - If you have tried 3 different search angles/tools and found nothing, output "Information not found". Do not loop forever.

    4. Output Style:
       - Provide a concise summary that directly answers the "Search Task".
       - Include key details (Years, Full Names, Locations) found in the text.
       - If the answer is NOT in the search results, explicitly state: "Information not found in search results."
    \n
    """

    if search_loop_count >= 5:
        # 达到最大搜索循环次数，停止搜索
        # 构造系统提示
        force_stop_prompt = "You have reached the maximum number of search steps (5). Please summarize what you have found so far, even if it is incomplete. DO NOT search again."

        force_stop_system_prompt = SystemMessage(
            content=force_stop_prompt + SEARCH_SYSTEM_PROMPT
        )

        # 重新 invoke，但不绑定工具，强迫它生成文本
        response = llm.invoke([force_stop_system_prompt] + messages)
        return {
            "messages": [response],
        }

    SEARCH_SYSTEM_PROMPT += tools_selection_prompt + "\n\n" + no_rerank_prompt

    # 1. 准备系统提示和消息
    system_message = SystemMessage(content=SEARCH_SYSTEM_PROMPT)
    # 2. 绑定工具到语言模型
    llm_with_tools = llm.bind_tools(tools)
    # 3. 调用 LLM + 工具
    response = llm_with_tools.invoke([system_message] + messages)

    if not response.tool_calls:
        return {"messages": [response], "summary": response.content}

    return {"messages": [response]}
