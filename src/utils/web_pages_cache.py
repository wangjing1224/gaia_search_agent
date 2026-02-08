import threading
from collections import OrderedDict
from src.utils.WritePriorityRWLock import WritePriorityRWLock

class WebPageCache:
    _instance = None
    
    _lock = threading.Lock()  # 用于单例创建的基础锁
    
    # 写优先的读写锁
    _rw_lock = WritePriorityRWLock()

    def __new__(cls):
        # 单例创建：用基础锁保证线程安全
        if not cls._instance:
            with cls._lock:  # 获取基础锁，确保只有一个线程能创建实例
                if not cls._instance:
                    cls._instance = super(WebPageCache, cls).__new__(cls)
                    cls._instance.cache = OrderedDict()
                    cls._instance.capacity = 20
                    # 初始化一个锁来保护 cache 的访问，确保线程安全
                    cls._instance.cache_lock = threading.Lock()  # 用于保护 cache 的锁
        return cls._instance

    def get(self, url: str):
        with self.cache_lock:  # 获取 cache 锁，保护 cache 的访问
            if url in self.cache:
                self.cache.move_to_end(url)
                return self.cache[url]
            return None

    def set(self, url: str, content: str):
        with self.cache_lock:  # 获取 cache 锁，保护 cache 的访问
            if url in self.cache:
                self.cache.move_to_end(url)
            self.cache[url] = content
            
            if len(self.cache) > self.capacity:
                removed_url, _ = self.cache.popitem(last=False)
                print(f"[Cache] Memory full. Removed oldest page: {removed_url}")

    def clear(self):
        with self.cache_lock:  # 获取 cache 锁，保护 cache 的访问
            self.cache.clear()
            print("[Cache] Cleared all cached pages.")

# 全局实例
web_cache = WebPageCache()