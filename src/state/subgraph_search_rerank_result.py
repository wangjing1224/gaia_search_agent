from typing import Annotated, List, Union, Literal, TypedDict

class RerankItem(TypedDict):
    title: str
    content: str
    url: str
    source: str
    
class RerankResultItem(TypedDict):
    query: str
    rerank_items: List[RerankItem]

class RerankResult(TypedDict):
    loop: int
    rerank_result_items: List[RerankResultItem]
