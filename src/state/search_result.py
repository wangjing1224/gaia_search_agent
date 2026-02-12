from typing import TypedDict, Annotated, List, Dict
import operator

class SearchResult(TypedDict):
    query: str
    title: str
    content: str
    url: str
    source: str