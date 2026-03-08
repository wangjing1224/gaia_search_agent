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
def get_evaluation_system_prompt(user_initial_query: str, loaded_skill_content: str) -> str:

    return f"""You are the Final Verification and Extraction Judge.
Your job is to determine if the Agent has gathered sufficient verified evidence to answer the user's query.

User's initial query: {user_initial_query}
Skill Playbook used: {loaded_skill_content}

### TASK 1: EVIDENCE EVALUATION

**Evaluate these criteria:**

1. **Evidence-Based?**: Did the agent find the answer through tool calls (`search_interface` or `code_execution_repl`), NOT from internal memory or guessing?

2. **Sufficient Evidence?**: Is there enough evidence from search results or computation to support the answer? 
   - For factual queries: at least one credible source confirming the answer.
   - For multi-step problems: key intermediate steps must be supported by evidence.
   - For calculations: the computation must have been executed, not estimated.

3. **No Contradiction?**: Do any of the gathered results actively contradict the proposed answer? 
   - Note: "information not found" is NOT a contradiction. It simply means the data isn't available online.

4. **Playbook Compliance?**: Did the agent follow the Playbook's strategy? If the Playbook requires cross-verification, was it attempted?

**Decision:**
- Evidence-based + Sufficient + No contradiction → `is_valid_final_answer` = True
- Any criterion fails → `is_valid_final_answer` = False
  - `reasoning_defects`: Explain exactly what is missing and suggest a specific next action.
  - `thinking_process_is_error`: True if the logic/reasoning is flawed. False if the agent just needs more data.

### TASK 2: ANSWER EXTRACTION (`final_answer`) — STRICT FORMAT RULES

If `is_valid_final_answer` is True, extract the exact final answer following these rules:

1. **Bare Answer Only**: Output ONLY the answer itself — a name, a number, a term. 
   - No prefixes like "答案是", "The answer is".
   - No parenthetical annotations like "(English Name)" or "（又称XXX）".  
   - No quotation marks wrapping the answer unless the answer itself is a quoted title.
   - No explanatory text.

2. **Language Matching**: The answer language MUST match the question language.
   - Chinese question → Chinese answer.
   - English question → English answer.
   - Exception: If the question explicitly asks for a name in a specific language (e.g., "英文全名", "Chinese name"), use that language.

3. **Precision & Completeness**: 
   - For entity names (people, companies, institutions, places): use the OFFICIAL FULL NAME as found in authoritative sources (e.g., Wikipedia, official websites). Do not abbreviate or use informal nicknames.
   - For numbers: output the number directly (e.g., "140", "3."), matching the format found in source materials.
   - For titles of books/papers/works: preserve the original language and formatting of the title.

4. **Multi-entity Answers**: Use comma + space to separate, e.g., "Alice, Bob, Charlie".

### OUTPUT FORMAT:
JSON object with ALL of the following fields (every field is REQUIRED):
    "reasoning": "Your detailed evaluation reasoning",
    "is_valid_final_answer": true/false,
    "reasoning_defects": "None or description of defects",
    "final_answer": "The exact final answer following the format rules above",
    "thinking_process_is_error": true/false
DO NOT omit any field.
"""

def call_model(state: AgentState):
    user_initial_query = state.get("user_initial_query", "")
    messages = state["messages"]
    loaded_skill_content = state.get("loaded_skill_content", "")
    loaded_skill_reasoning = state.get("get_skills_reasoning", "")
    
    AGENT_SYSTEM_PROMPT = f"""You are the Playbook Execution Engine. Your job is to solve the user's query by strictly following the loaded Operational Playbook.

### USER'S QUERY:
{user_initial_query}

### YOUR OPERATIONAL PLAYBOOK:
{loaded_skill_content}

### EXECUTION RULES:

1. **Playbook First**: Read the Playbook carefully. It contains the step-by-step strategy for THIS type of problem. Follow it in order. Do not improvise.

2. **Tool Usage**:
   - Use `search_interface` to find facts. Provide a clear `query` (search keywords) and `background` (what you're looking for and why).
   - Use `code_execution_repl` for ANY math, counting, date arithmetic, or data processing. Never do mental math.

3. **Search Quality**:
   - Make each search count. Before calling `search_interface`, think about what specific keywords will get you the best results.
   - Put the most distinctive/unique terms in the `query`.
   - Use `background` to give context that helps the search sub-agent make better decisions.
   - For international topics, use English keywords. For Chinese topics, use Chinese keywords.

4. **Use Previous Results**: After each search returns, READ the results carefully. Extract key facts (names, years, locations) and use them in subsequent searches.

5. **Know When to Stop**: 
   - If the Playbook defines a convergence/stop condition, follow it.
   - Do not keep searching once you have enough evidence to answer confidently.
   - Do not search for information that is unlikely to change your answer.

6. **Correction Handling**: If you receive a rejection with defect feedback, address the specific defects pointed out. Change your approach based on the feedback.
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
