# src/app.py
import os
import json
from dotenv import load_dotenv

# 首先加载环境变量，确保在导入 graph 之前环境变量已经准备好
load_dotenv()

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# 环境变量加载完之后，再导入 graph
from src.agent import graph

# 定义一个自定义的 JSONResponse，确保输出的 JSON 是 UTF-8 编码且不转义中文
class CJSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"
    def render(self, content) -> bytes:
        return json.dumps(content, ensure_ascii=False).encode("utf-8")

app = FastAPI()

@app.post("/")
async def chat_endpoint(request: Request):
    try:
        # 1. 解析比赛要求的输入格式: {"question": "..."}
        data = await request.json()
        question = data.get("question")
        
        if not question:
            raise HTTPException(status_code=400, detail="Missing 'question' field")

        # 2. 调用 LangGraph
        inputs = {
            "messages": [("user", question)],
            "user_initial_query": question
        }
        
        # 运行图
        result = await graph.ainvoke(inputs)
        
        # 3. 提取最终答案
        # LangGraph 的最后一条消息通常是 AI 的回答
        final_message = result.get("final_answer", "")
        
        print("Final answer from graph:", final_message)
        
        return CJSONResponse(content={"answer": final_message})

    except Exception as e:
        print(f"Error processing request: {e}")
        return CJSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    # PAI-EAS 部署时通常会指定端口，或者默认 8000
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)