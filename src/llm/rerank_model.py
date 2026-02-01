from flashrank import Ranker, RerankRequest

# 初始化 (会自动下载轻量模型 ms-marco-TinyBERT-L-2-v2，仅 40MB)
# cache_dir 可以指定模型下载位置，方便打包到比赛服务器
ranker_model_flash = Ranker(model_name="ms-marco-TinyBERT-L-2-v2", cache_dir="./models")