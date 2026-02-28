from src.state.state import AgentState
from src.llm.model import get_llm
from src.utils.skills_utils import get_skills_overview
from src.tools.load_skill_tool import load_skill
from src.schemas.main_graph_skills_load_response import MainGraphSkillsLoadResponse

from langchain_core.messages import SystemMessage, HumanMessage

# 初始化 LLM 和 Tools
tools = [load_skill]
llm = get_llm()

def maingraph_skills_load_node(state: AgentState):
    # 这个message是主图中传递的消息列表，仅为了提取用户最初问题
    messages = state["messages"]
    
    # 初始化用户最初问题
    if state.get("user_initial_query") is None:
        # 从消息中提取用户最初的问题
        user_initial_query = None
        for msg in messages:
            if isinstance(msg, HumanMessage):
                user_initial_query = msg.content
                break
        state["user_initial_query"] = user_initial_query
    
    # 这才是技能加载节点真正使用的消息列表，专门记录技能加载过程中的消息，包括系统提示词和工具调用的输入输出等，供技能加载过程中的多轮交互使用    
    skills_load_messages = state["skills_load_messages"]
    
    # 定义主图技能加载节点的系统提示词，包含技能列表和用户最初问题等关键信息，指导模型正确选择技能并调用load_skill工具    
    SKILLS_LOAD_NODE_SYSTEM_PROMPT = f"""
    You are an elite Factual Research Execution Agent.
    SKILLS OVERVIEW:
    {get_skills_overview()}
    USER'S INITIAL QUERY:
    {state['user_initial_query']}
    Your task is to load the most relevant skill based on the user's initial query.
    Follow these directives strictly:
    1. Analyze the user's initial query and determine which skill is most relevant to solving the riddle.
    2. Call the `load_skill` tool with the name of the identified skill tofetch the detailed playbook.
    3. Do NOT attempt to answer the question or perform any reasoning before loading the skill
    4. Keep your initial analysis concise (1-2 sentences) and focused solely on skill selection.
    """
    
    # 将系统提示词和技能加载过程中的消息记录一起发送给LLM，得到新的技能加载消息
    system_prompt = SystemMessage(content=SKILLS_LOAD_NODE_SYSTEM_PROMPT)
    llm_with_tools = llm.bind_tools(tools)
    response = llm_with_tools.invoke([system_prompt] + skills_load_messages)
    
    # 此时表示技能加载节点已经完成了技能选择和工具调用，得到了新的技能加载消息，接下来需要更新状态
    if not response.tool_calls:
        # 构造新的系统提示词，让他整理好收集到的技能加载消息，输出最终加载好的技能内容，供后续节点使用
        SKILLS_LOAD_NODE_OUTPUT_SYSTEM_PROMPT = """
        You have completed the skill loading process. 
        Now, based on the entire conversation history of this skill loading phase.
        Don't alter zhe content
        """
        
        output_system_prompt = SystemMessage(content=SKILLS_LOAD_NODE_OUTPUT_SYSTEM_PROMPT)
        structured_llm = llm.with_structured_output(MainGraphSkillsLoadResponse)
        output_response = structured_llm.invoke([output_system_prompt] + skills_load_messages + [response])
        
        return {
            "skills_load_messages": "clear",
            "loaded_skill_content": output_response.loaded_skill_content,
            "get_skills_reasoning": output_response.get_skills_reasoning
        }  
    
    return {
        "skills_load_messages": [response]
    }