from src.state.subgraph_search_state import SubgraphSearchState
from langchain_core.messages import ToolMessage
from src.llm.rerank_model import ranker_model_flash
from src.utils.qwen_rerank import qwen_rerank_sync
from flashrank import Ranker, RerankRequest

from src.state.subgraph_search_rerank_result import RerankResult ,  RerankResultItem, RerankItem

import hashlib

def subgraph_search_rerank_node(state: SubgraphSearchState):
    # 更新搜索循环次数
    search_loop_count = state.get("search_loop_count", 0) + 1
    
    # 得到这一轮查询的所有搜索结果
    serach_results = state.get("search_results", [])
    
    print(f"Rerank total {len(serach_results)} results.")
    
    # 定义一个列表来存储所有rerank结果项
    rerank_result_items = []
    
    rerank_results :RerankResult = {
        "loop": search_loop_count,
        "rerank_result_items": rerank_result_items
    }
    
    # 如果没有搜索结果，直接返回
    if not  serach_results:
        return {
            "search_results": "clear",  # 清空原有搜索结果
            "reranked_results": [rerank_results],# 这里即使没有搜索结果，也要更新rerank_results，告诉主节点这一轮没有有用的搜索结果
            "search_loop_count": search_loop_count
        }
    
    # 如果有搜索结果，进行rerank
    # 将搜索结果通过问题进行分类，方便后续rerank模型根据问题对结果进行针对性排序
    classify_by_query = {}
    for result in serach_results:
        query = result.get("query","")
        if query not in classify_by_query:
            classify_by_query[query] = []
        formatted_result: RerankItem = {
            "title": result.get("title",""),
            "content": result.get("content",""),
            "url": result.get("url",""),
            "source": result.get("source","")
        }
        classify_by_query[query].append(formatted_result)
    
    # 对每个查询的问题搜索结果进行去重和rerank
    for query_key in classify_by_query.keys():
        # 获取当前查询的问题搜索结果
        results = classify_by_query[query_key]
        
        #对每个query_key的结果进行去重
        unique_results = {}
        for result in results:
            title = result.get("title","")
            content = result.get("content","")
            url = result.get("url","")
            
            # 生成唯一键
            if url and url != "":
                unique_key = url
            else:
                if not content:
                    continue
                else:
                    content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
                    unique_key = f"{title}_{content_hash}"
            
            # 去重
            if unique_key not in unique_results:
                unique_results[unique_key] = result
            
        # 无重复结果列表
        cleaned_results = list(unique_results.values())
        
        # 将去重后的结果进行rerank
        # 构造rerank输入
        passage_list = [
            {"content": res.get("content",""), "meta": res}
            for res in cleaned_results
        ]
        # 使用Qwen模型进行rerank
        reranked_docs = qwen_rerank_sync(query_key, [p["content"] for p in passage_list], top_n=5)
        # 根据rerank结果重新构建reranked_results
        reranked_results = []
        for doc in reranked_docs:
            for p in passage_list:
                if p["content"] == doc:
                    reranked_results.append(p["meta"])
                    break
        
        # 将当前query_key的rerank结果添加到总的rerank结果中
        rerank_result_item : RerankResultItem = {
            "query": query_key,
            "rerank_items": reranked_results
        }
        
        # 将当前query_key的rerank结果项添加到总的rerank结果列表中
        rerank_result_items.append(rerank_result_item)
    
    rerank_results = {
        "loop": search_loop_count,
        "rerank_result_items": rerank_result_items
    }
    
    return {
        "search_results": "clear",  # 清空原有搜索结果
        "reranked_results": [rerank_results],
        "search_loop_count": search_loop_count
    }