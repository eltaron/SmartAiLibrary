"""
services/rag_service/chain.py
LangChain RAG chain with caching and token budget guard.

NOTE: langchain.chains.RetrievalQA was removed in modern LangChain
releases, so this module builds the equivalent pipeline using LCEL
(retriever -> prompt -> LLM via RunnableParallel). The LLM is accessed
through Groq's OpenAI-compatible endpoint using langchain_openai's
ChatOpenAI client with a custom base_url.
"""
import functools
from typing import Optional

import structlog
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.documents import Document

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


def _format_docs(docs: list[Document]) -> str:
    """Concatenate retrieved passages into a single context block ('stuff' strategy)."""
    context = "\n\n".join(doc.page_content for doc in docs)
    return enforce_token_budget(context, settings.RAG_MAX_CONTEXT_TOKENS)


class RagChain:
    """
    Thin wrapper exposing the same call surface the rest of the codebase
    expects from a RetrievalQA chain: .invoke()/.ainvoke() taking
    {"query": ...} and returning {"result": ..., "source_documents": [...]}.
    """

    def __init__(self, retriever, llm, prompt: PromptTemplate):
        self._retriever = retriever
        self._llm = llm
        self._prompt = prompt

        self._chain = RunnableParallel(
            source_documents=self._retriever,
            question=RunnablePassthrough(),
        ) | RunnableParallel(
            source_documents=lambda x: x["source_documents"],
            result=(
                {
                    "context": lambda x: _format_docs(x["source_documents"]),
                    "question": lambda x: x["question"],
                }
                | self._prompt
                | self._llm
                | StrOutputParser()
            ),
        )

    def invoke(self, inputs: dict) -> dict:
        question = inputs["query"]
        out = self._chain.invoke(question)
        return {"result": out["result"], "source_documents": out["source_documents"]}

    async def ainvoke(self, inputs: dict, config: Optional[dict] = None) -> dict:
        question = inputs["query"]
        out = await self._chain.ainvoke(question, config=config)
        return {"result": out["result"], "source_documents": out["source_documents"]}


@functools.lru_cache(maxsize=256)
def build_rag_chain(isbn: str) -> RagChain:
    """
    Build RAG chain for a book (cached per ISBN).

    Uses Groq's OpenAI-compatible API as the LLM provider.

    Args:
        isbn: Book ISBN

    Returns:
        RagChain wrapping retriever -> prompt -> LLM (LCEL pipeline)
    """
    llm = ChatOpenAI(
        model=settings.RAG_LLM_MODEL,
        base_url=settings.RAG_LLM_BASE_URL,
        api_key=settings.GROQ_API_KEY,
        temperature=0.1,
        streaming=True,
    )

    retriever = get_retriever(isbn, top_k=settings.RAG_TOP_K)

    chain = RagChain(retriever=retriever, llm=llm, prompt=SYSTEM_PROMPT)

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


async def invoke_chain(isbn: str, question: str) -> dict:
    """
    Invoke RAG chain with token budget enforcement.

    Args:
        isbn: Book ISBN
        question: User question

    Returns:
        Dict with answer and citations
    """
    chain = build_rag_chain(isbn)

    result = await chain.ainvoke({"query": question})

    answer = result.get("result", "")
    source_docs = result.get("source_documents", [])

    citations = extract_citations(source_docs)

    return {
        "answer": answer,
        "citations": citations,
    }