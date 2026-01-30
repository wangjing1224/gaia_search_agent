# src/node/nodes.py
from src.state.state import AgentState
from src.llm.model import get_llm
from src.tools.search import get_tools

# 初始化 LLM 和 Tools
tools = get_tools()
llm = get_llm()

# 将工具绑定到 LLM (Function Calling)
llm_with_tools = llm.bind_tools(tools)

def call_model(state: AgentState):
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    # 返回更新后的 messages，MessagesState 会自动 append
    return {"messages": [response]}