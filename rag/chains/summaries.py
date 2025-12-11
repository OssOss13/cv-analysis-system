from rag.chains.llm import get_llm
from rag.prompts import SUMMARY_SYSTEM_PROMPT
from rag.schemas import CVSummarySchema
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

def get_cv_summary_chain():
    """
    Creates a chain that turns raw CV text into a structured CVSummarySchema.
    """
    llm = get_llm()

    llm_structured = llm.with_structured_output(CVSummarySchema)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SUMMARY_SYSTEM_PROMPT),
            ("human", "CV_TEXT:\n{cv_text}"),
        ]
    )    
    return prompt | llm_structured

def generate_cv_summary(cv_text: str) -> CVSummarySchema:
    """
    Takes raw CV text and returns a standardized CVSummarySchema.
    """
    return get_cv_summary_chain().invoke({"cv_text": cv_text})
