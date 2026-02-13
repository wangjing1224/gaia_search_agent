import math
from src.utils.qwen_rerank import qwen_rerank_sync

def paginate_web_content(full_content, query: str, instruct: str, page_size: int = 3000) -> str:
    
    overlap_size = 800  # 页面重叠部分的大小，确保上下文连续
    
    if not full_content:
        return "The url content is empty."
    
    total_length = len(full_content)
    total_pages = math.ceil(total_length / page_size)
    
    # 完整网页内容切片，构造rerank输入,每个切片包含 page_size 字符，且相邻切片有 overlap_size 字符的重叠,确保上下文连续
    documents_list = []
    start = 0
    while start < total_length:
        end = min(start + page_size, total_length)
        chunk = full_content[start:end]
        documents_list.append(chunk)
        if end == total_length:
            break
        start = end - overlap_size  # 下一页开始位置，重叠部分确保上下文连续
    
    
    # 使用Qwen模型进行rerank，确保重要内容优先展示
    reranked_docs = qwen_rerank_sync(query,documents_list, instruct=instruct, top_n=5)
    
    # 拼接rerank后的内容，并添加分页信息
    reranked_content = ""
    for i, doc in enumerate(reranked_docs):
        reranked_content += (
            f"PAGE {i+1}:\n"
            f"{doc}\n"
        )
    
    return_content = (
        f"This web main content:\n{reranked_content}"
    )
    return return_content