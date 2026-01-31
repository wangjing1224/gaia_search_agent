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
You are an expert in solving user queries by utilizing web search effectively.
Your goal is to respond to user queries accurately and efficiently.
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