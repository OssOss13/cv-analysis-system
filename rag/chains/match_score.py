from langchain_core.prompts import ChatPromptTemplate
from rag.chains.llm import get_llm
from rag.schemas import CVMatchScoreSchema
from rag.prompts import MATCH_SCORE_SYSTEM_PROMPT

def get_match_score_chain():
    llm = get_llm()

    # Structured output
    llm_structured = llm.with_structured_output(CVMatchScoreSchema)

    prompt = ChatPromptTemplate.from_messages([
        ("system", MATCH_SCORE_SYSTEM_PROMPT),
        ("user", 
        """
        CV SUMMARY:
        {cv_summary}

        POSITION DETAILS:
        {position_details}
        """)
    ])

    return prompt | llm_structured

# should it take TOON object?
def generate_match_score(cv_summary: dict, position_details: dict) -> CVMatchScoreSchema:
    chain = get_match_score_chain()

    return chain.invoke({
        "cv_summary": cv_summary,
        "position_details": position_details
    })
