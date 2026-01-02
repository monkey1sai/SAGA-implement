"""
vLLM/SGLang Tool Use Benchmark
測試在帶有 Tool 定義情況下的併發效能
"""

import os
import asyncio
import time
import json
import aiohttp
import statistics
from typing import List, Dict, Any

# Simple .env loader
def load_env_file(filepath):
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    except FileNotFoundError:
        pass

load_env_file('.env')

# ============== 配置 ==============
VLLM_URL = "http://localhost:8082/v1/chat/completions"
API_KEY = os.getenv("VLLM_API_KEY", "your-secure-api-key-here")
MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"

# 測試參數
CONCURRENT_REQUESTS = 20
TOTAL_REQUESTS = 40

# Tool 定義
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        },
    }
]

PROMPT = "What is the weather in San Francisco?"

async def make_tool_request(session: aiohttp.ClientSession, request_id: int) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": PROMPT}],
        "tools": TOOLS,
        "tool_choice": "auto",
        "stream": True 
    }
    
    start_time = time.perf_counter()
    first_token_time = None
    token_count = 0
    
    try:
        async with session.post(VLLM_URL, headers=headers, json=payload) as response:
            if response.status != 200:
                text = await response.text()
                return {"error": f"Status {response.status}: {text}", "latency": 0}
            
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith("data: ") and line != "data: [DONE]":
                    try:
                        if first_token_time is None:
                            first_token_time = time.perf_counter()
                        
                        data = json.loads(line[6:])
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            
                            # 計算 Tool Call 相關的 token
                            if "tool_calls" in delta:
                                # 簡單估算：每個 chunk 算一次傳輸，精確 token 數需 tokenizer，這裡計算 chunk 頻率近似
                                # 或者檢查 arguments 的長度
                                tool_calls = delta["tool_calls"]
                                for tc in tool_calls:
                                    if "function" in tc and "arguments" in tc["function"]:
                                        # 為了統計吞吐量，這裡計算生成的字元數並除以 4 (粗略估計 token)
                                        # 這是因為 stream 模式下 arguments 是片段傳回的
                                        args_part = tc["function"]["arguments"]
                                        token_count += len(args_part) / 4 
                            
                            # 有些模型可能同時回傳 content
                            if "content" in delta and delta["content"]:
                                token_count += 1
                                
                    except:
                        pass
                        
        end_time = time.perf_counter()
        
        ttft = (first_token_time - start_time) if first_token_time else (end_time - start_time)
        gen_time = (end_time - first_token_time) if first_token_time else 0
        total_time = end_time - start_time
        
        # 修正：如果生成太快或內容太少導致 token_count 為 0 (例如只回了 tool id)
        if token_count == 0: token_count = 1 

        return {
            "id": request_id,
            "ttft": ttft,
            "gen_time": gen_time,
            "total_time": total_time,
            "tokens": token_count,
        }
        
    except Exception as e:
        return {"error": str(e), "latency": 0}

async def run_benchmark():
    print("=" * 60)
    print("🚀 vLLM/SGLang Tool Use Benchmark")
    print("=" * 60)
    print(f"Model: {MODEL_NAME}")
    print(f"Concurrency: {CONCURRENT_REQUESTS}")
    print("Scenario: Function Calling (Weather)")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        tasks = []
        global_start = time.perf_counter()
        
        for i in range(TOTAL_REQUESTS):
            tasks.append(make_tool_request(session, i))
        
        results = await asyncio.gather(*tasks)
        global_end = time.perf_counter()

    valid_results = [r for r in results if "error" not in r]
    if not valid_results:
        print("❌ All requests failed!")
        if results: print(f"First error: {results[0]}")
        return

    avg_ttft = statistics.mean(r["ttft"] for r in valid_results)
    avg_gen_time = statistics.mean(r["gen_time"] for r in valid_results)
    avg_total_time = statistics.mean(r["total_time"] for r in valid_results)
    
    total_tokens = sum(r["tokens"] for r in valid_results)
    global_duration = global_end - global_start
    system_throughput = total_tokens / global_duration

    print("=" * 60)
    print("📊 TOOL USE PERFORMANCE")
    print("=" * 60)
    print(f"1️⃣  Time to First Token (TTFT)")
    print(f"    Average: {avg_ttft:.4f} s")
    print("-" * 60)
    print(f"2️⃣  Total Request Time")
    print(f"    Average: {avg_total_time:.4f} s")
    print("=" * 60)
    print(f"🔥 System Throughput: {system_throughput:.2f} tokens/s (Estimated)")
    print(f"✅ Successful Req:    {len(valid_results)}/{TOTAL_REQUESTS}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_benchmark())
