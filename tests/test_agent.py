import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
django.setup()

from rag.agent import simple_agent_query

# Test queries
queries = [
    "What CVs do you have?",
    "Who has the most Python experience?",
    "Tell me about John Doe's projects",
    "Compare all candidates with Machine Learning skills",
]

for query in queries:
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")
    answer = simple_agent_query(query)
    print(f"Answer: {answer}\n")