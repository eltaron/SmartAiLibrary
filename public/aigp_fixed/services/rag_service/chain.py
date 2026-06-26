"""
services/rag_service/chain.py
LangChain RAG chain with caching and token budget guard.
"""
import functools
from typing import Optional

import structlog
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

from services.rag_service.retriever import get_retriever
from shared.config import settings

log = structlog.get_logger(__name__)

SYSTEM_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are an intelligent reading assistant for the Smart AI Library.
Answer the user's question using ONLY the excerpts provided below.
If the excerpts do not contain enough information, respond with:
"I don't have enough information from this book to answer that question."

Do not speculate or add information not present in the excerpts.
Always cite the page number(s) you drew information from.

Book Excerpts:
{context}

Question: {question}

Answer (cite page numbers):""",
)


@functools.lru_cache(maxsize=256)
def build_rag_chain(isbn: str) -> RetrievalQA:
    """
    Build RAG chain for a book (cached per ISBN).

    Args:
        isbn: Book ISBN

    Returns:
        RetrievalQA chain
    """
    llm = ChatOpenAI(
        model=settings.RAG_LLM_MODEL,
        temperature=0.1,
        streaming=True,
    )

    retriever = get_retriever(isbn, top_k=settings.RAG_TOP_K)

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": SYSTEM_PROMPT},
        return_source_documents=True,
    )

    log.info("rag.chain_built", isbn=isbn)
    return chain


def extract_citations(source_documents: list) -> list[dict]:
    """
    Extract citations from source documents.

    Args:
        source_documents: List of source documents from chain

    Returns:
        List of citations with page_num and score
    """
    citations = []

    for doc in source_documents:
        metadata = doc.metadata
        citations.append({
            "page_num": metadata.get("page_num"),
            "score": metadata.get("score", 0.0),
        })

    return citations


def enforce_token_budget(
    context: str,
    max_tokens: int = 3800,
) -> str:
    """
    Enforce token budget on context.

    If context exceeds max_tokens, truncate to fit.

    Args:
        context: Stuffed context string
        max_tokens: Maximum tokens allowed

    Returns:
        Truncated context if needed
    """
    import tiktoken

    try:
        enc = tiktoken.get_encoding("cl100k_base")
    except Exception:
        log.warning("tiktoken.fallback")
        return context

    tokens = enc.encode(context)

    if len(tokens) > max_tokens:
        truncated_tokens = tokens[:max_tokens]
        context = enc.decode(truncated_tokens)
        log.warning(
            "rag.token_budget_enforced",
            original_tokens=len(tokens),
            truncated_tokens=max_tokens,
        )

    return context


def invoke_chain(isbn: str, question: str) -> dict:
    """
    Invoke RAG chain with token budget enforcement.

    Args:
        isbn: Book ISBN
        question: User question

    Returns:
        Dict with answer and citations
    """
    chain = build_rag_chain(isbn)

    result = chain.invoke({"query": question})

    answer = result.get("result", "")
    source_docs = result.get("source_documents", [])

    citations = extract_citations(source_docs)

    return {
        "answer": answer,
        "citations": citations,
    }