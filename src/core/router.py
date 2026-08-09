import os
from openai import OpenAI
from api.models import ChatCompletionRequest
from dotenv import load_dotenv
from core.security import redact_pii, detect_prompt_injection
from core.cache import get_cached_response, add_to_cache
from core.metrics import CACHE_HITS, CACHE_MISSES, LLM_TOKENS, LLM_LATENCY
import time

# Load the .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# Initialize the OpenAI client, but point it to Mistral's server
client = OpenAI(
    api_key=os.getenv("MISTRAL_API_KEY"),
    base_url="https://api.mistral.ai/v1"
)

def classify_prompt(prompt: str) -> str:
    """
    Classifies the prompt to decide which model to use.
    Returns 'simple' or 'complex'.
    """
    # Convert prompt to a set of lowercase words for exact matching
    words = prompt.split()
    words_set = set(word.lower().strip('.,!?') for word in words)
    
    # 1. Check for complex keywords FIRST (using exact word match)
    complex_keywords = {
        "code", "build", "write", "explain", "summarize", "analyze", "python", 
        "javascript", "debug", "create", "develop", "website", "application", 
        "api", "database", "sql", "react", "html", "css", "algorithm", 
        "architecture", "design", "generate", "implement", "refactor", 
        "document", "script"
    }
    
    # If any exact word matches, it's complex
    if words_set.intersection(complex_keywords):
        return "complex"
        
    # 2. If no keywords, check length
    if len(words) < 12:
        return "simple"
        
    # 3. Default to complex for safety
    return "complex"

async def route_llm_request(request: ChatCompletionRequest):
    """
    Dynamic Router: Analyzes, secures, caches, and routes the request.
    """
    user_prompt = request.messages[-1].content if request.messages else ""
    
    # 1. SECURITY CHECK
    if detect_prompt_injection(user_prompt):
        print("[Security] 🚨 PROMPT INJECTION DETECTED! Blocking request.")
        return {
            "error": {
                "message": "Security violation: Prompt injection detected.",
                "type": "security_error",
                "code": 403
            }
        }
    
    secured_prompt = redact_pii(user_prompt)
    request.messages[-1].content = secured_prompt
    
    if user_prompt != secured_prompt:
        print("[Security] 🔒 PII Redacted from prompt.")
    
    # 2. CACHE CHECK
    cached_response = get_cached_response(secured_prompt)
    if cached_response:
        CACHE_HITS.inc() # Increment Prometheus Cache Hit counter
        return {
            "id": "cached-response",
            "choices": [{"message": {"role": "assistant", "content": cached_response}}],
            "cached": True
        }
    
    CACHE_MISSES.inc() # Increment Prometheus Cache Miss counter
        
    # 3. ROUTING
    prompt_type = classify_prompt(secured_prompt)
    
    if prompt_type == "simple":
        selected_model = "open-mistral-7b"
    else:
        selected_model = "mistral-large-latest"
    
    print(f"[Router] Prompt Type: {prompt_type.upper()} | Routing to: {selected_model}")

    try:
        start_time = time.time() # Start latency timer
        
        response = client.chat.completions.create(
            model=selected_model,
            messages=[msg.dict() for msg in request.messages],
            temperature=request.temperature
        )
        
        latency = time.time() - start_time # Stop latency timer
        
        # Record metrics
        LLM_LATENCY.labels(model=selected_model).observe(latency)
        LLM_TOKENS.labels(model=selected_model, token_type="prompt").inc(response.usage.prompt_tokens)
        LLM_TOKENS.labels(model=selected_model, token_type="completion").inc(response.usage.completion_tokens)
        
        # 4. SAVE TO CACHE
        llm_response_text = response.choices[0].message.content
        add_to_cache(secured_prompt, llm_response_text)
        
        return response.model_dump()
    except Exception as e:
        print(f"[ERROR] API Call Failed: {str(e)}")
        raise e
