from typing import TypedDict, Annotated, List, Dict
import operator

class SearchResult(TypedDict):
    title: str
    content: str
    url: str
    source: str