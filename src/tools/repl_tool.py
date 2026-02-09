import sys
import io
import asyncio
import traceback
import math
import datetime
import re
import statistics
import multiprocessing
from contextlib import redirect_stdout
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Dict, Any

FORBIDDEN_KEYWORDS = [
    "import os", "from os", "import sys", "from sys", 
    "import subprocess", "from subprocess",
    "open(", "input(", "exit(", "quit(", "exec(", "eval("
]

class code_execution_repl_args(BaseModel):
    code: str = Field(..., description="The Python code to execute")
    
# 这个工具的设计目标是提供一个安全的环境来执行 Python 代码，适用于需要动态计算或处理数据的场景。
# 通过限制可用的库和内置函数，并禁止使用危险的关键词，我们可以最大程度地降低安全风险。
# 同时，使用 asyncio 和 multiprocessing 来管理代码执行，可以防止长时间运行的代码阻塞主线程，并在必要时强制终止执行。
def _code_execution_repl_worker(code: str, queue:multiprocessing.Queue):
    
    # 1. 安全检查：禁止使用危险的关键词
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in code:
            queue.put(f"SecurityError: The code contains forbidden keyword '{keyword}'.")
            return 
    
    # 2. 定义一个安全的执行环境，限制可用的库和内置函数
    local_env = {
        "math": math,
        "datetime": datetime,
        "re": re,
        "statistics": statistics,
        "sum": sum,
        "len": len,
        "max": max,
        "min": min,
        "sorted": sorted,
        "abs": abs,
        "round": round,
        "set": set,
        "enumerate": enumerate,
        "zip": zip
    }
    
    output_buffer = io.StringIO()
    try:
        
        with redirect_stdout(output_buffer):
            
            exec(code, {}, local_env)
        
        result = output_buffer.getvalue()
        if not result.strip():
            result = "Code executed successfully with no output.\nDid you forget to use `print(...)`? Please print your final answer."
        
        queue.put(result.strip())
    except Exception:
        
        # 获取异常信息
        exc_type, exc_value, exc_tb = sys.exc_info()
        
        # 提取堆栈列表
        tb_list = traceback.extract_tb(exc_tb)
        
        # 构建干净的报错信息
        # 我们只关心 filename 为 "<string>" 的帧（即用户代码）
        # 并且我们手动拼接字符串，不让 traceback 自动去读取源码行
        clean_traceback_str = "Traceback (most recent call last):\n"
        
        found_user_code = False
        for frame in tb_list:
            if frame.filename == "<string>":
                found_user_code = True
                # 手动格式化：File "<code>", line X, in <module>
                # 注意：这里我们故意【不】包含 frame.line (源代码内容)，防止打印出 spawn_main
                clean_traceback_str += f'  File "<code>", line {frame.lineno}, in {frame.name}\n'
        
        # 如果堆栈里没找到 <string> (极少见系统错)，就回退到原始信息，但尽量清洗
        if not found_user_code:
            clean_traceback_str += "  (System internal error frame hidden)\n"

        # 加上最后的错误类型和描述
        error_msg = f"{exc_type.__name__}: {exc_value}"
        
        final_error = f"Error:\n{clean_traceback_str}{error_msg}"
        queue.put(final_error)
        

# 这个函数提供了一个接口来执行代码，并设置了一个超时时间。如果代码在指定时间内没有完成执行，函数将强制终止进程并返回一个超时错误消息。
def run_code_execution_with_timeout(code: str, timeout: int = 5) -> str:
    
    # 1. 创建一个 multiprocessing.Queue 来获取子进程的输出
    queue = multiprocessing.Queue()
    
    # 2. 创建一个新的进程来执行代码
    process = multiprocessing.Process(target=_code_execution_repl_worker, args=(code, queue))
    process.start()
    # 3. 等待进程完成，设置超时时间
    process.join(timeout)
    
    # 4. 如果进程仍然在运行，强制终止它
    if process.is_alive():
        # 终止进程
        process.terminate()

        process.join()
        
        return f"Error: Code execution timed out after {timeout} seconds."
    
    if not queue.empty():
        return queue.get()
    else:
        return "Error: No output from code execution."

# 这个函数是工具的主入口，使用 asyncio 来管理异步执行，并调用 run_code_execution_with_timeout 来执行代码。
@tool('code_execution_repl', args_schema=code_execution_repl_args)
async def code_execution_repl(code: str) -> str:
    """Execute Python code in a REPL environment and return the output or error message.

    Args:
        code: The Python code to execute.
    Returns:
        The output of the executed code or any error messages.
    """
    
    try:
        
        result = await asyncio.to_thread(run_code_execution_with_timeout, code, 5)
        
        return result
    
    except Exception as e:
        
        return f"SystemError: {str(e)}"
        
  
if __name__ == "__main__":
    async def test():
        test1_code = "print(123 * 456)"
        
        test2_code = """
from datetime import date
d1 = date(2020, 1, 1)
d2 = date(2023, 1, 1)
print(f"Days: {(d2-d1).days}")
"""
        
        test3_code = "import os; print(os.getcwd())"
        
        test4_code = "while True: pass"
        
        test5_code = "print(1/0)"
        
        test1 = await code_execution_repl.ainvoke({"code": test1_code})
        test2 = await code_execution_repl.ainvoke({"code": test2_code})
        test3 = await code_execution_repl.ainvoke({"code": test3_code})
        test4 = await code_execution_repl.ainvoke({"code": test4_code})
        test5 = await code_execution_repl.ainvoke({"code": test5_code})
        
        print("Test 1 Result:\n", test1)
        print("Test 2 Result:\n", test2)
        print("Test 3 Result:\n", test3)
        print("Test 4 Result:\n", test4)
        print("Test 5 Result:\n", test5)
        
    asyncio.run(test())