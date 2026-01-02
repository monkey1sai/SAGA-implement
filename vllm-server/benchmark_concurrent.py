"""
vLLM Concurrent Throughput Benchmark (Streaming)
測試 vLLM 在高併發下的首字延遲 (TTFT) 與總生成速度
"""

import asyncio
import time
import json
import aiohttp
import statistics
from typing import List, Dict, Any

# ============== 配置 ==============
VLLM_URL = "http://localhost:8081/v1/chat/completions"
API_KEY = "your-secure-api-key-here"
MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"

# 測試參數
CONCURRENT_REQUESTS = 20  # 模擬多少人同時請求
MAX_TOKENS = 128          # 每個請求生成的 token 數
TOTAL_REQUESTS = 40       # 總共發送多少個請求

PROMPT = "Write a short summary about the history of the internet."

async def make_stream_request(session: aiohttp.ClientSession, request_id: int) -> Dict[str, Any]:
    """發送單個串流 (Stream) 請求並測量時間"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": MAX_TOKENS,
        "temperature": 0.7,
        "stream": True  # <--- 重要：開啟串流模式
    }
    
    start_time = time.perf_counter()
    first_token_time = None
    token_count = 0
    
    try:
        async with session.post(VLLM_URL, headers=headers, json=payload) as response:
            if response.status != 200:
                return {"error": f"Status {response.status}", "latency": 0}
            
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith("data: ") and line != "data: [DONE]":
                    try:
                        # 記錄收到第一個 token 的時間 (TTFT)
                        if first_token_time is None:
                            first_token_time = time.perf_counter()
                        
                        data = json.loads(line[6:]) # remove "data: "
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta and delta["content"]:
                                token_count += 1
                    except:
                        pass
                        
        end_time = time.perf_counter()
        
        # 計算指標
        ttft = (first_token_time - start_time) if first_token_time else (end_time - start_time)
        gen_time = (end_time - first_token_time) if first_token_time else 0
        total_time = end_time - start_time
        
        return {
            "id": request_id,
            "ttft": ttft,                # 首字延遲 (反應時間)
            "gen_time": gen_time,        # 生成時間 (輸出過程)
            "total_time": total_time,    # 總時間
            "tokens": token_count,
            "tps": token_count / total_time if total_time > 0 else 0
        }
        
    except Exception as e:
        return {"error": str(e), "latency": 0}

async def run_benchmark():
    print("=" * 60)
    print("🚀 vLLM Concurrent Streaming Benchmark")
    print("=" * 60)
    print(f"Model: {MODEL_NAME}")
    print(f"Concurrency: {CONCURRENT_REQUESTS} users")
    print(f"Total Requests: {TOTAL_REQUESTS}")
    print(f"Max Tokens: {MAX_TOKENS}")
    print("=" * 60)
    print("\nStarting benchmark... (measuring TTFT and Generation Time)\n")

    async with aiohttp.ClientSession() as session:
        tasks = []
        global_start = time.perf_counter()
        
        for i in range(TOTAL_REQUESTS):
            tasks.append(make_stream_request(session, i))
        
        results = await asyncio.gather(*tasks)
        global_end = time.perf_counter()

    valid_results = [r for r in results if "error" not in r]
    if not valid_results:
        print("❌ All requests failed!")
        return

    # 計算統計數據
    avg_ttft = statistics.mean(r["ttft"] for r in valid_results)
    avg_gen_time = statistics.mean(r["gen_time"] for r in valid_results)
    avg_total_time = statistics.mean(r["total_time"] for r in valid_results)
    
    total_tokens = sum(r["tokens"] for r in valid_results)
    global_duration = global_end - global_start
    system_throughput = total_tokens / global_duration

    print("=" * 60)
    print("📊 DETAILED LATENCY ANALYSIS")
    print("=" * 60)
    print(f"1️⃣  Time to First Token (TTFT) / 反應時間")
    print(f"    (包含排隊, Prompt 處理, 開始思考)")
    print(f"    Average: {avg_ttft:.4f} s")
    print(f"    Min:     {min(r['ttft'] for r in valid_results):.4f} s")
    print(f"    Max:     {max(r['ttft'] for r in valid_results):.4f} s")
    print("-" * 60)
    
    print(f"2️⃣  Generation Time / 輸出生成時間")
    print(f"    (從吐出第一個字到結束)")
    print(f"    Average: {avg_gen_time:.4f} s")
    print("-" * 60)
    
    print(f"3️⃣  Total Request Time / 總耗時")
    print(f"    Average: {avg_total_time:.4f} s")
    print("=" * 60)
    
    print(f"🔥 System Throughput: {system_throughput:.2f} tokens/s")
    print(f"✅ Successful Req:    {len(valid_results)}/{TOTAL_REQUESTS}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_benchmark())
