import os
import asyncio
# 1. 引入 dotenv 用于加载环境变量
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from typing import List, Dict
from src.state.search_result import SearchResult

# 2. 在获取 Key 之前，先加载环境变量
# 这会寻找当前目录或父级目录下的 .env 文件并加载
load_dotenv()

tavily_key = os.environ.get("TAVILY_API_KEY")

# 3. 最好加个简单的检查，防止 Key 没配好时报错看不懂
if not tavily_key:
    # 这里的 print 只是为了调试，实际生产中可以用 logging
    print("⚠️ 警告: 未找到 TAVILY_API_KEY，请检查 .env 文件")

class web_search_Tavily_args(BaseModel):
    query: str = Field(..., description="The search query.")
    max_results: int = Field(10, description="The maximum number of search results to return.Default is 10.")

@tool('web_search_Tavily', args_schema=web_search_Tavily_args)
async def web_search_Tavily(query: str ,max_results: int = 10) -> List[SearchResult]:
    """Use Tavily to search the web for relevant information.

    Args:
        query: The search query.
        max_results: The maximum number of search results to return. Default is 10.
    Returns:
        The search results from Tavily.
    """
    return await asyncio.to_thread(web_search_Tavily_sync, query, max_results)

def web_search_Tavily_sync(query: str ,max_results: int = 10) -> List[SearchResult]:
    """Use Tavily to search the web for relevant information.

    Args:
        query: The search query.
        max_results: The maximum number of search results to return. Default is 10.
    Returns:
        The search results from Tavily.
    """
    
    # 实例化 TavilySearchResults
    tavil = TavilySearchResults(
        tavily_api_key=tavily_key, # 注意：有些旧版本参数名是 api_key，新版建议用 tavily_api_key
        max_results=max_results
    )
    
    cleaned_results: List[SearchResult] = []
    
    # 执行搜索
    # try-except 块有助于在单独测试时看清具体网络错误
    try:
        results = tavil.invoke(query)
        
        # 简单的容错处理，防止 results 为空或格式不对
        if not results:
            return []
        
        for result in results:
            formated_result: SearchResult = {
                "title": result.get("title", ""),
                "content": result.get("content", ""),
                "url": result.get("url", "None"),
                "source": "Tavily"
            }
            cleaned_results.append(formated_result)
        
        return cleaned_results
    
    except Exception as e:
        print(f"Error executing Tavily search: {str(e)}")
        return []
    
    
if __name__ == "__main__":
    # Example usage
    # 确保上面 load_dotenv() 已经执行
    print(f"Current Key: {tavily_key[:5]}******") # 打印 Key 的前几位确认加载成功
    
    try:
        result = asyncio.run(web_search_Tavily.ainvoke({
            "query": "What is LangGraph?",
            "max_results": 1
        }))
        print("\n--- Search Results ---\n")
        print(result)
    except Exception as e:
        print(f"\nError running tool: {e}")