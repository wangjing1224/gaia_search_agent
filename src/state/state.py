# src/state/state.py
from langgraph.graph import MessagesState
from typing import Annotated, List, Union, Literal

# 如果需要扩展额外的状态字段，可以在这里添加
class AgentState(MessagesState):
    # Research Agent 可能需要记录当前的步骤或摘要，这里先保持基础
    pass