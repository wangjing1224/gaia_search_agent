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

ANGENt_SYSTEM_PROMPT = """You are the Lead Researcher for a high-stakes competition. Your goal is to answer complex, multi-hop questions with absolute precision.

### CORE OPERATING RULES

1. Language Consistency: 
   - If the user asks in Chinese, ALWAYS think and answer in Chinese.
   - If the user asks in English, ALWAYS think and answer in English.
   - Do not mix languages unless specific terms require it.

2. **DECOMPOSE & PLAN (The "Riddle Solver" Mode)**
   - The user's query is likely a "Riddle" composed of nested variables.
   - **DO NOT** search the whole sentence.
   - **STRATEGY**:
     1. Identify the *Unknown Variables* (e.g., "a European country", "the year he died").
     2. Create a Plan: Solve Variable A -> Solve Variable B -> Final Answer.
     3. Execute Step 1.
   
   - *Example User Query*: "What is the capital of the country where the CEO of Tesla was born?"
   - *Bad Search*: "Capital of country where CEO of Tesla born"
   - *Good Plan*: 
     1. Search: "Who is the CEO of Tesla?" -> Found: Elon Musk.
     2. Search: "Where was Elon Musk born?" -> Found: South Africa.
     3. Search: "Capital of South Africa" -> Found: Pretoria.

3. **VARIABLE SUBSTITUTION (Crucial)**
   - When you get a result from the `search_subgraph_node`, you MUST explicitly substitute it into your next step.
   - If Step 1 returns "1984", your next search query MUST contain "1984", NOT "the year he was born".

4. **TOOL USAGE & ROUTING**
   - **External Information**: ALWAYS use `search_interface` (which routes to the Search Subgraph). 
     - *Tip*: Provide a specific `background` in the tool call arguments to help the subgraph understand context.
   - **Calculation/Logic**: ALWAYS use `code_execution_repl`.
     - *Strict Rule*: NEVER do mental math. If you need to calculate age (2024 - 1956), convert currency, or count items in a list, WRITE PYTHON CODE.

5. **FINAL ANSWER FORMAT**
   - Once you have all pieces, synthesize the answer.
   - The user wants a direct answer. If the question asks for a name, provide the name. If it asks for a number, provide the number.
   - **Normalization**: 
     - Remove punctuation from the end (unless it's part of the name).
     - Ensure language consistency (Use Chinese if the question is Chinese).

6. FINAL OUTPUT
When you are ready to answer, output strictly the answer itself. 
Do not add "The answer is...". 
For example, if the answer is "2024", just output "2024".

### FAILURE HANDLING
- If a search comes back empty, do not give up. **REPHRASE** the query.
- Try searching for synonyms or related events.
- If you are stuck on a riddle, try searching for unique keywords in the riddle text directly.

Remember: You are the Manager. The `search_interface` is your Research Team. Give them clear, specific directives.
"""


def call_model(state: AgentState):
    user_initial_query = state.get("user_initial_query", "")
    messages = state["messages"]

    system_message = SystemMessage(content=ANGENt_SYSTEM_PROMPT)

    # 将工具绑定到 LLM (Function Calling)
    llm_with_tools = llm.bind_tools(tools)
    # 调用 LLM，传入系统提示和历史消息，获取模型响应
    response = llm_with_tools.invoke([system_message] + messages)

    # 返回更新后的 messages，MessagesState 会自动 append
    # 如果没有工具调用，说明模型已经给出了最终答案，可以直接返回 final_answer
    if not response.tool_calls:

        user_initial_query

        # 构造结构化输出的prompt，规范回答
        new_system_prompt = (
            ANGENt_SYSTEM_PROMPT
            + f"""
    User initial query: {user_initial_query}
    Extract the final answer in strict accordance with the required JSON format.
    Requirements:
    1. The user's question must be answered accurately.
    2. Strictly maintain the same language as the user's question (Chinese or English).
    3. Do not add any redundant explanations or prefixes.
    """
        )

        structured_llm = llm.with_structured_output(MainGraphResponse)
        final_structured_response = structured_llm.invoke(
            [SystemMessage(content=new_system_prompt)] + messages
        )

        if not final_structured_response.is_valid_final_answer:
            reflection_prompt = HumanMessage(
                content=f"""
              Your reasoning record: {final_structured_response.reasoning}
              Your previous reasoning has some defects: {final_structured_response.reasoning_defects}.
              Please reflect on these defects and try to find the missing information. 
              Then, update your reasoning and final answer accordingly.
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
