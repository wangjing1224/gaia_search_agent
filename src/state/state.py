# src/state/state.py
from langgraph.graph import MessagesState
from typing import Annotated, List, Union, Literal
from typing import Optional

# 如果需要扩展额外的状态字段，可以在这里添加
class AgentState(MessagesState):
    
    #用户最初问题
    user_initial_query : str
    
    #最终答案
    final_answer : Optional[str] = None
    