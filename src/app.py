# src/app.py
import os
from dotenv import load_dotenv

# 1. 必须最先加载环境变量！否则后面的 import 找不到 Key 会报错
load_dotenv()

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# 2. 环境变量加载完之后，再导入 graph
from src.agent import graph

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
        # Research Agent 可能需要跑几十秒，这里使用 ainvoke 等待结果
        # 注意：user_id 可以随机生成或固定，用于隔离会话
        inputs = {"messages": [("user", question)]}
        
        # 运行图
        result = await graph.ainvoke(inputs)
        
        # 3. 提取最终答案
        # LangGraph 的最后一条消息通常是 AI 的回答
        final_message = result["messages"][-1]
        answer_content = final_message.content

        # 4. 简单的后处理（符合比赛归一化要求，虽然评测会做，但我们最好先做）
        answer_content = answer_content.strip() 

        # 5. 返回比赛要求的 JSON 格式: {"answer": "..."}
        return JSONResponse(content={"answer": answer_content})

    except Exception as e:
        print(f"Error processing request: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    # PAI-EAS 部署时通常会指定端口，或者默认 8000
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)