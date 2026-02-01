from src.state.subgraph_search_state import SubgraphSearchState
from langchain_core.messages import ToolMessage
from src.llm.rerank_model import ranker_model_flash
from flashrank import Ranker, RerankRequest
import hashlib

def subgraph_search_rerank_node(state: SubgraphSearchState):
    query = state.get("current_query", "")
    
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
        {"id":i ,"text": res.get("content",""),"meta": res}
        for i, res in enumerate(cleaned_results)
    ]
    
    rerankrequest = RerankRequest(
        query = query,
        passages = passage_list,
    )
    
    reranked_list = ranker_model_flash.rerank(rerankrequest)
    
    # 提取重新排序后的结果，只取前5个
    reranked_results = []
    for reranked_item in reranked_list.reranked_passages[:5]:
        reranked_results.append(reranked_item.meta)
    
    return {
        "reranked_results": reranked_results,
    }