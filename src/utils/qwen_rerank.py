import dashscope
from http import HTTPStatus
from typing import List, Dict, Any

from src.config import DASHSCOPE_API_KEY

dashscope.api_key = DASHSCOPE_API_KEY

def qwen_rerank_sync(query: str, documents: List[str], top_n: int = 5, instruct: str = "Given a web search query, retrieve relevant passages that answer the query.") -> List[str]:
    if not documents:
        return []
    
    # 1. 截断输入，确保总长度不超过模型限制、并且保留足够的上下文
    truncated_docs = [doc[:2000] for doc in documents]  # 每个文档最多保留2000字符
    
    try:
        # 2. 调用 DashScope API 进行 reranking
        response = dashscope.TextReRank.call(
            model="qwen3-rerank",
            query=query,
            documents=truncated_docs,
            top_n=top_n,
            instruct=instruct
        )
        
        if response.status_code == HTTPStatus.OK:
            reranked_docs = []
            
            for item in response.output.results:
                doc_index = item.index
                if 0 <= doc_index < len(documents):
                    reranked_docs.append(documents[doc_index])
            return reranked_docs
        
        else:
            print(f"Error: DashScope API returned status code {response.status_code}")
            # 直接返回原始文档列表的前 top_n 个，作为降级方案
            return documents[:top_n]
        
    except Exception as e:
        print(f"Exception during reranking: {str(e)}")
        # 直接返回原始文档列表的前 top_n 个，作为降级方案
        return documents[:top_n]
    
if __name__ == "__main__":
    query = "什么是文本排序模型？"
    documents = [
        "文本排序模型是一种用于对文本进行排序的机器学习模型，常用于信息检索和自然语言处理任务中。",
        "文本排序模型通过学习文本之间的相关性来对文本进行排序，常见的模型包括基于学习的排序模型和基于规则的排序模型。",
        "文本排序模型在搜索引擎中被广泛应用，用于根据用户的查询对搜索结果进行排序，以提供更相关的结果。",
        "文本排序模型广泛用于搜索引擎...",  # index 0 (相关)
        "今天天气真不错...",              # index 1 (无关)
        "深度学习改变了NLP领域...",       # index 2 (相关)
        "量子力学是...",              # index 3 (无关)
    ]
    
    reranked_docs = qwen_rerank_sync(query, documents, top_n=4)
    print("Reranked Documents:")
    for doc in reranked_docs:
        print(doc)