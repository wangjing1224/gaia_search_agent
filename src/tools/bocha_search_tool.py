import asyncio
import json
import requests
import httpx
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from typing import List, Literal, Dict
from src.state.search_result import SearchResult
from src.config import BOCHA_API_KEY

class web_search_bocha_args(BaseModel):
    query: str = Field(..., description="The search query string.")
    max_results: int = Field(10, description="Max results count. Default is 10.")
    freshness: Literal["noLimit", "oneDay", "oneWeek", "oneMonth", "oneYear"] = Field(
        "noLimit",
        description="Time filter. Use 'oneDay' or 'oneWeek' for breaking news; 'noLimit' for general info."
    )

@tool('web_search_bocha', args_schema=web_search_bocha_args)
async def web_search_bocha(query: str, max_results: int = 10, freshness: str = "noLimit") -> List[SearchResult]:
    """
    [Alternative Web Search] A powerful search engine capable of retrieving high-quality web content.
    
    WHEN TO USE:
    1. Specifically effective for CHINESE language queries or entities related to China.
    2. As a fallback or complementary search when SerpApi results are insufficient.
    3. When you need a second opinion from a different search index.
    """
    
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
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("code") != 200 or not data.get("data"):
                print(f"Bocha API returned error or empty: {data}")
                return []
            
            web_pages = data["data"].get("webPages", {}).get("value", [])
            
            for page in web_pages:
                formatted_result: SearchResult = {
                    "query": query,
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
                    "query": query,
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