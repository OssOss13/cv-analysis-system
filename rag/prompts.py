from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import PydanticOutputParser
from rag.schemas import CVSummarySchema
from langchain_core.prompts import PromptTemplate

# 1. Contextualize Question Prompt
# This prompt reformulates the latest user question to stand alone, given the chat history.
CONTEXTUALIZE_Q_SYSTEM_PROMPT = """Given a chat history and the latest user question \
which might reference context in the chat history, formulate a standalone question \
which can be understood without the chat history. Do NOT answer the question, \
just reformulate it if needed and otherwise return it as is."""

contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", CONTEXTUALIZE_Q_SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

# 2. QA Prompt
# This is the prompt for answering the question using the retrieved context.
QA_SYSTEM_PROMPT = """
You are an expert HR assistant analyzing candidate CVs.

You MUST follow these rules:
- Only use information from the context documents provided below.
- If the answer is not in the context, say: "I cannot find this information in the CV."
- Never guess or hallucinate.
- Provide clear, concise, and factual replies.

### CONTEXT DOCUMENTS ###
{context}
### END CONTEXT ###
"""

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", QA_SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)



# The prompt instructs the LLM to return strict JSON matching the model
SUMMARY_SYSTEM_PROMPT = """
You will be given the extracted text of a candidate CV. Produce a JSON object with the following keys:
- name (string or null)
- current_title (string or null)
- years_experience (float or null)
- skills (list of short strings)
- education (list of short strings)
- certifications (list of short strings)
- work_history (list of short strings)
- emails (list of strings of 1 email or more if multiple)

Rules:
- Return ONLY valid JSON (no extra commentary).
- Use null for missing values.
- years_experience must be a float if present; otherwise null.
- Keep skill strings short (single token phrases like "Python", "Machine Learning").
- emails must be list of strings of 1 email or more if multiple.

CV_TEXT:
{cv_text}

Output valid JSON only.
"""

# SUMMARY OR CV_TEXT
MATCH_SCORE_SYSTEM_PROMPT = """
You are an AI hiring assistant. You will evaluate how well a candidate fits a job position.

You will be given:

1. CV SUMMARY — a structured summary of the candidate’s skills, experience, education, and history.
2. POSITION DETAILS — job title, description, required skills, responsibilities and seniority.

Your task:

- Produce a match score between 0 and 100.
- Consider ONLY the information given. Do NOT hallucinate missing details.
- Score based mainly on skill overlap and experience relevance.
- Return a short explanation (max 50 words).
- Return a list of matched skills (skills appearing both in CV and the position requirements).

OUTPUT FORMAT:
Return ONLY valid JSON that matches the CVMatchScoreSchema.
"""
