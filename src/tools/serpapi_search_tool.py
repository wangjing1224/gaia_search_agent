import asyncio
from serpapi import GoogleSearch
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from src.state.search_result import SearchResult
from src.config import SERPAPI_API_KEY

class web_search_serpapi_args(BaseModel):
    query: str = Field(..., description="The search query.")
    max_results: int = Field(10, description="The maximum number of search results to return. Default is 10.")
    engine: Literal["google", "bing","google_scholar"] = Field("google", description="The search engine to use. Default is google. google: Google Search; bing: Bing Search; google_scholar: Google Scholar.Select 'google_scholar' to search for academic papers.'google' and 'bing' are for general web search.")
    country:Literal["cn","us","uk"] = Field("us", description="The country to search in. Default is us.us: United States; uk: United Kingdom; cn: China.")
    time_range: str = Field(
        None, 
        description="Optional time range. Examples: 'qdr:y' (past year), 'cdr:1,cd_min:2020,cd_max:2022' (specific years).Default is None, which means no time filter. Notice:Static facts are usually not affected by time range, while news and recent events are more likely to be influenced by time range. For general web search, you can set an appropriate time range to get more relevant results. For academic paper search using google_scholar, it's often useful to set a time range to find the most recent research."
    )
    
@tool('web_search_serpapi', args_schema=web_search_serpapi_args)
async def web_search_serpapi(query: str, max_results: int = 10, engine: str = "google", country: str = "us", time_range: Optional[str] = None) -> List[SearchResult]:
    """Use SerpAPI to search the web for relevant information.

    Args:
        query: The search query.
        max_results: The maximum number of search results to return. Default is 10.
        engine: The search engine to use. Default is google. google: Google Search; bing: Bing Search; google_scholar: Google Scholar.Select 'google_scholar' to search for academic papers.'google' and 'bing' are for general web search.
        country: The country to search in. Default is us.us: United States; uk: United Kingdom; cn: China.
        time_range: Optional time range. Examples: 'qdr:y' (past year), 'cdr:1,cd_min:2020,cd_max:2022' (specific years).Default is None, which means no time filter. Notice:Static facts are usually not affected by time range, while news and recent events are more likely to be influenced by time range. For general web search, you can set an appropriate time range to get more relevant results. For academic paper search using google_scholar, it's often useful to set a time range to find the most recent research.
    Returns:
        The search results from SerpAPI.
    """
    return await asyncio.to_thread(web_search_serpapi_sync, query, max_results, engine, country, time_range)

def web_search_serpapi_sync(query: str, max_results: int = 10, engine: str = "google", country: str = "us", time_range: Optional[str] = None) -> List[SearchResult]:
    
    cleaned_results: List[SearchResult] = []
    
    params = {
        "api_key": SERPAPI_API_KEY,
        "engine": engine,
        "q": query,
        "num": max_results,
        "gl": country,
        "hl": "en"
    }
    
    if time_range and engine != "google_scholar":
        params["tbs"] = time_range
        
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # 处理不同搜索引擎的结果格式
        if engine == "google_scholar":
            if "organic_results" in results:
                for result in results["organic_results"]:
                    title = result.get("title", "No Title")
                    
                    summary = result.get("publication_info", {}).get("summary", "")
                    snippet = result.get("snippet", "")
                    
                    content = f"Summary: {summary}. Snippet/Abstract: {snippet}"
                    
                    formatted_result: SearchResult = {
                        "title": title,
                        "content": content,
                        "url": result.get("link", ""),
                        "source": "SerpAPI_Google Scholar"
                    }
                    cleaned_results.append(formatted_result)
        else:
            # 优先查看是否有 Knowledge Graph (知识图谱) 结果
            if "knowledge_graph" in results and results["knowledge_graph"]:
                kg = results["knowledge_graph"]
                title = kg.get("title", "No Title")
                description = kg.get("description", "")
                url = kg.get("source", {}).get("link", "")
                formatted_result: SearchResult = {
                    "title": f"{title} (Knowledge Graph)", 
                    "content": description,
                    "url": url,
                    "source": f"SerpAPI_{engine.capitalize()}_KnowledgeGraph"
                }
                cleaned_results.append(formatted_result)
            
            # 新闻结果
            news_results = results.get("news_results", []) or results.get("top_stories", [])
            for news in news_results:
                news_title = news.get("title", "No Title")
                news_snippet = news.get("snippet", "")
                news_date = news.get("date", "Recent")
                news_url = news.get("link", "")
                news_content = f"News: {news_snippet} (Published: {news_date})"
                formatted_result: SearchResult = {
                    "title": f"{news_title} (News)",
                    "content": news_content,
                    "url": news_url,
                    "source": f"SerpAPI_{engine.capitalize()}_News"
                }
                cleaned_results.append(formatted_result)
            
            # 遍历自然搜索结果
            if "organic_results" in results:
                for result in results["organic_results"]:
                    title = result.get("title", "No Title")
                    formatted_result: SearchResult = {
                        "title": title,
                        "content": result.get("snippet", ""),
                        "url": result.get("link", ""),
                        "source": f"SerpAPI_{engine.capitalize()}"
                    }
                    cleaned_results.append(formatted_result)
        
        return cleaned_results
    
    except Exception as e:
        print(f"Error during SerpAPI search: {str(e)}")
        return []
    
if __name__ == "__main__":
    result1 = asyncio.run(web_search_serpapi.ainvoke({
        "query": "Elon Musk ",
        "max_results": 5,
        "engine": "google",
        "country": "us",
        # "time_range": "qdr:y"
    }))
    # result2 = asyncio.run(web_search_serpapi.ainvoke({
    #     "query": "LLM research papers",
    #     "max_results": 5,
    #     "engine": "google_scholar",
    #     "country": "us",
    # }))
    print(result1)
    # print(result2)