import time
import requests

GATEWAY_URL = "http://localhost:8000/v1/chat/completions"
HEADERS = {"Content-Type": "application/json"}

# 50 prompts: 25 unique, 25 duplicates (to trigger cache)
prompts = [
    "What is the capital of France?",
    "Tell me the capital city of France.", # Semantic duplicate
    "Explain quantum computing in simple terms.",
    "Explain quantum computing simply.", # Semantic duplicate
    "Write a haiku about a robot.",
    "Compose a haiku about robots.", # Semantic duplicate
] * 8 + ["What is the capital of France?"] * 2

print(f"Sending {len(prompts)} requests to the Gateway...")

cache_hits = 0
cache_misses = 0
total_latency = 0

# Financial tracking
cost_without_gateway = 0.0
cost_with_gateway = 0.0

# Pricing per 1M tokens (Industry standard rates)
GPT4O_PROMPT_PRICE = 5.00 / 1_000_000
GPT4O_COMPLETION_PRICE = 15.00 / 1_000_000

MISTRAL_PROMPT_PRICE = 0.25 / 1_000_000
MISTRAL_COMPLETION_PRICE = 0.25 / 1_000_000

for i, prompt in enumerate(prompts):
    payload = {
        "model": "auto-router",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    start_time = time.time()
    response = requests.post(GATEWAY_URL, headers=HEADERS, json=payload)
    latency = time.time() - start_time
    total_latency += latency
    
    if response.status_code == 200:
        data = response.json()
        
        # Check if it was a cache hit
        if data.get("cached", False):
            cache_hits += 1
            # Estimate tokens for the "Without Gateway" baseline
            est_prompt_tokens = len(prompt) / 4
            est_completion_tokens = len(data["choices"][0]["message"]["content"]) / 4
            cost_without_gateway += (est_prompt_tokens * GPT4O_PROMPT_PRICE) + (est_completion_tokens * GPT4O_COMPLETION_PRICE)
            # Cache hits cost $0 with the gateway
        else:
            cache_misses += 1
            # Extract EXACT tokens from Mistral response
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            
            # Calculate cost if this went to GPT-4o
            cost_without_gateway += (prompt_tokens * GPT4O_PROMPT_PRICE) + (completion_tokens * GPT4O_COMPLETION_PRICE)
            
            # Calculate actual cost using Mistral
            cost_with_gateway += (prompt_tokens * MISTRAL_PROMPT_PRICE) + (completion_tokens * MISTRAL_COMPLETION_PRICE)
    else:
        print(f"Request {i+1} failed: {response.text}")

# Calculate final numbers
cache_hit_rate = (cache_hits / len(prompts)) * 100
avg_latency = (total_latency / len(prompts)) * 1000
total_saved = cost_without_gateway - cost_with_gateway
savings_percentage = (total_saved / cost_without_gateway) * 100 if cost_without_gateway > 0 else 0

print("\n" + "="*40)
print("  ENTERPRISE BENCHMARK RESULTS")
print("="*40)
print(f"Total Requests      : {len(prompts)}")
print(f"Cache Hits          : {cache_hits}")
print(f"Cache Misses        : {cache_misses}")
print(f"Cache Hit Rate      : {cache_hit_rate:.2f}%")
print(f"Avg Latency/Request : {avg_latency:.2f}ms")
print("-" * 40)
print(f"Cost WITHOUT Gateway (GPT-4o): ${cost_without_gateway:.4f}")
print(f"Cost WITH Gateway (Mistral+Cache): ${cost_with_gateway:.4f}")
print(f"Total Money Saved   : ${total_saved:.4f} ({savings_percentage:.2f}% reduction)")
print("="*40)
