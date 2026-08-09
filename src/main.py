import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from api.routes import router

# Load environment variables from .env file
load_dotenv() 

app = FastAPI(
    title="Enterprise LLM Gateway",
    description="Dynamic routing, caching, and security for LLM applications",
    version="1.0.0"
)

# Include the API routes
app.include_router(router, prefix="/v1")

# Initialize Prometheus metrics endpoint at /metrics
Instrumentator().instrument(app).expose(app)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "LLM Gateway"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
