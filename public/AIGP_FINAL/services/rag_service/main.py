"""
services/rag_service/main.py
FastAPI service for RAG Q&A with streaming and sync endpoints.
"""
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import structlog

from services.rag_service.streaming import token_stream_generator, generate_sync_response
from services.rag_service.chain import build_rag_chain

log = structlog.get_logger(__name__)

app = FastAPI(
    title="RAG Service",
    description="RAG Q&A with LangChain and streaming support",
    version="1.0.0",
)


class QARequest(BaseModel):
    """Request model for Q&A."""

    isbn: str = Field(..., description="Book ISBN")
    question: str = Field(..., description="User question", min_length=1)


class QAResponse(BaseModel):
    """Response model for sync Q&A."""

    answer: str
    citations: list[dict]


@app.post("/qa/stream")
async def qa_stream(req: QARequest) -> StreamingResponse:
    """
    Streaming RAG Q&A endpoint.

    Returns Server-Sent Events (SSE) with tokens.
    """
    try:
        return StreamingResponse(
            token_stream_generator(req.isbn, req.question),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        log.error("qa_stream.failed", isbn=req.isbn, error=str(e))
        raise HTTPException(status_code=500, detail={"error": "AI-004", "message": str(e)})


@app.post("/qa/sync", response_model=QAResponse)
async def qa_sync(req: QARequest) -> QAResponse:
    """
    Synchronous RAG Q&A endpoint.

    Returns full JSON response with answer and citations.
    """
    try:
        result = await generate_sync_response(req.isbn, req.question)

        if not result.get("answer"):
            return QAResponse(
                answer="I don't have enough information from this book to answer that question.",
                citations=[],
            )

        return QAResponse(**result)

    except Exception as e:
        log.error("qa_sync.failed", isbn=req.isbn, error=str(e))
        raise HTTPException(status_code=500, detail={"error": "AI-004", "message": str(e)})


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "rag-service"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    log.error("unhandled.exception", path=request.url.path, error=str(exc))
    return Response(
        content='{"error": "AI-004", "message": "Internal server error"}',
        status_code=500,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "services.rag_service.main:app",
        host="0.0.0.0",
        port=8004,
        reload=True,
    )