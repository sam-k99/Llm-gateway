from fastapi import APIRouter, HTTPException
from api.models import ChatCompletionRequest
from core.router import route_llm_request

router = APIRouter()

@router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    Main endpoint that intercepts prompts and routes them.
    """
    try:
        response = await route_llm_request(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
