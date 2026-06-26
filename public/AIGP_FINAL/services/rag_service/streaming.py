"""
services/rag_service/streaming.py
Streaming SSE endpoint for RAG Q&A.
"""
import asyncio
import time
from typing import AsyncGenerator

import structlog
from langchain_core.callbacks.base import BaseCallbackHandler

log = structlog.get_logger(__name__)

TOKEN_TIMEOUT = 15


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
    loop = asyncio.get_running_loop()
    last_token_time = time.monotonic()

    class StreamCallback(BaseCallbackHandler):
        """
        Sync callback that bridges langchain's sync callback system
        to the async queue using thread-safe call.
        langchain 0.1.x calls on_llm_new_token synchronously from a thread,
        so we use call_soon_threadsafe instead of await.
        """

        def on_llm_new_token(self, token: str, **kwargs) -> None:
            nonlocal last_token_time
            last_token_time = time.monotonic()
            loop.call_soon_threadsafe(queue.put_nowait, token)

        def on_llm_end(self, *args, **kwargs) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, None)

        def on_llm_error(self, error: Exception, **kwargs) -> None:
            log.error("rag.llm_error", error=str(error))
            loop.call_soon_threadsafe(queue.put_nowait, "[ERROR]")

    async def run_chain() -> None:
        try:
            await chain.ainvoke(
                {"query": question},
                config={"callbacks": [StreamCallback()]},
            )
        except Exception as e:
            log.error("rag.chain_error", error=str(e))
            loop.call_soon_threadsafe(queue.put_nowait, "[ERROR]")

    task = asyncio.create_task(run_chain())

    try:
        while True:
            try:
                token = await asyncio.wait_for(queue.get(), timeout=TOKEN_TIMEOUT)

                if token is None:
                    break
                if token == "[ERROR]":
                    break
                yield f"data: {token}\n\n"

            except asyncio.TimeoutError:
                log.warning("rag.stream_timeout", elapsed=time.monotonic() - last_token_time)
                yield "data: [TIMEOUT]\n\n"
                task.cancel()
                break
    finally:
        if not task.done():
            task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    yield "data: [DONE]\n\n"


async def generate_sync_response(isbn: str, question: str) -> dict:
    """Generate synchronous (non-streaming) response."""
    from services.rag_service.chain import invoke_chain

    return await invoke_chain(isbn, question)
