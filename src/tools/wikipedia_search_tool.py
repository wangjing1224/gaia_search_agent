from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List, Dict
from src.state.search_result import SearchResult
import asyncio
import wikipedia

class WikipediaSearchArgs(BaseModel):
    # 修改描述，提示用户输入关键词而不是句子
    query: str = Field(..., description="The specific entity or topic to search (e.g., 'Python', 'Elon Musk'). DO NOT use questions like 'What is...'.")
    lang: str = Field("en", description="Wikipedia language code (e.g., 'en', 'zh'). Default is 'en'.")
    top_k_results: int = Field(10, description="Number of entries to return.")

@tool("wikipedia_search", args_schema=WikipediaSearchArgs)
async def web_search_wikipedia(
    query: str, 
    lang: str = "en", 
    top_k_results: int = 10
) -> List[SearchResult]:
    """Use Wikipedia to search for authoritative definitions and background knowledge.
    
    Args:
        query: The specific entity or topic to search (e.g., 'Python', 'Elon Musk'). DO NOT use questions like 'What is...'.
        lang: Wikipedia language code (e.g., 'en', 'zh'). Default is 'en'.
        top_k_results: Number of entries to return. Default is 10.  
    Returns: 
        A list of SearchResult objects containing the search results from Wikipedia.
    """
    return await asyncio.to_thread(web_search_wikipedia_sync, query, lang, top_k_results)

def web_search_wikipedia_sync(query: str, lang: str = "en", top_k_results: int = 10) -> List[SearchResult]:
    
    cleaned_results: List[SearchResult] = []
    
    try:
        # 设置语言，执行搜索
        wikipedia.set_lang(lang)
        titles = wikipedia.search(query, results=top_k_results)
        
        # 获取每个标题的摘要和URL
        for title in titles:
            try:
                page = wikipedia.page(title, auto_suggest=False)
                content = page.summary
                url = page.url
                
                result: SearchResult = {
                    "title": title,
                    "content": content,
                    "url": url,
                    "source": "Wikipedia"
                }
                
                cleaned_results.append(result)
            except Exception as e:
                # 如果某个页面获取失败，记录错误但继续处理其他页面
                print(f"Error retrieving page for title '{title}': {str(e)}")
        
        
        return cleaned_results

    except Exception as e:
        print(f"Error during Wikipedia search: {str(e)}")
        return []

if __name__ == "__main__":
    # 测试工具调用
    print("Testing Wikipedia Search Tool...")
    
    try:
        result = asyncio.run(web_search_wikipedia.ainvoke({
            "query": "北京",
            "lang": "zh",
            "top_k_results": 2
        }))
        print("\n--- Search Results ---\n")
        print(result)
    except Exception as e:
        print(f"Error during tool invocation: {str(e)}")