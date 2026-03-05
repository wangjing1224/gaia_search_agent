# src/node/nodes.py
from src.state.state import AgentState
from src.llm.model import get_llm
from src.interface_tools.search_interface import search_interface
from src.tools.repl_tool import code_execution_repl
from src.schemas.main_graph_response import MainGraphResponse

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser

# 初始化 LLM 和 Tools
tools = [search_interface, code_execution_repl]
llm = get_llm()


# 专门为结构化输出（验证与提取阶段）定制的裁判提示词
def get_evaluation_system_prompt(user_initial_query: str,loaded_skill_content: str ) -> str:

    return f"""You are the Final Verification and Extraction Judge.
Your mandate is to review the entire research history and strictly determine if the Agent has gathered unassailable, verified evidence to answer the user's query.

User's initial query: {user_initial_query}
Skill Playbook used: {loaded_skill_content}

### TASK 1: EVIDENCE EVALUATION (`is_valid_final_answer` & `reasoning_defects`)
- **Zero Hallucination Rule**: Did the agent actually find the explicit answer using `search_interface` or `code_execution_repl`? If the agent relied on internal memory, guessed, or hallucinated a connection, FAIL it.
- **If Failed**: 
  -> `is_valid_final_answer` = False.
  -> `reasoning_defects`: Point out exactly which logical step is missing evidence, or which keyword needs to be searched. Be specific (e.g., "You assumed the year is 1868 but didn't verify if company X was founded then.").
  -> 'thinking_process_is_error' = True if the defect is in the reasoning process (e.g., flawed logic, incorrect inference). Otherwise, False (indicating a skill application error).
- **If Verified**: 
  -> `is_valid_final_answer` = True.
  -> `reasoning_defects` = "None".

### TASK 2: ANSWER EXTRACTION (`final_answer`)
- If `is_valid_final_answer` is True, extract the exact final answer.
- **Normalization**: NO conversational filler. If the answer is "2024", output "2024", not "The year is 2024".
- **Language**: Strictly match the language of the User's initial query (e.g., Chinese query -> Chinese answer).

### OUTPUT FORMAT:
You MUST format your output as a JSON object with ALL of the following fields (every field is REQUIRED):
    "reasoning": "Your detailed reasoning process for evaluating the answer",
    "is_valid_final_answer": True/False,
    "reasoning_defects": "None or description of defects",
    "final_answer": "The exact final answer",
    "thinking_process_is_error": True/False
DO NOT omit any field. All five fields must be present.
"""


def call_model(state: AgentState):
    user_initial_query = state.get("user_initial_query", "")
    messages = state["messages"]
    loaded_skill_content = state.get("loaded_skill_content", "")
    loaded_skill_reasoning = state.get("get_skills_reasoning", "")
    
    AGENT_SYSTEM_PROMPT = f"""You are the Playbook Execution Engine. 
You have been assigned a complex research task and provided with a strict Operational Playbook (Loaded Skill).

### USER'S QUERY TO SOLVE:
{user_initial_query}

### YOUR OPERATIONAL PLAYBOOK (STRICT ADHERENCE REQUIRED):
{loaded_skill_content}

### GLOBAL EXECUTION RULES:
1. **Follow the Playbook**: You must execute the steps defined in the Operational Playbook EXACTLY. Do not skip steps.
2. **Variable Substitution**: If a search reveals a variable (e.g., Year = 1994), substitute "1994" into all subsequent tool calls.
3. **Delegation**: Use `search_interface` to gather facts. Use `code_execution_repl` for any math, counting, or date logic. NO MENTAL MATH.
4. **Correction Handling**: If you previously received a Reflection Prompt rejecting your answer, you MUST pivot your strategy. Change your search keywords or use a different angle based on the defects pointed out.
5. **Anti-Tunnel Vision**: If your current search keywords yield no relevant results after 2 attempts, STOP searching the same thing. Pick a completely different clue from the user's query and start a new search track.
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

        structured_llm = llm.with_structured_output(MainGraphResponse, method="json_mode")
        
        try:
            final_structured_response = structured_llm.invoke(
                [SystemMessage(content=evaluation_system_prompt)] + messages + [response]
            )
        except Exception as e:
            print("Error parsing structured response:", e)
            final_structured_response = MainGraphResponse(
                reasoning="JSON parsing failed due to missing fields.",
                is_valid_final_answer=False,
                reasoning_defects=f"Format error: {e}",
                final_answer="",
                thinking_process_is_error=True
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
                    "skills_load_messages": [reflection_skillloadnode_prompt],
                    "thinking_process_is_error": False
                }

        return {
            "messages": [response],
            "final_answer": final_structured_response.final_answer,
            "thinking_process_is_error": None  # 继续保持原有状态，等待后续判断
        }

    return {
        "messages": [response],
        "thinking_process_is_error": None  # 继续保持原有状态，等待后续判断
    }
