import os
from dotenv import load_dotenv
load_dotenv()

# DashScope API Key
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")

# Tavily Search API Key
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# PubMed API Key
PUBMED_API_KEY = os.getenv("PUBMED_API_KEY")
PUBMED_EMAIL = os.getenv("PUBMED_EMAIL")

# BoCha API Key
BOCHA_API_KEY = os.getenv("BOCHA_API_KEY")

# SerpApi API Key
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

# Jina API Key
JINA_API_KEY = os.getenv("JINA_API_KEY")