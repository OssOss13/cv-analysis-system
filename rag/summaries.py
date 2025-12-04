from langchain_openai import ChatOpenAI
import os 
from rag.prompts import summary_prompt, cv_summary_parser
from rag.schemas import CVSummarySchema
from dotenv import load_dotenv

load_dotenv()

def get_cv_summary_chain():
    """
    Creates a chain that turns raw CV text into a structured CVSummarySchema.
    """
    llm = ChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    return summary_prompt | llm | cv_summary_parser

def generate_cv_summary(cv_text: str) -> CVSummarySchema:
    """
    Takes raw CV text and returns a standardized CVSummarySchema.
    """
    chain = get_cv_summary_chain()
    return chain.invoke({"cv_text": cv_text})
