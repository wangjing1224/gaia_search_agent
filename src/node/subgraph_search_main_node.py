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
    - If the query is International/Technical, try English keywords FIRST.
    - **LANGUAGE ESCALATION**: If English yields nothing after 1 attempt, try the entity's native language.

    PHASE 2: DEEP READING (The "Jina" Trigger)
    - If a search result title looks relevant but the snippet is truncated → call `web_read_jina` on that URL immediately.
    - Priority targets: Wikipedia pages, company history pages, biographical articles.
    - Do NOT search again if you have a promising URL waiting to be read.

    PHASE 3: PRECISION FALLBACK (The "SerpApi" Trigger)
    - If `web_search_bocha` returns NOTHING relevant after 1-2 attempts:
    - Switch to `web_search_serpapi`.
    - Try LIST queries: "list of [industry] companies founded in [region]".
    
    PHASE 4: ACADEMIC SEARCH
    - Only use `paper_search_arxiv` or `paper_search_pubmed` if the user explicitly asks for papers or scientific research.
    
    ### 6. ANTI-DEADLOCK RULE (CRITICAL!)
    - If you have searched the SAME topic 2 times with similar keywords and got irrelevant results both times:
      **STOP IMMEDIATELY. Output your best summary based on what you HAVE found.**
    - Do NOT rephrase the same query slightly and try again. This wastes search budget.
    - "Information not found for this specific sub-question" is a perfectly valid output.
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
                no_rerank_prompt = "This is your FIRST search. Please analyze the user's query and call a search tool to find relevant information."
            # 如果不是第一次搜索，说明之前的搜索没有得到有用的结果，需要提示模型换个搜索关键词或者换个角度继续搜索
            else:
                no_rerank_prompt = "Your previous search did not yield useful results. Review the history and CALL A TOOL with a DIFFERENT keyword or approach."
        else:
            # 如果有rerank结果，但rerank当前的loop数和搜索循环数不一致，说明上一次搜索没有得到有用的结果，需要提示模型换个搜索关键词或者换个角度继续搜索
            if latest_rerank_result.get("loop", -1) != search_loop_count:
                no_rerank_prompt = "Your previous search did not yield useful results. Review the history and CALL A TOOL with a DIFFERENT keyword or approach."
    else:
        # 如果有有效的rerank结果，说明之前的搜索得到了有用的结果，需要提示模型分析这些结果，看看能不能从中找到有用的信息，或者根据这些结果调整搜索策略
        no_rerank_prompt = "Review the newly fetched information. If you have the EXACT answer, output your summary directly. Otherwise, call a tool to dig deeper."

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
       - **For entity names (companies, people, institutions): always include the OFFICIAL FULL NAME as it appears in authoritative sources (e.g., Wikipedia).** Do not abbreviate.
       - If the answer is NOT in the search results, explicitly state: "Information not found in search results."
    
    {tools_selection_prompt}
    
    ### CURRENT STATUS & NEXT ACTION
    Current Search Loop: {search_loop_count} / 5
    {no_rerank_prompt}

    CRITICAL INSTRUCTION: Based on the current status, you MUST choose ONE of the following actions right now:
    - OPTION A: Call one of the available tools to search or read.
    - OPTION B: Output your final text summary to the user.
    """

    if search_loop_count >= 5:
        # 达到最大搜索循环次数，停止搜索
        # 构造系统提示
        force_stop_prompt = "CRITICAL: You have reached the maximum number of search steps (5). DO NOT CALL ANY TOOLS. You MUST output a final text summary based on what you have found so far. If you found nothing, say 'Information not found'.\n\n"

        force_stop_system_prompt = SystemMessage(
            content=force_stop_prompt + SEARCH_SYSTEM_PROMPT
        )

        # 重新 invoke，但不绑定工具，强迫它生成文本
        response = llm.invoke([force_stop_system_prompt] + messages)
        
        summary = response.content if response.content else "Information not found."
        return {
            "messages": [response],
            "summary": summary
        }

    # 1. 准备系统提示和消息
    system_message = SystemMessage(content=SEARCH_SYSTEM_PROMPT)
    # 2. 绑定工具到语言模型
    llm_with_tools = llm.bind_tools(tools)
    # 3. 调用 LLM + 工具
    response = llm_with_tools.invoke([system_message] + messages)

    if not response.tool_calls:
        return {"messages": [response], "summary": response.content}

    return {"messages": [response]}
