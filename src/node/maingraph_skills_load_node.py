from src.state.state import AgentState
from src.llm.model import get_llm
from src.utils.skills_utils import get_skills_overview
from src.tools.load_skill_tool import load_skill
from src.schemas.main_graph_skills_load_response import MainGraphSkillsLoadResponse

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser

# 初始化 LLM 和 Tools
tools = [load_skill]
llm = get_llm()


def maingraph_skills_load_node(state: AgentState):
    user_initial_query = state.get("user_initial_query")
    if user_initial_query is None:
        # 这个message是主图中传递的消息列表，仅为了提取用户最初问题
        messages = state["messages"]
        # 从消息中提取用户最初的问题
        for msg in messages:
            if isinstance(msg, HumanMessage):
                user_initial_query = msg.content
                break
    

    # 这才是技能加载节点真正使用的消息列表，专门记录技能加载过程中的消息，包括系统提示词和工具调用的输入输出等，供技能加载过程中的多轮交互使用
    skills_load_messages = state.get("skills_load_messages", [])

    # 定义主图技能加载节点的系统提示词，包含技能列表和用户最初问题等关键信息，指导模型正确选择技能并调用load_skill工具
    SKILLS_LOAD_NODE_SYSTEM_PROMPT = f"""You are the Skill Router for a factual research system. 
    
SKILLS OVERVIEW:
{get_skills_overview()}

USER'S INITIAL QUERY:
{user_initial_query}

### YOUR ONLY MISSION:
1. Read the user's initial query to determine its type (e.g., Multi-hop, Academic, Calculation).
2. Then you should use the "load_skill" tool to load the most appropriate Operational Playbook (Skill) that can solve the user's query. Each skill is designed for a specific query type, so choose carefully based on the query's characteristics.
3. IF YOU ALREADY GOT THE SKILL CONTENT, SIMPLY OUTPUT WHY THIS SKILL WAS CHOSEN BASED on the user's query type, DO NOT OUTPUT ANYTHING ELSE. The content of the skill will be extracted by a later node, you don't need to worry about it.
4. **RED LINE**: DO NOT attempt to solve the riddle. DO NOT search your memory. DO NOT output any reasoning steps about the answer itself.
"""

    # 将系统提示词和技能加载过程中的消息记录一起发送给LLM，得到新的技能加载消息
    system_prompt = SystemMessage(content=SKILLS_LOAD_NODE_SYSTEM_PROMPT)
    
    # 判断是否是技能加载节点的第一轮交互，如果是第一轮，需要加上用户提示词，防止出错
    is_first_turn = len(skills_load_messages) == 0
    if is_first_turn:
        human_prompt = HumanMessage(content=user_initial_query)
        input_messages = [system_prompt, human_prompt] + skills_load_messages
    else:
        input_messages = [system_prompt] + skills_load_messages
        
    llm_with_tools = llm.bind_tools(tools)
    response = llm_with_tools.invoke(input_messages)
    
    # 根据是否是第一轮交互来决定返回的消息列表，如果是第一轮，需要把用户提示词也加上，供后续技能加载交互使用
    return_messages = [human_prompt, response] if is_first_turn else [response]

    # 此时表示技能加载节点已经完成了技能选择和工具调用，得到了新的技能加载消息，接下来需要更新状态
    if not response.tool_calls:
        # 构造新的系统提示词，让他整理好收集到的技能加载消息，输出最终加载好的技能内容，供后续节点使用
        SKILLS_LOAD_NODE_OUTPUT_SYSTEM_PROMPT ="""
Based on the conversation history, your task is to extract the EXACT raw markdown content of the loaded skill and your brief reasoning.
You MUST format your output as a JSON object.

### STRICT RULES:
1. `loaded_skill_content`: MUST be the exact, unmodified text returned by the `load_skill` tool. Do not summarize or alter the playbook.
2. `get_skills_reasoning`: Briefly state why this skill was chosen based on the user's query type.
"""

        # output_system_prompt = SystemMessage(
        #     content=SKILLS_LOAD_NODE_OUTPUT_SYSTEM_PROMPT
        # )
        # structured_llm = llm.with_structured_output(MainGraphSkillsLoadResponse)
        # output_response = structured_llm.invoke(
        #     [output_system_prompt] + skills_load_messages + [response]
        # )
        
        parser = JsonOutputParser(pydantic_object=MainGraphSkillsLoadResponse)
        
        final_prompt = SKILLS_LOAD_NODE_OUTPUT_SYSTEM_PROMPT + "\n\n" + parser.get_format_instructions()
        
        llm_no_streaming = llm.bind(stream=False)  # 结构化输出不需要流式，确保一次性返回完整内容
        raw_structured_response = llm_no_streaming.invoke(
            [SystemMessage(content=final_prompt)] + skills_load_messages + [response]
        )
        
        try:
            parsed_dict = parser.invoke(raw_structured_response)
            loaded_skill_content = parsed_dict.get("loaded_skill_content", "")
            get_skills_reasoning = parsed_dict.get("get_skills_reasoning", "")
        except Exception as e:
            print("Error parsing structured response:", e)
            loaded_skill_content = "The skill content could not be extracted due to an error in parsing the response.Please don't use tools calls, then return the skills_load_node."
            get_skills_reasoning = "No reasoning provided or error in parsing response."

        # return {
        #     "skills_load_messages": return_messages,
        #     "loaded_skill_content": output_response.loaded_skill_content,
        #     "get_skills_reasoning": output_response.get_skills_reasoning,
        # }
        return {
            "skills_load_messages": return_messages,
            "loaded_skill_content": loaded_skill_content,
            "get_skills_reasoning": get_skills_reasoning
        }
    
    
    # 初始化用户最初问题
    # 注意：用户最初问题只需要在技能加载节点的第一轮交互时从消息中提取一次，后续技能加载交互不需要重复提取，直接保存在状态中供后续节点使用即可
    if state.get("user_initial_query") is None:
        return {
            "user_initial_query": user_initial_query,
            "skills_load_messages": return_messages
        }
    # 如果不是第一轮交互，说明已经提取过用户最初问题了，直接更新技能加载消息列表即可
    else:
        return {
            "skills_load_messages": return_messages
        }
