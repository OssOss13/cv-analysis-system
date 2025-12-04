import os
from langchain_openai import ChatOpenAI
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.history_aware_retriever import create_history_aware_retriever
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.messages import HumanMessage, AIMessage
from django.core.cache import cache
from dotenv import load_dotenv
from rag.prompts import contextualize_q_prompt, qa_prompt
from rag.vectorstore import get_vectorstore
from functools import lru_cache

load_dotenv()

def get_llm():
    """
    Returns a new LLM instance.
    """
    return ChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        streaming=True
)

# ============================================================================
# DEPRECATED: These functions are kept for backward compatibility
# Use rag.agent.invoke_cv_agent() instead for the agent-based approach
# ============================================================================

@lru_cache(maxsize=1)
def get_global_rag_chain():
    return get_rag_chain()


def get_rag_chain(user_id=None):
    """
    Creates the full RAG chain:
     - history-aware question reformulation
     - retriever
     - QA chain
    """

    llm = get_llm()
    vectorstore = get_vectorstore()

    # Create retriever with metadata filtering
    search_kwargs = {"k": 5}
    if user_id:
        search_kwargs["filter"] = {"user_id": user_id}
    
    retriever = vectorstore.as_retriever(search_kwargs=search_kwargs)

    # Step 1: Make retriever history-aware
    history_aware = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    # Step 2: QA chain (stuffing retrieved docs)
    qa_chain = create_stuff_documents_chain(llm, qa_prompt)

    # Step 3: Full RAG chain
    return create_retrieval_chain(history_aware, qa_chain)


def invoke_rag(query: str, chat_history: list):
    """
    Run the RAG chain and return the answer + sources.
    chat_history should be a list of LangChain messages.
    """

    # Use caching for frequently asked questions
    cache_key = f"rag_{hash(query)}_{user_id}"
    cached_result = cache.get(cache_key)
    
    if cached_result and not chat_history:  # Only use cache for first question
        return cached_result

    rag_chain = get_global_rag_chain()
    response = rag_chain.invoke({
        "input": query,
        "chat_history": chat_history
    })

    result = {
        "answer": response["answer"],
        "sources": response.get("context", [])
    }
    # Cache for 5 minutes
    if not chat_history:
        cache.set(cache_key, result, 300)
    
    return result


def simple_query(query: str):
    """Convenience wrapper for testing."""
    result = invoke_rag(query, [])
    return result["answer"]