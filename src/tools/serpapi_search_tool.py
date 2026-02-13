import asyncio
from serpapi import GoogleSearch
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from src.state.search_result import SearchResult
from src.config import SERPAPI_API_KEY

class web_search_serpapi_args(BaseModel):
    query: str = Field(..., description="The search query. MUST use specific, high-entropy keywords.")
    max_results: int = Field(10, description="Number of results. Default 10.")
    engine: Literal["google", "bing","google_scholar"] = Field(
        "google", 
        description="Search engine choice. Use 'google' for general knowledge, news, and facts. Use 'google_scholar' ONLY as a backup for academic papers if Arxiv/Pubmed fails.")
    country:Literal["cn","us","uk"] = Field("us", description="The country to search in. Default is us.us: United States; uk: United Kingdom; cn: China.")
    time_range: str = Field(
        None, 
        description="CRITICAL for time-sensitive queries. "
                    "Formats: 'qdr:d' (past 24h), 'qdr:w' (past week), 'qdr:m' (past month), 'qdr:y' (past year). "
                    "Example: for 'recent AI news', use 'qdr:w'. For historical facts, leave None."
        )
    
@tool('web_search_serpapi', args_schema=web_search_serpapi_args)
async def web_search_serpapi(query: str, max_results: int = 10, engine: str = "google", country: str = "us", time_range: Optional[str] = None) -> List[SearchResult]:
    """
    [PRECISION SEARCH - BACKUP] A Google Search wrapper. Use SPARINGLY (High Cost).
    
    WHEN TO USE (Specific Triggers):
    1. FALLBACK: When 'web_search_bocha' returns 0 results or irrelevant info.
    2. VERIFICATION: When you need to cross-check a fact (e.g., a specific date) found elsewhere.
    3. ENGLISH SPECIFIC: When searching for obscure Western entities, academic papers, or foreign news not indexed in China.
    
    BEST PRACTICE:
    - Translate Chinese queries to English before using this tool for international topics.
    - Use 'time_range' if the question implies a specific timeframe.
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
                        "query": query,
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