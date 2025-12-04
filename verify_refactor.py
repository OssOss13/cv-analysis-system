import os
import django
from django.test import RequestFactory
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from documents import views as doc_views
from chatbot import views as chat_views
from rag.agent import get_cv_agent_executor

def verify_views():
    print("Verifying Views...")
    factory = RequestFactory()
    
    # Verify list_cvs
    try:
        request = factory.get('/documents/list/')
        response = doc_views.list_cvs(request)
        if response.status_code == 200:
            print("✅ documents.views.list_cvs passed")
        else:
            print(f"❌ documents.views.list_cvs failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ documents.views.list_cvs raised exception: {e}")

    # Verify upload_cv (GET)
    try:
        request = factory.get('/documents/upload/')
        response = doc_views.upload_cv(request)
        if response.status_code == 200:
            print("✅ documents.views.upload_cv (GET) passed")
        else:
            print(f"❌ documents.views.upload_cv (GET) failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ documents.views.upload_cv (GET) raised exception: {e}")

    # Verify chatbot_view
    try:
        request = factory.get('/chatbot/')
        response = chat_views.chatbot_view(request)
        if response.status_code == 200:
            print("✅ chatbot.views.chatbot_view passed")
        else:
            print(f"❌ chatbot.views.chatbot_view failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ chatbot.views.chatbot_view raised exception: {e}")

def verify_agent():
    print("\nVerifying Agent Initialization...")
    try:
        agent = get_cv_agent_executor()
        print("✅ rag.agent.get_cv_agent_executor passed")
    except Exception as e:
        print(f"❌ rag.agent.get_cv_agent_executor raised exception: {e}")

if __name__ == "__main__":
    verify_views()
    verify_agent()
