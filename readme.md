# Gaia Search Agent (Research Agent)

这是一个基于 LangGraph 1.0 和 Qwen 模型构建的 Research Agent，集成了联网搜索功能。
本项目为阿里云 PAI-LangStudio 比赛参赛作品。

## 🛠️ 技术栈
- **框架**: LangGraph, LangChain
- **模型**: Qwen-Plus (通义千问)
- **工具**: Tavily Search (联网搜索)
- **部署**: FastAPI + Uvicorn

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
2. 配置环境变量
复制 .env.example 为 .env，并填入你的 Key：

代码段
DASHSCOPE_API_KEY=your_key
TAVILY_API_KEY=your_key
3. 本地启动
Bash
# 启动 API 服务
uvicorn src.app:app --host 0.0.0.0 --port 8000
📦 部署说明 (PAI-EAS)
启动命令: uvicorn src.app:app --host 0.0.0.0 --port 8000

端口配置: 8000