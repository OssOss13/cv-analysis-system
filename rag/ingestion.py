from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rag.vectorstore import get_vectorstore
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import os
import uuid
from rag.chains.summaries import generate_cv_summary
from documents.models import CV
import logging
from documents.models import CVSummary

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def save_cv(uploaded_file):
    """
    Saves the file into MEDIA_ROOT/cvs/ and returns the relative path.
    """

    # Generate unique file name to avoid overwrite
    ext = uploaded_file.name.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"

    # Path inside media/
    file_path = os.path.join("cvs", filename)

    # Save file
    saved_path = default_storage.save(file_path, ContentFile(uploaded_file.read()))

    return saved_path   # example: "cvs/9f22b33d-1234.pdf"

def extract_full_text(file_path):
    """Use PyPDFLoader to extract text. file_path is the relative path in MEDIA_ROOT or absolute path."""
    # If relative path, convert to absolute
    if not os.path.isabs(file_path):
        abs_path = os.path.join(settings.MEDIA_ROOT, file_path)
    else:
        abs_path = file_path

    loader = PyPDFLoader(abs_path)
    pages = loader.load()
    # Concatenate page content for summary generation (keep full text)
    text = "\n\n".join([p.page_content for p in pages])
    return text, pages


def chunk_documents(pages, chunk_size=1000, chunk_overlap=200):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap, 
        add_start_index=True)
    return splitter.split_documents(pages)


def ingest_cv_and_create_summary_by_id(cv_id: int):
    """
    Master ingestion function for a CV already saved as a CV model.
    This will:
     - extract text
     - chunk & embed chunks
     - generate structured summary
     - save summary to Django DB (CVSummary model)
     - create human-readable summary text
     - embed the summary as its own document
    """
    try:
        cv = CV.objects.get(id=cv_id)
    except CV.DoesNotExist:
        logger.error(f"CV with id {cv_id} not found")
        raise ValueError(f"CV with id {cv_id} not found")

    try:
        # Update status
        cv.is_processed = False
        cv.processing_error = None
        cv.save()

        logger.info(f"Starting ingestion for CV {cv_id}: {cv.file.name}")

        # 1) Extract text + pages
        abs_file_path = cv.file.path
        full_text, pages = extract_full_text(abs_file_path)

        if not full_text.strip():
            raise ValueError("No text could be extracted from the PDF")

        # 2) Chunk the document pages
        chunks = chunk_documents(pages)
        logger.info(f"Created {len(chunks)} chunks for CV {cv_id}")

        # 3) Add metadata to chunks
        for c in chunks:
            c.metadata["cv_id"] = cv_id
            c.metadata["type"] = "chunk"  # Distinguish from summary
            c.metadata["filename"] = cv.file.name

        # 4) Add chunk documents to vectorstore
        vectorstore = get_vectorstore()
        vectorstore.add_documents(chunks)  
        logger.info(f"Added {len(chunks)} chunks to ChromaDB for CV {cv_id}")
    

        # 5) Generate structured summary using LLM
        summary_model = generate_cv_summary(full_text)
        logger.info(f"Generated summary for CV {cv_id}: {summary_model.name}")

        # 6) Save summary in DB
        # If exists, update
        cv_summary, created = CVSummary.objects.update_or_create(cv=cv, defaults={"summary_json": summary_model.dict()})
        logger.info(f"Saved summary for CV {cv_id}: {cv_summary}")
        action = "Created" if created else "Updated"
        logger.info(f"{action} CVSummary in DB for CV {cv_id}")

        # 7) Embed the summary itself as a single document (to support global comparisons)
        from langchain_core.documents import Document 
        summary_text = format_summary_for_embedding(summary_model, cv.file.name)
        logger.info(f"Formatted summary text:\n{summary_text}")
       
        summary_doc = Document(
            page_content=summary_text, 
            metadata={
                "cv_id": cv_id,
                "type": "summary",  # Critical: marks this as a summary document
                "filename": cv.file.name,
                "candidate_name": summary_model.name or "Unknown",
                "years_experience": summary_model.years_experience or 0,
            })
        vectorstore.add_documents([summary_doc])
        logger.info(f"Added summary document to ChromaDB for CV {cv_id}")
        
        # Mark as processed
        cv.is_processed = True
        cv.save()
        
        logger.info(f"Successfully ingested CV {cv_id}")
        return True

    except Exception as e:
        logger.error(f"Error ingesting CV {cv_id}: {str(e)}")
        cv.is_processed = False
        cv.processing_error = str(e)
        cv.save()
        raise


def format_summary_for_embedding(summary_model, cv_filename: str) -> str:
    """
    Convert CVSummarySchema into human-readable text for semantic search.
    This makes it easier for the LLM to compare CVs.
    """
    parts = [f"CV Filename: {cv_filename}"]
    
    if summary_model.name:
        parts.append(f"Candidate Name: {summary_model.name}")
    
    if summary_model.current_title:
        parts.append(f"Current Title: {summary_model.current_title}")
    
    if summary_model.years_experience is not None:
        parts.append(f"Years of Experience: {summary_model.years_experience}")
    
    if summary_model.skills:
        parts.append(f"Skills: {', '.join(summary_model.skills)}")
    
    if summary_model.education:
        parts.append(f"Education: {' | '.join(summary_model.education)}")
    
    if summary_model.certifications:
        parts.append(f"Certifications: {', '.join(summary_model.certifications)}")
    
    if summary_model.work_history:
        parts.append(f"Work History: {' | '.join(summary_model.work_history)}")

    if summary_model.emails:
        parts.append(f"Emails: {' | '.join(summary_model.emails)}")
    
    return "\n".join(parts)
