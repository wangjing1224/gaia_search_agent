# src/state/state.py
from langgraph.graph import MessagesState
from langchain_core.messages import AnyMessage
from typing import Annotated, List, Union, Literal
from typing import Optional

def skills_load_messages_reducer(current: List[AnyMessage], update: Union[List[AnyMessage], str]) -> List[AnyMessage]:
    if update == "clear":
        return []
    else:
        return current + update

# 如果需要扩展额外的状态字段，可以在这里添加
class AgentState(MessagesState):
    
    #用户最初问题
    user_initial_query : str
    
    #最终答案
    final_answer : Optional[str] = None
    
    #技能加载过程中的消息记录，包含系统提示词和工具调用的输入输出等
    skills_load_messages : Annotated[List[AnyMessage], skills_load_messages_reducer]
    
    #最终加载好的技能内容
    loaded_skill_content : Optional[str] = None
    
    #加载技能的推理过程
    get_skills_reasoning : Optional[str] = None
    
    #错误的答案是否由于错误的思维过程导致的，true表示思维过程有误，false表示思维过程正确加载的技能有误
    thinking_process_is_error: Optional[bool] = None
    