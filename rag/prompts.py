from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import PydanticOutputParser
from rag.schemas import CVSummarySchema

# 1. Contextualize Question Prompt
# This prompt reformulates the latest user question to stand alone, given the chat history.
contextualize_q_system_prompt = """Given a chat history and the latest user question \
which might reference context in the chat history, formulate a standalone question \
which can be understood without the chat history. Do NOT answer the question, \
just reformulate it if needed and otherwise return it as is."""

contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

# 2. QA Prompt
# This is the prompt for answering the question using the retrieved context.
qa_system_prompt = """
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
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)



# The prompt instructs the LLM to return strict JSON matching the model
SUMMARY_PROMPT = """
You will be given the extracted text of a candidate CV. Produce a JSON object with the following keys:
- name (string or null)
- current_title (string or null)
- years_experience (float or null)
- skills (list of short strings)
- education (list of short strings)
- certifications (list of short strings)
- work_history (list of short strings)

Rules:
- Return ONLY valid JSON (no extra commentary).
- Use null for missing values.
- years_experience must be a float if present; otherwise null.
- Keep skill strings short (single token phrases like "Python", "Machine Learning").

CV_TEXT:
{cv_text}
"""

# Parser for extracting the model from the LLM output
cv_summary_parser = PydanticOutputParser(pydantic_object=CVSummarySchema)

summary_prompt = ChatPromptTemplate.from_template(
    SUMMARY_PROMPT
    ).partial(schema=cv_summary_parser.get_format_instructions())


