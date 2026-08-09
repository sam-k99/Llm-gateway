from prometheus_client import Counter, Histogram

# Count how many times we hit the cache vs missed
CACHE_HITS = Counter(
    'gateway_cache_hits_total', 
    'Total number of semantic cache hits'
)

CACHE_MISSES = Counter(
    'gateway_cache_misses_total', 
    'Total number of semantic cache misses'
)

# Count tokens used per model (to calculate cost)
LLM_TOKENS = Counter(
    'gateway_llm_tokens_total', 
    'Total tokens used by the gateway',
    ['model', 'token_type'] # token_type will be 'prompt' or 'completion'
)

# Track latency of the LLM calls
LLM_LATENCY = Histogram(
    'gateway_llm_latency_seconds',
    'Latency of LLM API calls in seconds',
    ['model']
)
