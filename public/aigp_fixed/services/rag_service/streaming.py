"""
services/rag_service/streaming.py
Streaming SSE endpoint for RAG Q&A.
"""
import asyncio
from typing import AsyncGenerator

import structlog
from langchain_core.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

log = structlog.get_logger(__name__)

TOKEN_TIMEOUT = 15


class QueueCallback(StreamingStdOutCallbackHandler):
    """Callback that puts tokens into an async queue."""

    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue()

    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        await self.queue.put(token)

    async def on_llm_end(self, *args, **kwargs) -> None:
        await self.queue.put(None)


async def token_stream_generator(isbn: str, question: str) -> AsyncGenerator[str, None]:
    """
    Generate token stream for SSE.

    Args:
        isbn: Book ISBN
        question: User question

    Yields:
        SSE-formatted tokens
    """
    from services.rag_service.chain import build_rag_chain

    chain = build_rag_chain(isbn)
    queue: asyncio.Queue = asyncio.Queue()
    timeout_task = None
    last_token_time = asyncio.get_event_loop().time()

    class QueueCallback(StreamingStdOutCallbackHandler):
        async def on_llm_new_token(self, token: str, **kwargs) -> None:
            nonlocal last_token_time
            last_token_time = asyncio.get_event_loop().time()
            await queue.put(token)

        async def on_llm_end(self, *args, **kwargs) -> None:
            await queue.put(None)

    async def run_chain():
        try:
            await chain.ainvoke(
                {"query": question},
                config={"callbacks": [QueueCallback()]},
            )
        except Exception as e:
            log.error("rag.chain_error", error=str(e))
            await queue.put("[ERROR]")

    task = asyncio.create_task(run_chain())

    while True:
        try:
            token = await asyncio.wait_for(queue.get(), timeout=TOKEN_TIMEOUT)

            if token is None:
                break
            elif token == "[ERROR]":
                break
            else:
                yield f"data: {token}\n\n"

        except asyncio.TimeoutError:
            elapsed = asyncio.get_event_loop().time() - last_token_time
            log.warning("rag.stream_timeout", elapsed=elapsed)
            yield "data: [TIMEOUT]\n\n"
            task.cancel()
            break

    yield "data: [DONE]\n\n"


async def generate_sync_response(isbn: str, question: str) -> dict:
    """
    Generate synchronous (non-streaming) response.

    Args:
        isbn: Book ISBN
        question: User question

    Returns:
        Dict with answer and citations
    """
    from services.rag_service.chain import invoke_chain

    result = invoke_chain(isbn, question)

    return result