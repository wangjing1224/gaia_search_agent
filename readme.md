# 🌐 Gaia Research Agent - 企业级多跳搜索与推理智能体

Gaia Research Agent 是一个基于 **LangGraph** 构建的高级研究型智能体（Research Agent）。本项目最初为应对“阿里云 PAI-LangStudio 挑战赛”中严苛的多跳推理、长文本信息验证与零幻觉要求而设计。

与传统的单轮对话或简单的 RAG 系统不同，Gaia 具备**动态技能加载 (S.O.P Routing)**、**嵌套子图搜索循环 (Iterative Search Subgraph)**、**安全的本地代码沙盒**以及**多线程安全的网页缓存**等生产级特性，能够在不微调模型的前提下，通过纯 Agent 工程自主规划并解决极其复杂的真实世界事实考证难题。

## ✨ 核心亮点 (Key Features)

### 1. 🧠 动态 S.O.P 技能加载与路由 (Skill-based Playbook Routing)

摒弃了传统的“超级大 Prompt”做法，创新性地引入了动态技能加载机制。

- **按需加载**：Agent 首轮会根据用户的查询类型（如：多跳实体溯源、学术文献检索、时间与年份计算等），从 Markdown 库中动态加载对应的 S.O.P（标准作业程序）。
    
- **行为约束**：每个 Playbook 包含特定的战术工作流（Tactical Workflow），严格约束大模型的思考路径，极大降低了复杂任务中的幻觉率和逻辑偏离。
    

### 2. 🔍 嵌套子图驱动的深度搜索循环 (Iterative Search Subgraph)

构建了独立的 `search_subgraph`，将搜索行为从主脑中解耦，形成闭环的侦察兵机制。

- **多源情报融合**：集成 Bocha（主搜）、SerpApi（Google/Scholar 备用）、Arxiv（数理学术）、PubMed（生物医学）四大检索源。
    
- **自适应降级与重试**：子图内置最大 5 轮的搜索循环。如果浅层 Snippet 无法回答问题，会自动触发 **Deep Reading (Jina Reader)** 提取完整网页；如果当前关键词无果，会自动结合历史失败经验重写关键词甚至切换语言（如请求英译）。
    
- **内容重排与提纯**：对杂乱的搜索结果进行 MD5 去重，并通过 `Qwen3-rerank` 进行语义重排，提取 Top-N 核心段落反馈给主节点，大幅节省 Token 消耗并提高命中率。
    

### 3. 🛡️ 工业级的工程实现与性能优化

展示了扎实的 Python 后端与并发编程能力：

- **并发工具调用**：在节点（如 `subgraph_search_searchtools_execution_node`）中大量使用 `asyncio.gather`，实现多搜索工具的并发调用，大幅缩短长链路耗时。
    
- **线程安全的内存缓存 (RW Lock)**：为应对高频的相同 URL 抓取，手写了**写优先的读写锁 (`WritePriorityRWLock`)**，结合 `OrderedDict` 实现线程安全的 LRU 网页内容缓存。
    
- **安全的代码执行沙盒**：针对时间计算和规则统计任务，实现了基于 `multiprocessing` 的隔离 Python REPL 工具。内置超时强杀（Timeout Terminate）、禁用危险包（`os`, `sys` 等）以及堆栈信息清洗，确保系统安全。
    
- **极致的网页清洗引擎**：针对 Jina 抓取的全量网页，手写了基于正则表达式的高效 Markdown 清洗器 (`clean_web_markdown_content`)，精准剥离维基百科目录、广告、导航栏、多语言尾注等垃圾信息。
    

### 4. 🔄 结构化输出与反思机制 (Reflection & Self-Correction)

- 引入了 **“裁判”机制 (Evaluation System Prompt)**：在输出最终答案前，强制模型审查“是否基于搜索到的证据”、“是否存在推理缺陷”。
    
- **异常捕获与容错**：采用最严苛的 `JsonOutputParser` 方案，即使大模型返回破损 JSON，系统也不会 Crash，而是优雅拦截并触发重试。
    
- 若判定证据不足或逻辑断裂，Agent 会触发 `thinking_process_is_error` 分支，将具体的缺陷反馈给大脑进行重新搜索或重新加载技能，形成完整的自我纠错闭环。
    

---

## 🏗️ 系统架构设计 (Architecture)

系统由 **Main Graph（主脑控制流）** 和 **Search Subgraph（深度搜索子图）** 两部分嵌套协同工作。

### 主图编排 (Main Graph)

主脑负责识别意图、加载技能 S.O.P、调用工具并进行最终的裁判校验。

### 搜索子图循环 (Search Subgraph)

复杂的搜索行为被剥离为子图。工作流：主节点规划搜索词 ➡️ 并发执行各路Search API ➡️ 去重与Qwen Rerank ➡️ 判断是否达成目标（最多循环5次） ➡️ 触发 Jina 深度阅读(如需) ➡️ 汇总证据返回主脑。

---

## 💻 核心代码目录解析

Plaintext

```
gaia_search_agent/
├── src/
│   ├── agent.py                 # Graph 的暴露入口
│   ├── app.py                   # FastAPI 接口，提供标准 HTTP 评测服务
│   ├── graph.py                 # 主图 (Main Graph) 核心编排逻辑
│   ├── llm/                     # LLM 模型与 Rerank 模型初始化
│   ├── node/                    # 所有的执行节点 (Node)
│   ├── route/                   # 条件边路由逻辑 (Conditional Edges)
│   ├── schemas/                 # Pydantic 结构化输出定义
│   ├── skills/                  # S.O.P 技能库 (Markdown)
│   ├── state/                   # 跨节点流转的状态定义
│   ├── subgraph/                # 搜索子图的定义
│   ├── tools/                   # 具体的外部工具集成 (Arxiv, Bocha, Jina, REPL 等)
│   └── utils/                   # 核心工程组件库 🔧
│       ├── WritePriorityRWLock.py  # 自定义写优先读写锁
│       ├── web_pages_cache.py      # LRU 网页内存缓存
│       ├── web_content_clean.py    # Markdown 垃圾清洗器
│       ├── web_paginate.py         # 长文本重叠分块与重排机制
│       └── qwen_rerank.py          # Qwen-Rerank 接口调用
├── .env.example                 # 环境变量模板
├── langgraph.json               # LangGraph CLI 配置文件
└── requirements.txt
```

---

## 🛠️ 技术栈 (Tech Stack)

- **AI 框架**: LangGraph 1.0, LangChain Core
    
- **大语言模型**: 通义千问 (Qwen-Max) 驱动逻辑规划，Qwen3-Rerank 驱动语义重排。
    
- **搜索与数据源**: Bocha API (主搜), SerpApi (备用), Arxiv & PubMed (专业文献), Jina Reader (深度网页抓取)。
    
- **后端框架**: FastAPI, Uvicorn (异步非阻塞支持)
    
- **工程组件**: `asyncio` (并发控制), `multiprocessing` (代码沙盒), 自定义 `RWLock` (读写锁并发控制)。
    

---

## 🚀 快速开始 (Quick Start)

### 1. 环境准备

Bash

```
# 克隆仓库
git clone https://github.com/wangjing1224/gaia_search_agent.git
cd gaia_search_agent

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，填入所需的 API Keys：

代码段

```
DASHSCOPE_API_KEY=your_dashscope_key
BOCHA_API_KEY=your_bocha_key
SERPAPI_API_KEY=your_serpapi_key
JINA_API_KEY=your_jina_key
```

### 3. 启动可视化调试 UI (🌟 强烈推荐)

本项目原生支持 **LangGraph Studio**。这是测试和观测多跳 Agent 最佳的方式，你可以直观地看到每个节点的触发、子图的嵌套循环以及跨节点的状态（State）流转。

**👉 运行以下命令启动本地开发服务器与可视化 UI：**

Bash

```
# 确保你已经安装了 langgraph-cli
langgraph dev
```

执行后，终端会输出一个 Web UI 链接（通常为 `http://localhost:2024`）。在浏览器中打开，即可进入 LangGraph Studio 界面，输入你的测试问题并实时观察 Agent 的思考路径。

### 4. 启动标准 HTTP 服务 (生产/评测模式)

如果你想通过代码、Postman 或自动化脚本批量测试，可以启动内置的 FastAPI 标准服务：

Bash

```
uvicorn src.app:app --host 0.0.0.0 --port 8000
```

**命令行/脚本测试调用：**

- Mac / Linux (Bash):
    

Bash

```
curl -X POST "http://localhost:8000/" \
     -H "Content-Type: application/json" \
     -d '{"question": "2018年诺贝尔物理学奖的一位女性得主，曾在加拿大的一所顶尖大学长期任教。这所大学在2023年正式任命了一位新的校长，请问这位新校长的英文全名是什么？"}'
```

- Windows (PowerShell):
    

PowerShell

```
Invoke-RestMethod -Uri "http://localhost:8000/" `
    -Method Post `
    -Headers @{"Content-Type"="application/json"} `
    -Body '{"question": "2018年诺贝尔物理学奖的一位女性得主，曾在加拿大的一所顶尖大学长期任教。这所大学在2023年正式任命了一位新的校长，请问这位新校长的英文全名是什么？"}'
```

---

## 💡 典型工作流展示：面对极端难题的抗幻觉与自我纠错

在测试中，面对类似于“_某国发射的科学卫星导致八年后某个特定罕见病中心成立_”这种“海龟汤”式的变态推理题，单次 Search 命中率几乎为零。Gaia Agent 的核心价值不在于暴力猜答案，而是通过 LangGraph Studio 展现了一个**极其严谨、可观测、抗幻觉的机器思考过程**：

1. **🕵️ 动态策略路由 (S.O.P Routing)** 系统不会盲目调用外部搜索，而是先识别任务类型并加载对应 Markdown Playbook，强制大模型按步骤降维拆解复杂问题。
    
2. **🔄 深度下钻与子图循环 (Deep Dive & Subgraph Looping)** 若浅层检索缺失关键信息，子图不会直接放弃，而是根据 S.O.P 触发 `Jina Reader` 进入目标百科页面进行长文本截取与 `Qwen3-Rerank` 重排。
    
3. **🛡️ 零幻觉底线与优雅降级 (Graceful Degradation)** 当检索到的证据链断裂，或者大模型擅自“脑补”连接时，系统的**裁判节点 (Evaluation Node)** 会立即判定 `is_valid_final_answer = False`。
    
    - **异常拦截**：即使遇到大模型输出的 JSON 格式破损，系统也不会崩溃，而是通过底层的 `JsonOutputParser` 优雅拦截。
        
    - **自我修复**：系统将错误详情与逻辑断点反投给主脑触发重试；若穷尽最大重试次数仍无严谨证据，Agent 会如实输出“基于当前搜索链，无法验证最终实体”。这种**过程完全白盒化、坚决不产生幻觉**的工程架构，极大提升了复杂业务落地时的可控性。