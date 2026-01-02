"""
vLLM Token Generation Benchmark (Quick Version)
快速測試 vLLM 服務的 token 生成速度
"""

import time
import requests
import statistics

# ============== 配置 ==============
VLLM_URL = "http://localhost:8081/v1/chat/completions"
API_KEY = "your-secure-api-key-here"
MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"

# 測試參數
MAX_TOKENS = 100  # 每次生成的 token 數
NUM_RUNS = 3      # 測試次數


def benchmark():
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompts = [
        "Write a haiku about the moon.",
        "What is 2+2? Explain briefly.",
        "Name three colors.",
    ]
    
    print("=" * 50)
    print("vLLM Quick Benchmark")
    print(f"Model: {MODEL_NAME}")
    print(f"Max Tokens: {MAX_TOKENS}")
    print("=" * 50)
    
    results = []
    
    for i, prompt in enumerate(prompts, 1):
        payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": MAX_TOKENS,
            "temperature": 0.7,
        }
        
        print(f"\n[{i}/{len(prompts)}] Prompt: {prompt}")
        
        start = time.perf_counter()
        resp = requests.post(VLLM_URL, headers=headers, json=payload, timeout=60)
        elapsed = time.perf_counter() - start
        
        if resp.status_code == 200:
            data = resp.json()
            tokens = data["usage"]["completion_tokens"]
            tps = tokens / elapsed
            results.append(tps)
            
            print(f"    ✅ {tokens} tokens in {elapsed:.2f}s = {tps:.2f} tokens/s")
            print(f"    Response: {data['choices'][0]['message']['content'][:80]}...")
        else:
            print(f"    ❌ Error: {resp.status_code}")
    
    if results:
        print("\n" + "=" * 50)
        print("📊 RESULTS")
        print("=" * 50)
        print(f"Average: {statistics.mean(results):.2f} tokens/s")
        print(f"Min:     {min(results):.2f} tokens/s")
        print(f"Max:     {max(results):.2f} tokens/s")
        print("=" * 50)


if __name__ == "__main__":
    benchmark()
