from src.llm.model import get_llm
from src.tools.tavily_tool import web_search_Tavily
from src.state.subgraph_search_state import SubgraphSearchState

llm = get_llm()

tools = [web_search_Tavily]

def subgraph_search_main_node(state: SubgraphSearchState):
    messages = state["messages"]
    response = llm.bind_tools(tools).invoke(messages)
    return {"messages": [response]}