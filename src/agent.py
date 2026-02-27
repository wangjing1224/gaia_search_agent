# src/agent.py
from src.graph import create_graph
from src.utils.skills_utils import init_skills_cache

# 初始化技能缓存

# 创建并暴露编译好的 graph
# 变量名 'graph' 非常重要，langgraph.json 会引用它
graph = create_graph()