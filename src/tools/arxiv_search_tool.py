import asyncio
from langchain_community.retrievers import ArxivRetriever
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List
from src.state.search_result import SearchResult

import arxiv

class paper_search_arxiv_args(BaseModel):
    query: str = Field(..., description="The search query.The query must be English.")
    max_results: int = Field(15, description="The maximum number of search results to return.Default is 15.")
    
@tool('paper_search_arxiv', args_schema=paper_search_arxiv_args)
async def paper_search_arxiv(query: str, max_results: int = 15) -> List[SearchResult]:
    """Use Arxiv to search for relevant academic papers.

    Args:
        query: The search query. The query must be English.
        max_results: The maximum number of search results to return. Default is 15.
    Returns:
        The search results from Arxiv.
    """
    return await asyncio.to_thread(paper_search_arxiv_sync, query, max_results)

def paper_search_arxiv_sync(query: str, max_results: int = 15) -> List[SearchResult]:
    """Use Arxiv to search for relevant academic papers.

    Args:
        query: The search query. The query must be English.
        max_results: The maximum number of search results to return. Default is 15.
    Returns:
        The search results from Arxiv.
    """
    
    cleaned_results: List[SearchResult] = []
    
    try:
        
        arxiv_client = arxiv.Client()
        arxiv_retriever = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        results = arxiv_client.results(arxiv_retriever)
        
        if not results:
            print("⚠️ 警告: ArxivRetriever 返回的结果格式不正确，预期是列表")
            return []
        
        for result in results:
            
            papaer_title = result.title or "No Title"
            paper_url = result.entry_id or f"https://arxiv.org/abs/{result.get_short_id()}"
            paper_content = result.summary[:800] if result.summary else ""
            
            
            # 这里的 result 结构取决于 ArxivRetriever 的实现
            formatted_result: SearchResult = {
                "title": papaer_title,
                "content": paper_content,
                "url": paper_url,
                "source": "Arxiv"
            }
            cleaned_results.append(formatted_result)
        
        return cleaned_results
    except Exception as e:
        print(f"Error during Arxiv search: {str(e)}")
        return []
    
if __name__ == "__main__":
    # 简单测试
    result = asyncio.run(paper_search_arxiv.ainvoke({
        "query": "llm",
        "max_results": 5
    }))
    print(result)