import asyncio
import time
import os
from src.config import PUBMED_API_KEY, PUBMED_EMAIL
from typing import List
from pydantic import BaseModel, Field
from src.state.search_result import SearchResult
from Bio import Entrez
from langchain_core.tools import tool

Entrez.email = PUBMED_EMAIL
Entrez.api_key = PUBMED_API_KEY


class paper_search_pubmed_args(BaseModel):
    query: str = Field(..., description="The search query.")
    max_results: int = Field(15, description="The maximum number of search results to return. Default is 15.")

@tool('paper_search_pubmed', args_schema=paper_search_pubmed_args)
async def paper_search_pubmed(query: str, max_results: int = 15) -> List[SearchResult]:
    """Use PubMed to search for relevant academic papers.

    Args:
        query: The search query.
        max_results: The maximum number of search results to return. Default is 15.
    Returns:
        The search results from PubMed.
    """
    return await asyncio.to_thread(paper_search_pubmed_sync, query, max_results)

def paper_search_pubmed_sync(query: str, max_results: int = 15) -> List[SearchResult]:
    """Use PubMed to search for relevant academic papers.

    Args:
        query: The search query.
        max_results: The maximum number of search results to return. Default is 15.
    Returns:
        The search results from PubMed.
    """
    
    cleaned_results: List[SearchResult] = []
    
    try:
        # 1. 使用 Entrez.esearch 搜索 PubMed，获取相关论文的 ID 列表
        search_handle = Entrez.esearch(
            db="pubmed",
            term=query,
            retmax=max_results,
            sort="relevance",
        )
        
        search_results = Entrez.read(search_handle)
        search_handle.close()
        
        pmid_list = search_results["IdList"]
        
        if not pmid_list:
            print("⚠️ 警告: PubMed esearch 返回的结果中没有 ID 列表")
            return []
    
        # 2.根据 ID 列表使用 Entrez.efetch 获取论文的详细信息
        search_handle = Entrez.efetch(
            db="pubmed",
            id=pmid_list,
            remode="xml",
        )
        articls = Entrez.read(search_handle)
        search_handle.close()
        # PubMed 的 efetch 返回的 XML 结构中，论文信息通常在 "PubmedArticle" 键下
        pubmed_articles = articls.get("PubmedArticle", [])
        
        # 3. 提取论文的标题、摘要、URL 等信息，并构建 SearchResult 对象
        for article in pubmed_articles:
            try:
                # 获取文章基本信息
                article_data = article['MedlineCitation']['Article']
                article_title = article_data.get('ArticleTitle', 'No Title')
                
                article_text = ""
                if 'Abstract' in article_data:
                    abstract_list = article_data['Abstract'].get('AbstractText', [])
                    if isinstance(abstract_list, list):
                        article_text = " ".join([str(x) for x in abstract_list])
                    else:
                        article_text = str(abstract_list)
                
                pmid = article['MedlineCitation']['PMID']
                article_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                
                # 获取年份信息
                try:
                    pub_date = article_data.get('Journal', {}).get('JournalIssue', {}).get('PubDate', {})
                    year = pub_date.get('Year', '')
                    if not year and 'MedlineDate' in pub_date:
                        year = pub_date['MedlineDate']
                except Exception as e:
                    print(f"Error extracting publication year: {str(e)}")
                    year = "Unknown"
                
                # 组装内容：加上年份和期刊名，有助于大模型回答 "哪一年发表" 的问题
                journal_name = article_data.get('Journal', {}).get('Title', 'Unknown Journal')
                final_content = f"Published in {year} ({journal_name}). Abstract: {article_text[:800]}"
                
                formatted_result: SearchResult = {
                    "title": article_title,
                    "content": final_content,
                    "url": article_url,
                    "source": "PubMed"
                }
                cleaned_results.append(formatted_result)
                
            except Exception as e:
                print(f"Error processing article: {str(e)}")
                continue
        
        return cleaned_results
    except Exception as e:
        print(f"Error during PubMed search: {str(e)}")
        return []
    
if __name__ == "__main__":
    # 简单测试
    result = asyncio.run(paper_search_pubmed.ainvoke({
        "query": "cancer immunotherapy",
        "max_results": 1
    }))
    print(result)