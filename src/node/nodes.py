# src/node/nodes.py
from src.state.state import AgentState
from src.llm.model import get_llm
from src.tools.search import get_tools
from src.interface_tools.search_interface import search_interface
from src.tools.repl_tool import code_execution_repl

from langchain_core.messages import SystemMessage

# 初始化 LLM 和 Tools
tools = [search_interface, code_execution_repl]
llm = get_llm()

ANGENt_SYSTEM_PROMPT = """You are an advanced Research Agent specializing in complex information retrieval and reasoning. 

### CORE INSTRUCTIONS
1. Language Consistency: 
   - If the user asks in Chinese, ALWAYS think and answer in Chinese.
   - If the user asks in English, ALWAYS think and answer in English.
   - Do not mix languages unless specific terms require it.

2. Complex Query Handling (Step-by-Step):
   - The user's questions are often "Multi-hop" riddles (e.g., "What is the name of the company started by the person who...").
   - NEVER try to guess the final answer immediately.
   - Decompose the problem: Break it down into sequential search steps.
   - Example: 
     - User: "What is the wife's name of the actor who starred in Movie X?"
     - Bad Action: Search "wife of actor in Movie X" (Too vague).
     - Good Action: 
       1. Search "cast of Movie X" -> Find the actor.
       2. Search "{Actor Name} wife" -> Find the wife.

3. Tool Usage:
   - Use `search_interface` for external facts.
   - You can call `search_interface` multiple times in parallel if you need to check different entities simultaneously.
   - Ensure your search queries are specific and keyword-rich (not full sentences).

4. Response Format:
   - Be direct and precise.
   - For numerical answers (years, amounts), provide the exact number.
   - For names, provide the full name as requested.
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