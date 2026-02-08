import threading

class WritePriorityRWLock:
    """
    写优先的读写锁（对应操作系统读者-写者问题的写优先解决方案）
    核心规则：
    1. 读锁：多个线程可同时获取（共享），但有写等待时，读锁阻塞
    2. 写锁：只能一个线程获取（独占），且优先于读锁
    3. 读写互斥、写写互斥
    """
    def __init__(self):
        # 基础锁：保护下面的计数器
        self._base_lock = threading.Lock()
        # 条件变量：用于等待/唤醒读/写线程
        self._condition = threading.Condition(self._base_lock)
        
        # 计数器：当前活跃的读线程数
        self._active_readers = 0
        # 计数器：等待中的写线程数（解决写优先的核心）
        self._waiting_writers = 0
        # 标记：是否有活跃的写线程
        self._active_writer = False

    # ---------- 读锁操作 ----------
    def acquire_read(self):
        """获取读锁（读线程调用）"""
        with self._condition:
            # 写优先核心：如果有写线程在等，读线程先等（不插队）
            while self._waiting_writers > 0 or self._active_writer:
                self._condition.wait()  # 释放锁，等待被唤醒
            # 没有写等待/活跃写，允许获取读锁
            self._active_readers += 1

    def release_read(self):
        """释放读锁（读线程调用）"""
        with self._condition:
            self._active_readers -= 1
            # 最后一个读线程释放锁时，唤醒等待的写线程
            if self._active_readers == 0:
                self._condition.notify_all()

    # ---------- 写锁操作 ----------
    def acquire_write(self):
        """获取写锁（写线程调用）"""
        with self._condition:
            # 先标记：有写线程在等（让后续读线程排队）
            self._waiting_writers += 1
            # 等待：直到没有活跃读、没有活跃写
            while self._active_readers > 0 or self._active_writer:
                self._condition.wait()
            # 拿到写锁：标记活跃写，清空等待数
            self._waiting_writers -= 1
            self._active_writer = True

    def release_write(self):
        """释放写锁（写线程调用）"""
        with self._condition:
            self._active_writer = False
            # 唤醒所有等待的线程（优先唤醒写，因为新读会先检查_waiting_writers）
            self._condition.notify_all()

    # ---------- 上下文管理器（简化使用） ----------
    def read_lock(self):
        """with语句用读锁：with rw_lock.read_lock(): ..."""
        return _LockContextManager(self.acquire_read, self.release_read)

    def write_lock(self):
        """with语句用写锁：with rw_lock.write_lock(): ..."""
        return _LockContextManager(self.acquire_write, self.release_write)

# 辅助类：让读写锁支持with语句（简化代码）
class _LockContextManager:
    def __init__(self, acquire_func, release_func):
        self.acquire = acquire_func
        self.release = release_func

    def __enter__(self):
        self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()