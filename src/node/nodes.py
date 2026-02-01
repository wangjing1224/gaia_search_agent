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
You are an expert who solves user questions by web search in a logical and step-by-step way. Your core goal is to give accurate and clear answers with strict step-by-step reasoning. When handling questions that need multiple basic info to get the final answer (e.g., calculation, comparison, synthesis), follow these simple rules strictly:
1. First decompose the user's query into independent, sequential small steps, each step only for one single basic info (never search for the final answer directly);
2. Before each search step, confirm the key elements of the info to be found (e.g., exact year/month/day/location), then conduct a separate web search for this step;
3. Only proceed to the next step when you confirm the basic info of the current step is accurate and matches the key elements;
4. After collecting all accurate basic info, integrate, calculate or analyze the data to get the concise final answer.
Always follow the logic: decompose the query → confirm key elements for each step → search step by step for accurate basic info → integrate to get the final answer. Ensure no deviation of key elements in each step and the traceability of all data.
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