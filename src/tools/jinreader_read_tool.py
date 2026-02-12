import asyncio
import requests
import math
import httpx
from typing import List,Literal
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.config import JINA_API_KEY
from src.utils.web_paginate import paginate_web_content
from src.utils.web_content_clean import clean_web_markdown_content
from src.utils.web_pages_cache import web_cache

PAGE_SIZE = 3000  # 每页内容的最大字符数，超过部分会被截断

InstructOptions = Literal[
    "Given a web search query, retrieve relevant passages that answer the query.",
    "Retrieve semantically similar text."
]

class web_read_jina_args(BaseModel):
    url: str = Field(..., description="The specific URL to scrape. MUST start with http:// or https://.")
    query: str = Field(..., description="The original question or keyword should focus on web content. This helps the reader extract relevant information.")
    instruct: InstructOptions = Field(
        "Given a web search query, retrieve relevant passages that answer the query.",
        description="Instruction for the reader model."
    )

@tool('web_read_jina', args_schema=web_read_jina_args)
async def web_read_jina(url: str, query: str, instruct: InstructOptions = "Given a web search query, retrieve relevant passages that answer the query.") -> str:
    """
    [Web Page Reader] Deeply reads and extracts full content from a SPECIFIC URL.
    
    WHEN TO USE:
    1. You have found a promising URL from a search tool (SerpApi/Bocha) and need to read its details.
    2. The user explicitly provides a link to analyze.
    
    DO NOT USE:
    - Do not use this for general keyword searching. It requires a valid URL.
    """
    
    if not url.startswith("http://") and not url.startswith("https://"):
        print(f"Invalid URL: {url}. URL must start with http:// or https://")
        return "Error: Invalid URL. URL must start with http:// or https://"
    
    cache_content = web_cache.get(url)
    if cache_content:
        print(f"Cache hit for URL: {url}")
        full_content = cache_content
        
    else:
        print(f"Cache miss for URL: {url}. Fetching content from Jina Reader.")
        
        jina_url = f"https://r.jina.ai/{url}"
        
        headers = {
            "Authorization": f"Bearer {JINA_API_KEY}"
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(jina_url, headers=headers)
                
            if response.status_code == 200:
                raw_content = response.text
                full_content = clean_web_markdown_content(raw_content)
                web_cache.set(url, full_content)  # 将内容存入缓存
            elif response.status_code == 429:
                print(f"Error: Rate limit exceeded for Jina Reader while accessing URL {url}")
                return "Error: Rate limit exceeded for Jina Reader. Please try again later."
            else:
                print(f"Error: Failed to read page. Status Code: {response.status_code}, URL: {url}")
                return f"Error: Failed to read page. Status Code: {response.status_code}, URL: {url}"
        except Exception as e:
            print(f"Error during Jina Reader request: {str(e)}, URL: {url}")
            return f"Error: An exception occurred while reading the page. Details: {str(e)}, URL: {url}"
        
    paginate_content = paginate_web_content(full_content=full_content, query=query, page_size=PAGE_SIZE, instruct=instruct)
    
    result_content = (
        f"SOURCE URL: {url}\n"
        f"{paginate_content}"
    )
    
    return result_content
    
def web_read_jina_sync(url: str, query: str, instruct: InstructOptions = "Given a web search query, retrieve relevant passages that answer the query.") -> str:
    
    # 简单的输入验证，确保 URL 以 http 或 https 开头
    if not url.startswith("http://") and not url.startswith("https://"):
        print(f"Invalid URL: {url}. URL must start with http:// or https://")
        return "Error: Invalid URL. URL must start with http:// or https://"
    
    # 检查缓存是否存在当前请求url
    cache_content = web_cache.get(url)
    if cache_content:
        print(f"Cache hit for URL: {url}")
        full_content = cache_content
    
    else:
        print(f"Cache miss for URL: {url}. Fetching content from Jina Reader.")
    
        jina_url = f"https://r.jina.ai/{url}"
        
        headers = {
            "Authorization": f"Bearer {JINA_API_KEY}"
        }
        
        try:
            response = requests.get(jina_url, headers=headers, timeout=15)
                    
            if response.status_code == 200:
                
                raw_content = response.text
                
                # 清洗内容，去除多余的空白和特殊字符，保留基本的文本结构
                full_content = clean_web_markdown_content(raw_content)
                
                web_cache.set(url, full_content)  # 将内容存入缓存
            
            elif response.status_code == 429:
                print(f"Error: Rate limit exceeded for Jina Reader while accessing URL {url}")
                return "Error: Rate limit exceeded for Jina Reader. Please try again later."
            
            else:
                print(f"Error: Failed to read page. Status Code: {response.status_code}, URL: {url}")
                return f"Error: Failed to read page. Status Code: {response.status_code}, URL: {url}"
        except Exception as e:
            print(f"Error during Jina Reader request: {str(e)}, URL: {url}")
            return f"Error: An exception occurred while reading the page. Details: {str(e)}, URL: {url}"
    
    # 对内容进行分页处理，返回指定页码的内容
    paginate_content = paginate_web_content(full_content=full_content, query=query, page_size=PAGE_SIZE, instruct=instruct)
    
    # 构造返回结果，包含当前页内容和分页信息
    result_content = (
        f"SOURCE URL: {url}\n"
        f"{paginate_content}"
    )
    
    return result_content
    
if __name__ == "__main__":
    # 简单测试
    test_url = "https://en.wikipedia.org/wiki/Artificial_intelligence"
    result1 = asyncio.run(web_read_jina.ainvoke({
        "url": test_url,
        "query": "What is artificial intelligence?",
        "page_number": 1
    }))
    result2 = asyncio.run(web_read_jina.ainvoke({
        "url": test_url,
        "query": "What is artificial intelligence?",
        "page_number": 2
    }))
    print(result1) 
    print(result2)  