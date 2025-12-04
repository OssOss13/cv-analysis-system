# rag/tools.py
import logging
from typing import List, Dict, Any, Optional
from langchain.tools import tool
from rag.vectorstore import search_cvs_by_criteria
from documents.models import CV, CVSummary
from rag.ingestion import format_summary_for_embedding
from rag.schemas import CVSummarySchema

logger = logging.getLogger(__name__)


@tool
def search_cv_summaries(query: str, top_k: int = 10) -> str:
    """
    Search across all CV summaries to compare and rank multiple candidates. The summary consists of the following fields:
    - name
    - current_title
    - years_experience
    - skills
    - work_experience
    - education
    - certifications

    
    Use this tool when the user wants to:
    - Compare multiple candidates
    - Find the best match for a role
    - Rank candidates by experience or skills
    - Ask "who has the most X" or "which candidate is best for Y"
    
    Args:
        query: The search query describing what you're looking for
        top_k: Number of CVs to return (default 10)
    
    Returns:
        Formatted string with CV summaries for comparison
    """
    try:
        logger.info(f"Searching CV summaries with query: {query}")
        
        results = search_cvs_by_criteria(
            query=query,
            filter_dict={"type": "summary"},
            top_k=top_k,
            with_scores=True
        )
        
        if not results:
            return "No CVs found matching your criteria."
        
        # Format results for the LLM
        formatted_output = f"Found {len(results)} candidate(s):\n\n"
        
        for idx, (doc, score) in enumerate(results, 1):
            cv_id = doc.metadata.get("cv_id")
            filename = doc.metadata.get("filename", "Unknown")
            candidate_name = doc.metadata.get("candidate_name", "Unknown")

            similarity_pct = max(0, (1 - score) * 100)

            formatted_output += f"{'='*60}\n"
            formatted_output += f"Candidate #{idx} (Match: {similarity_pct:.1f}%)\n"
            formatted_output += f"{'='*60}\n"
            formatted_output += f"CV ID: {cv_id}\n"
            formatted_output += f"Name: {candidate_name}\n"
            formatted_output += f"Filename: {filename}\n"
            formatted_output += f"\nProfile:\n{doc.page_content}\n\n"
        
        return formatted_output
        
    except Exception as e:
        logger.error(f"Error searching CV summaries: {e}")
        return f"Error searching CVs: {str(e)}"


@tool
def search_cv_details(query: str, cv_id: Optional[int] = None, top_k: int = 5) -> str:
    """
    Search detailed CV content for specific information.
    
    This tool searches the full text of a CV and is ideal for:
    - Getting specific details about one candidate
    - Finding information about projects, responsibilities, or achievements
    - Questions about educational background, certifications, or work history
    - Extracting specific examples or case studies from a CV
    
    Args:
        query: The specific information you need (e.g., "Django projects", "leadership experience")
        cv_id: Optional - Limit search to a specific CV if you know the ID
        top_k: Number of relevant sections to return (default 5)
    
    Returns:
        Detailed CV sections matching your query
    """
    try:
        logger.info(f"Searching CV details with query: {query}, cv_id: {cv_id}")
        
        if not cv_id:
           filter_dict = {"type": "chunk"}
        else:
            # get the cv_id from the summary id as the agent invokes summary id.
            summary = CVSummary.objects.filter(id=cv_id).first()
            summary_cv_id = summary.cv_id
            filter_dict = {"cv_id": summary_cv_id}
        
        results = search_cvs_by_criteria(
            query=query,
            filter_dict=filter_dict,
            top_k=top_k,
            with_scores=True
        )
        
        if not results:
            cv_context = f" in CV {cv_id}" if cv_id else ""
            return f"No detailed information found{cv_context} matching your query."
        
        # Group results by CV to avoid redundancy
        cv_sections = {}
        for doc, score in results:
            doc_cv_id = doc.metadata.get("cv_id")
            if doc_cv_id not in cv_sections:
                cv_sections[doc_cv_id] = {
                    "filename": doc.metadata.get("filename", "Unknown"),
                    "sections": []
                }
            
            # Convert distance to similarity
            similarity_pct = max(0, (1 - score) * 100)
            
            cv_sections[doc_cv_id]["sections"].append({
                "content": doc.page_content,
                "page": doc.metadata.get("page", "Unknown"),
                "similarity": similarity_pct
            })
        
        # Format output
        formatted_output = f"Found relevant information in {len(cv_sections)} CV(s):\n\n"
        
        for doc_cv_id, data in cv_sections.items():
            formatted_output += f"{'='*60}\n"
            formatted_output += f"CV ID: {doc_cv_id} - {data['filename']}\n"
            formatted_output += f"{'='*60}\n\n"
            
            for idx, section in enumerate(data['sections'], 1):
                formatted_output += f"--- Section {idx} (Page {section['page']}, Match: {section['similarity']:.1f}%) ---\n"
                formatted_output += f"{section['content']}\n\n"
        
        return formatted_output
        
    except Exception as e:
        logger.error(f"Error searching CV details: {e}", exc_info=True)
        return f"Error searching CV details: {str(e)}"


@tool
def list_all_cvs() -> str:
    """
    List all uploaded CVs with basic information.
    
    Use this tool to:
    - Know the total number of CVs
    - See what CVs are available in the system
    - Get an overview of all candidates
    - Find the CV ID for a specific candidate
    
    Returns:
        Complete list of all CVs with candidate names, titles, and experience
    """
    try:
        logger.info("Listing all CVs")
        
        cvs = CV.objects.select_related('summary').order_by('-uploaded_at')
        
        if not cvs.exists():
            return "No CVs have been uploaded yet."
        
        formatted_output = f"Total CVs in system: {cvs.count()}\n\n"
        
        for idx, cv in enumerate(cvs, 1):
            formatted_output += f"{'='*70}\n"
            formatted_output += f"CV #{idx}\n"
            formatted_output += f"{'='*70}\n"
            
            if hasattr(cv, 'summary') and cv.summary.summary_json:
                # Convert JSON back to CVSummarySchema object
                summary_dict = cv.summary.summary_json
                summary_model = CVSummarySchema(**summary_dict)
                
                # Reuse the same formatting function used during ingestion!
                formatted_summary = format_summary_for_embedding(
                    summary_model=summary_model,
                    cv_filename=cv.file.name
                )
                
                formatted_output += formatted_summary
            else:
                # Fallback if no summary exists
                formatted_output += f"CV ID: {cv.id}\n"
                formatted_output += f"Filename: {cv.file.name}\n"
                formatted_output += f"Uploaded: {cv.uploaded_at.strftime('%Y-%m-%d %H:%M')}\n"
                formatted_output += "Status: Processing or no summary available\n"
            
            formatted_output += "\n"
        
        return formatted_output
        
    except Exception as e:
        logger.error(f"Error listing CVs: {e}", exc_info=True)
        return f"Error listing CVs: {str(e)}"