import os
import django
from django.conf import settings
import logging
from dotenv import load_dotenv

load_dotenv()

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rag.vectorstore import get_vectorstore

def check_chroma_content(cv_id=None):
    print(f"Checking ChromaDB content" + (f" for CV ID: {cv_id}" if cv_id else " for all CVs") + "...")
    
    try:
        vectorstore = get_vectorstore()
        collection = vectorstore._collection
        
        # Build query
        where_clause = {}
        if cv_id:
            where_clause = {"cv_id": int(cv_id)}
            
        # Get all items matching the filter
        results = collection.get(where=where_clause)
        
        ids = results['ids']
        metadatas = results['metadatas']
        documents = results['documents']
        
        count = len(ids)
        print(f"Found {count} documents in ChromaDB matching criteria.")
        
        if count == 0:
            print("No documents found.")
            return

        summary_count = 0
        chunk_count = 0
        
        print("\n--- Document Details ---")
        for i in range(count):
            meta = metadatas[i]
            doc_type = meta.get('type', 'unknown')
            
            if doc_type == 'summary':
                summary_count += 1
                print(f"\n[SUMMARY DOCUMENT]")
                print(f"ID: {ids[i]}")
                print(f"Metadata: {meta}")
                print(f"Content Preview: {documents[i][:200]}...")
            elif doc_type == 'chunk':
                chunk_count += 1
                # Only print first few chunks to avoid spam
                if chunk_count <= 3:
                    print(f"\n[CHUNK DOCUMENT #{chunk_count}]")
                    print(f"ID: {ids[i]}")
                    print(f"Metadata: {meta}")
                    print(f"Content Preview: {documents[i][:100]}...")
            else:
                print(f"\n[UNKNOWN TYPE DOCUMENT]")
                print(f"ID: {ids[i]}")
                print(f"Metadata: {meta}")

        print(f"\n--- Statistics ---")
        print(f"Total Documents: {count}")
        print(f"Summary Documents: {summary_count}")
        print(f"Chunk Documents: {chunk_count}")
        
        if cv_id:
            if summary_count > 0:
                print(f"\nSUCCESS: Summary found for CV {cv_id}.")
            else:
                print(f"\nWARNING: No summary found for CV {cv_id}.")
                
            if chunk_count > 0:
                print(f"SUCCESS: {chunk_count} full text chunks found for CV {cv_id}.")
            else:
                print(f"WARNING: No text chunks found for CV {cv_id}.")

    except Exception as e:
        print(f"Error checking ChromaDB: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    cv_id_arg = None
    if len(sys.argv) > 1:
        cv_id_arg = sys.argv[1]
    
    # Default to 30 if not provided, as per user context, or just list all if user wants
    # But for this specific request, I'll default to checking 30 if no arg provided, 
    # but actually the user might want to see everything.
    # Let's check for 30 specifically as requested.
    target_id = cv_id_arg if cv_id_arg else 30
    check_chroma_content(target_id)
