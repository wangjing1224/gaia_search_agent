# src/node/nodes.py
from src.state.state import AgentState
from src.llm.model import get_llm
from src.interface_tools.search_interface import search_interface
from src.tools.repl_tool import code_execution_repl
from src.schemas.main_graph_response import MainGraphResponse

from langchain_core.messages import SystemMessage, HumanMessage

# 初始化 LLM 和 Tools
tools = [search_interface, code_execution_repl]
llm = get_llm()


# 专门为结构化输出（验证与提取阶段）定制的裁判提示词
def get_evaluation_system_prompt(user_initial_query: str,loaded_skill_content: str ) -> str:

    return f"""You are the Final Verification and Extraction Judge.
Your task is to review the entire conversation history and determine if the Agent has gathered unassailable, verified evidence to answer the user's initial query.

User's initial query: {user_initial_query}
loaded skill content: {loaded_skill_content}

### TASK 1: EVALUATION (is_valid_final_answer & reasoning_defects)
- **Check the Evidence**: Did the agent actually find the explicit answer via search tools, or is it hallucinating/guessing? 
- If the agent failed to find the information, or the evidence is contradictory, or it made a logical leap without proof:
  -> Set `is_valid_final_answer` to False.
  -> Explain EXACTLY what is missing or what needs to be re-searched in `reasoning_defects`.
- If the evidence is solid and the logical chain is complete:
  -> Set `is_valid_final_answer` to True.
  -> Set `reasoning_defects` to "None".

### TASK 2: EXTRACTION (final_answer)
If `is_valid_final_answer` is True, extract the final answer strictly:
1. NO conversational filler (e.g., Output "魂武者" instead of "答案是魂武者").
2. Strictly maintain the SAME LANGUAGE as the user's question (Chinese or English).
3. If the question asks for a specific format (e.g., digits only, or "A and B"), follow it strictly.
*Note: If `is_valid_final_answer` is False, just fill final_answer with "N/A" (it will be discarded anyway).*
"""


def call_model(state: AgentState):
    user_initial_query = state.get("user_initial_query", "")
    messages = state["messages"]
    loaded_skill_content = state.get("loaded_skill_content", "")
    loaded_skill_reasoning = state.get("get_skills_reasoning", "")
    
    AGENT_SYSTEM_PROMPT = f"""
    User's Initial Query: {user_initial_query}
    {loaded_skill_content}
    """

    system_message = SystemMessage(content=AGENT_SYSTEM_PROMPT)

    # 将工具绑定到 LLM (Function Calling)
    llm_with_tools = llm.bind_tools(tools)
    # 调用 LLM，传入系统提示和历史消息，获取模型响应
    response = llm_with_tools.invoke([system_message] + messages)

    # 返回更新后的 messages，MessagesState 会自动 append
    # 如果没有工具调用，说明模型已经给出了最终答案，可以直接返回 final_answer
    if not response.tool_calls:

        # 构造结构化输出的prompt，规范回答
        evaluation_system_prompt = get_evaluation_system_prompt(user_initial_query, loaded_skill_content)

        structured_llm = llm.with_structured_output(MainGraphResponse)
        final_structured_response = structured_llm.invoke(
            [SystemMessage(content=evaluation_system_prompt)] + messages + [response]
        )

        if not final_structured_response.is_valid_final_answer:
            if final_structured_response.thinking_process_is_error:
                reflection_mainnode_prompt = HumanMessage(
                    content=f"""
                    Your attempt to provide a final answer was rejected by the Verification Module.
                    Your reasoning record: {final_structured_response.reasoning}
                    Identified Defects & Missing Info: {final_structured_response.reasoning_defects}
                    ACTION REQUIRED: You are NOT allowed to guess. You must analyze zhe reasoning recordd and defects,then you should reformulate your search strategy. 
                    """
                )
                return {
                    "messages": [response, reflection_mainnode_prompt],
                    "thinking_process_is_error": True
                }
            else:
                reflection_skillloadnode_prompt = HumanMessage(
                    content=f"""
                    The Verification Module has determined that the final answer is invalid.
                    This suggests that the error may lie in the application of the skills.
                    Your get_skills_reasoning for loading the skill was: {loaded_skill_reasoning}
                    Please reselect the skills based on the user's initial query and the skills overview.
                    """
                )
                return {
                    "skills_load_messages": [response, reflection_skillloadnode_prompt],
                    "thinking_process_is_error": False
                }

        return {
            "messages": [response],
            "final_answer": final_structured_response.final_answer,
        }

    return {"messages": [response]}
