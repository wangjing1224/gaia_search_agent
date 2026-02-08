import asyncio
import json
import requests
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from typing import List, Literal, Dict
from src.state.search_result import SearchResult
from src.config import BOCHA_API_KEY

class web_search_bocha_args(BaseModel):
    query: str = Field(..., description="The search query.")
    max_results: int = Field(10, description="The maximum number of search results to return. Default is 10.")
    freshness: Literal["noLimit", "oneDay", "oneWeek", "oneMonth", "oneYear"] = Field(
        "noLimit",
        description="noLimit: No time limit; oneDay: Last 24 hours; oneWeek: Last 7 days; oneMonth: Last one month; oneYear: Last one year. Default is noLimit."
    )

@tool('web_search_bocha', args_schema=web_search_bocha_args)
async def web_search_bocha(query: str, max_results: int = 10, freshness: str = "noLimit") -> List[SearchResult]:
    """Use Bocha to search the web for relevant information.

    Args:
        query: The search query.
        max_results: The maximum number of search results to return. Default is 10.
        freshness: noLimit: No time limit; oneDay: Last 24 hours; oneWeek: Last 7 days; oneMonth: Last one month; oneYear: Last one year. Default is noLimit.noLimit is the first option,search algorithm will adjust the time range of search results based on the query automatically.
    Returns:
        The search results from Bocha.
    """
    return await asyncio.to_thread(web_search_bocha_sync, query, max_results, freshness)

def web_search_bocha_sync(query: str, max_results: int = 10, freshness: str = "noLimit") -> List[SearchResult]:
    url = "https://api.bochaai.com/v1/web-search"    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BOCHA_API_KEY}"
    }
    
    payload = {
        "query": query,
        "count": max_results,
        "freshness": freshness,
        "summary": True
    }
    
    cleaned_results: List[SearchResult] = []    
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        # 如果响应状态码为 200，表示请求成功
        if response.status_code == 200:
            data = response.json()
            
            if data.get("code") != 200 or not data.get("data"):
                print(f"Bocha API returned error or empty: {data}")
                return []
            
            web_pages = data["data"].get("webPages", {}).get("value", [])
            
            for page in web_pages:
                formatted_result: SearchResult = {
                    "title": page.get("name", "No Title"),
                    "content": page.get("summary") or page.get("snippet", ""),
                    "url": page.get("url", ""),
                    "source": "Bocha"
                }
                cleaned_results.append(formatted_result)
                
            return cleaned_results
        
        else:
            print(f"Bocha API request failed with status code {response.status_code}: {response.text}")
            return []
        
    except Exception as e:
        print(f"Error executing Bocha search: {str(e)}")
        return []

if __name__ == "__main__":
    result = asyncio.run(web_search_bocha.ainvoke({
        "query": "阿里巴巴2024年的ESG报告",
        "max_results": 5,
    }))
    print(result)