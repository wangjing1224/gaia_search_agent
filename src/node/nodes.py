# src/node/nodes.py
from src.state.state import AgentState
from src.llm.model import get_llm
from src.interface_tools.search_interface import search_interface
from src.tools.repl_tool import code_execution_repl
from src.tools.load_skill_tool import load_skill
from src.schemas.main_graph_response import MainGraphResponse
from src.utils.skills_utils import get_skills_overview

from langchain_core.messages import SystemMessage, HumanMessage

# 初始化 LLM 和 Tools
tools = [search_interface, code_execution_repl, load_skill]
llm = get_llm()


# 动态获取主脑系统提示词，确保技能列表是最新的
def get_agent_system_prompt():

    skills_overview = get_skills_overview()

    return f"""You are the Lead Investigative Manager for a high-stakes competition. Your goal is to solve complex, multi-hop historical, academic, and factual riddles with absolute precision.

### AVAILABLE SKILLS (YOUR PLAYBOOKS)
{skills_overview}

### CORE WORKFLOW (MUST FOLLOW STRICTLY)

1. **SKILL ACQUISITION (FIRST STEP)**
   - Before searching, use the `load_skill` tool with the appropriate path from the AVAILABLE SKILLS list to load the operational playbook.

2. **DECOMPOSE & TRIANGULATE**
   - Break the riddle into sub-clues.
   - Use `search_interface` to find facts. If a query requires intersection of multiple events, search them independently.
   - **VARIABLE SUBSTITUTION**: If Step 1 finds "1984", your next search MUST include "1984", NOT "the year he was born".

3. **TOOL USAGE**
   - NEVER do mental math. Use `code_execution_repl` to calculate ages, years, or count items.

4. **REFLECTION & ERROR CORRECTION**
   - If you receive a "reflection prompt" stating your reasoning has defects, DO NOT attempt to answer again immediately.
   - You MUST formulate a new search strategy, change your keywords, and use `search_interface` or `code_execution_repl` to find the missing information.

5. **LANGUAGE CONSISTENCY**
   - If the user asks in Chinese, ALWAYS think and output in Chinese. If English, use English.
"""


# 专门为结构化输出（验证与提取阶段）定制的裁判提示词
def get_evaluation_system_prompt(user_initial_query: str):

    return f"""You are the Final Verification and Extraction Judge.
Your task is to review the entire conversation history and determine if the Agent has gathered unassailable, verified evidence to answer the user's initial query.

User initial query: {user_initial_query}

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

    system_message = SystemMessage(content=get_agent_system_prompt())

    # 将工具绑定到 LLM (Function Calling)
    llm_with_tools = llm.bind_tools(tools)
    # 调用 LLM，传入系统提示和历史消息，获取模型响应
    response = llm_with_tools.invoke([system_message] + messages)

    # 返回更新后的 messages，MessagesState 会自动 append
    # 如果没有工具调用，说明模型已经给出了最终答案，可以直接返回 final_answer
    if not response.tool_calls:

        # 构造结构化输出的prompt，规范回答
        evaluation_system_prompt = get_evaluation_system_prompt(user_initial_query)

        structured_llm = llm.with_structured_output(MainGraphResponse)
        final_structured_response = structured_llm.invoke(
            [SystemMessage(content=evaluation_system_prompt)] + messages + [response]
        )

        if not final_structured_response.is_valid_final_answer:
            reflection_prompt = HumanMessage(
                content=f"""
[SYSTEM INTERCEPTION] Your attempt to provide a final answer was rejected by the Verification Module.
Your reasoning record: {final_structured_response.reasoning}
Identified Defects & Missing Info: {final_structured_response.reasoning_defects}

ACTION REQUIRED: You are NOT allowed to guess. You MUST use tools (`search_interface` or `code_execution_repl`) to investigate the missing information mentioned above. Pivot your search strategy now.
"""
            )
            return {
                "messages": [response, reflection_prompt],
            }

        return {
            "messages": [response],
            "final_answer": final_structured_response.final_answer,
        }

    return {"messages": [response]}
