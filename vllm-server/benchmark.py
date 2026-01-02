"""
vLLM Token Generation Benchmark
測試 vLLM 服務的 token 生成速度
"""

import time
import requests
import statistics
from typing import List, Dict, Any

# ============== 配置 ==============
VLLM_URL = "http://localhost:8080/v1/chat/completions"
API_KEY = "your-secure-api-key-here"
MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"

# 測試參數
TEST_PROMPTS = [
    "Write a short story about a robot learning to paint.",
    "Explain quantum computing in simple terms.",
    "What are the benefits of renewable energy?",
    "Describe the process of photosynthesis step by step.",
    "Write a poem about the ocean.",
]

MAX_TOKENS = 256  # 每次生成的 token 數
NUM_RUNS = 5      # 每個 prompt 測試次數


def make_request(prompt: str, max_tokens: int = MAX_TOKENS) -> Dict[str, Any]:
    """發送請求到 vLLM API"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "stream": False  # 非串流模式
    }
    
    start_time = time.perf_counter()
    response = requests.post(VLLM_URL, headers=headers, json=payload, timeout=120)
    end_time = time.perf_counter()
    
    response.raise_for_status()
    data = response.json()
    
    return {
        "elapsed_time": end_time - start_time,
        "prompt_tokens": data["usage"]["prompt_tokens"],
        "completion_tokens": data["usage"]["completion_tokens"],
        "total_tokens": data["usage"]["total_tokens"],
        "content": data["choices"][0]["message"]["content"]
    }


def run_benchmark() -> None:
    """執行基準測試"""
    print("=" * 60)
    print("vLLM Token Generation Benchmark")
    print("=" * 60)
    print(f"Model: {MODEL_NAME}")
    print(f"Max Tokens per Request: {MAX_TOKENS}")
    print(f"Number of Prompts: {len(TEST_PROMPTS)}")
    print(f"Runs per Prompt: {NUM_RUNS}")
    print("=" * 60)
    print()
    
    all_results: List[Dict[str, Any]] = []
    all_tokens_per_second: List[float] = []
    
    # 預熱
    print("🔥 Warming up...")
    try:
        make_request("Hello", max_tokens=10)
        print("   Warmup complete.\n")
    except Exception as e:
        print(f"❌ Warmup failed: {e}")
        return
    
    # 執行測試
    for i, prompt in enumerate(TEST_PROMPTS, 1):
        print(f"📝 Prompt {i}/{len(TEST_PROMPTS)}: {prompt[:50]}...")
        
        prompt_results: List[Dict[str, Any]] = []
        
        for run in range(NUM_RUNS):
            try:
                result = make_request(prompt)
                prompt_results.append(result)
                
                tokens_per_sec = result["completion_tokens"] / result["elapsed_time"]
                all_tokens_per_second.append(tokens_per_sec)
                
                print(f"   Run {run + 1}: {result['completion_tokens']:3d} tokens in "
                      f"{result['elapsed_time']:.2f}s = {tokens_per_sec:.2f} tokens/s")
                print(f"   Input: \"{prompt[:60]}...\"")
                print(f"   Output: \"{result['content'][:100].replace(chr(10), ' ')}...\"")
                print("-" * 40)
                
            except Exception as e:
                print(f"   Run {run + 1}: ❌ Error - {e}")
        
        if prompt_results:
            avg_tokens = statistics.mean([r["completion_tokens"] for r in prompt_results])
            avg_time = statistics.mean([r["elapsed_time"] for r in prompt_results])
            avg_tps = statistics.mean([r["completion_tokens"] / r["elapsed_time"] for r in prompt_results])
            print(f"   📊 Average: {avg_tokens:.1f} tokens, {avg_time:.2f}s, {avg_tps:.2f} tokens/s\n")
        
        all_results.extend(prompt_results)
    
    # 總結
    print("=" * 60)
    print("📊 BENCHMARK RESULTS")
    print("=" * 60)
    
    if all_tokens_per_second:
        total_completion_tokens = sum(r["completion_tokens"] for r in all_results)
        total_time = sum(r["elapsed_time"] for r in all_results)
        
        print(f"Total Requests:           {len(all_results)}")
        print(f"Total Completion Tokens:  {total_completion_tokens}")
        print(f"Total Time (sum of latency): {total_time:.2f}s")
        print()
        print(f"Average Tokens/Second:    {statistics.mean(all_tokens_per_second):.2f}")
        print(f"Median Tokens/Second:     {statistics.median(all_tokens_per_second):.2f}")
        print(f"Min Tokens/Second:        {min(all_tokens_per_second):.2f}")
        print(f"Max Tokens/Second:        {max(all_tokens_per_second):.2f}")
        
        if len(all_tokens_per_second) > 1:
            print(f"Std Dev:                  {statistics.stdev(all_tokens_per_second):.2f}")
        
        # 計算 P50, P90, P99
        sorted_tps = sorted(all_tokens_per_second)
        n = len(sorted_tps)
        print()
        print(f"P50 Tokens/Second:        {sorted_tps[int(n * 0.50)]:.2f}")
        print(f"P90 Tokens/Second:        {sorted_tps[int(n * 0.90)]:.2f}")
        print(f"P99 Tokens/Second:        {sorted_tps[min(int(n * 0.99), n - 1)]:.2f}")
        
        print()
        print(f"Overall Throughput:       {total_completion_tokens / total_time:.2f} tokens/s")
    else:
        print("❌ No successful results to analyze.")
    
    print("=" * 60)


if __name__ == "__main__":
    run_benchmark()
