from django.conf import settings
import os
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import logging

logger = logging.getLogger(__name__)

persist_directory = os.path.join(settings.MEDIA_ROOT, "chroma_db")

def get_vectorstore():
    """
    Returns a Chroma vectorstore instance.
    If the directory does not exist, Chroma automatically creates it.
    """
    return Chroma(
        collection_name="cv_embeddings",
        persist_directory=persist_directory,
        embedding_function=OpenAIEmbeddings(),
    )

def delete_cv_from_vectorstore(cv_id: int):
    """Delete all embeddings associated with a CV."""
    try:
        vectorstore = get_vectorstore()
        # Chroma delete by metadata filter
        vectorstore._collection.delete(
            where={"cv_id": cv_id}
        )
        logger.info(f"Deleted embeddings for CV {cv_id}")
    except Exception as e:
        logger.error(f"Error deleting CV {cv_id} from vectorstore: {e}")

def get_retriever():
    """Create retriever fresh each time to include latest embeddings."""
    return get_vectorstore().as_retriever()


# Helper function for the tools
def search_cvs_by_criteria(query: str, filter_dict: dict = None, top_k: int = 5, with_scores: bool = True):
    """
    Search CVs based on semantic similarity with optional filtering.
    
    Args:
        query: Search query
        filter_dict: Metadata filter (e.g., {"type": "summary"})
        top_k: Number of results to return
        with_scores: If True, return (document, score) tuples; if False, return just documents
    
    Returns:
        List of documents or list of (document, score) tuples
    """
    vectorstore = get_vectorstore()
    
    if with_scores:
        results = vectorstore.similarity_search_with_score(
            query, 
            k=top_k,
            filter=filter_dict
        )
    else:
        results = vectorstore.similarity_search(
            query, 
            k=top_k,
            filter=filter_dict
        )
    
    return results

