import os
import json
import hashlib
import numpy as np
import redis
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# Connect to local Redis

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"), 
    port=6379, 
    db=0, 
    decode_responses=True
)

# OpenAI client for embeddings (pointed at Mistral)
embed_client = OpenAI(
    api_key=os.getenv("MISTRAL_API_KEY"),
    base_url="https://api.mistral.ai/v1"
)

def get_embedding(text: str) -> list:
    """Generates an embedding vector using Mistral's API."""
    response = embed_client.embeddings.create(
        model="mistral-embed",
        input=text
    )
    return response.data[0].embedding

def cosine_similarity(v1: list, v2: list) -> float:
    """Calculates cosine similarity between two vectors."""
    vec1 = np.array(v1)
    vec2 = np.array(v2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def get_cached_response(prompt: str) -> str | None:
    """
    Checks Redis for a semantically similar prompt.
    Returns the cached response if similarity > 0.85, else None.
    """
    prompt_vector = get_embedding(prompt)
    
    # Scan all cached prompts
    for key in redis_client.scan_iter("cache:*"):
        cached_data = json.loads(redis_client.get(key))
        similarity = cosine_similarity(prompt_vector, cached_data["vector"])
        
        if similarity > 0.85:
            print(f"[Cache] 🧠 CACHE HIT! Similarity: {similarity:.2f}")
            return cached_data["response"]
            
    return None

def add_to_cache(prompt: str, response: str):
    """Saves a prompt, its embedding, and response to Redis."""
    prompt_vector = get_embedding(prompt)
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
    
    cache_data = {
        "vector": prompt_vector,
        "response": response
    }
    
    redis_client.set(f"cache:{prompt_hash}", json.dumps(cache_data))
    print("[Cache] 💾 Saved to cache.")
