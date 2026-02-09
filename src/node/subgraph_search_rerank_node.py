from src.state.subgraph_search_state import SubgraphSearchState
from langchain_core.messages import ToolMessage
from src.llm.rerank_model import ranker_model_flash
from src.utils.qwen_rerank import qwen_rerank_sync
from flashrank import Ranker, RerankRequest
import hashlib

def subgraph_search_rerank_node(state: SubgraphSearchState):
    query = state.get("current_query", "")
    search_loop_count = state.get("search_loop_count", 0) + 1
    
    # 这里可以添加重新排序的逻辑
    serach_result = state.get("search_results", [])
    
    print(f"Rerank total {len(serach_result)} results.")
    
    # 简单去重
    unique_results = {}
    for result in serach_result:
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
    
    # 构造rerank输入
    passage_list = [
        {"content": res.get("content",""), "meta": res}
        for res in cleaned_results
    ]
    
    # 使用Qwen模型进行rerank
    reranked_docs = qwen_rerank_sync(query, [p["content"] for p in passage_list], top_n=5)
    
    # 根据rerank结果重新构建reranked_results
    reranked_results = []
    for doc in reranked_docs:
        for p in passage_list:
            if p["content"] == doc:
                reranked_results.append(p["meta"])
                break
    
    return {
        "search_results": "clear",  # 清空原有搜索结果
        "reranked_results": reranked_results,
        "search_loop_count": search_loop_count
    }