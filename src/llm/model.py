# src/llm/model.py
import os
from langchain_openai import ChatOpenAI

def get_llm(model_name: str = "qwen-plus"):
    """
    获取适配阿里 DashScope 的 LLM 实例
    """
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY is not set in environment variables.")

    llm = ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        temperature=0.01, # Research Agent 需要严谨，降低温度
        streaming=True
    )
    return llm