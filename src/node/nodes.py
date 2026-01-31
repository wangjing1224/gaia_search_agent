# src/node/nodes.py
from src.state.state import AgentState
from src.llm.model import get_llm
from src.tools.search import get_tools
from src.interface_tools.search_interface import search_interface

from langchain_core.messages import SystemMessage

# 初始化 LLM 和 Tools
tools = [search_interface]
llm = get_llm()

ANGENt_SYSTEM_PROMPT = """
You are an expert in solving user queries by utilizing web search effectively and logically. Your core goal is to respond to user queries accurately, efficiently, and with clear step-by-step reasoning.
When handling queries that require integrating multiple pieces of basic information to get the final answer (e.g., calculating differences, making comparisons, or synthesizing conclusions), you must follow these rules strictly:
1. First, decompose the user's query into independent, sequential basic search steps. Each step should only focus on obtaining one single piece of basic information, rather than directly searching for the final integrated result or comparison.
2. Execute each search step one by one: conduct a separate web search for each decomposed basic information point, confirm that you have obtained accurate and complete basic data for that step before proceeding to the next step.
3. After collecting all the required basic information through multi-step searches, integrate, calculate, or analyze the data to form the final answer to the user's query.
4. It is strictly prohibited to directly search for "final comparison results", "direct answers" or other integrated content that skips the basic search steps. You must ensure that every piece of basic information comes from an independent search operation.
Always maintain the logic of "decompose the query → search step by step for basic information → integrate to get the final answer", ensuring the accuracy and traceability of each piece of data, and efficiently completing the user's query based on reliable search results.
"""

def call_model(state: AgentState):
    messages = state["messages"]
        
    system_message = SystemMessage(content=ANGENt_SYSTEM_PROMPT)
    
    
    # 将工具绑定到 LLM (Function Calling)
    llm_with_tools = llm.bind_tools(tools)
    
    response = llm_with_tools.invoke([system_message] + messages)
    # 返回更新后的 messages，MessagesState 会自动 append
    
    if not response.tool_calls:
        return {
            "messages": [response],
            "final_answer": response.content
        }
        
    return {"messages": [response]}