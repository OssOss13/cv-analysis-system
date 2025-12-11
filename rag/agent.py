import logging
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnablePassthrough
from langchain_core.agents import AgentFinish
from langgraph.prebuilt import create_react_agent
from rag.tools import search_cv_summaries, search_cv_details, list_all_cvs
from rag.chains.llm import get_llm

logger = logging.getLogger(__name__)

def get_cv_agent_executor():
    """
    Creates an agent that uses bind_tools for automatic tool documentation.
    
    Returns:
        Configured agent
    """
    llm = get_llm()
    
    # Define available tools
    tools = [search_cv_summaries, search_cv_details, list_all_cvs]
    
    # Bind tools to LLM - this automatically uses the tool docstrings
    llm_with_tools = llm.bind_tools(tools)
    
    # Simplified system prompt - no need to explain tools manually
    system_prompt = """You are an expert HR assistant specializing in CV analysis and candidate evaluation.

### Your Role ###
- Analyze and compare candidate CVs
- Answer questions about candidate qualifications
- Help find the best candidates for specific roles
- Provide detailed insights about candidate experience

### Guidelines ###
- ONLY use information from tool results - never make assumptions
- Always cite which CV/candidate you're referring to (by name or filename)
- When comparing candidates, provide clear rankings with specific reasoning
- If no relevant information is found, state this clearly
- Be concise but thorough in your analysis
- Use tools strategically 
- If the question is about multiple candidates, ALWAYS use search_cv_summaries.
- If the question is about one candidate or specific details, ALWAYS use search_cv_details.

### Response Format ###
- Use clear, professional language
- Structure comparisons in an easy-to-read format
- Include specific data points (years of experience, skills, etc.)
- Highlight key differences between candidates when comparing
"""

# Create the agent using LangGraph's prebuilt agent
    agent = create_react_agent(
        llm_with_tools, 
        tools,
        prompt=system_prompt
    )
    
    return agent


def format_chat_history(messages: List[Dict[str, str]]) -> List:
    """
    Convert Django message format to LangChain message format.
    
    Args:
        messages: List of dicts with 'sender' and 'text' keys
    
    Returns:
        List of LangChain message objects
    """
    formatted = []
    for msg in messages:
        if msg['sender'] == 'user':
            formatted.append(HumanMessage(content=msg['text']))
        else:
            formatted.append(AIMessage(content=msg['text']))
    return formatted


def invoke_cv_agent(query: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Invoke the CV agent with a user query.
    
    Args:
        query: User's question
        chat_history: List of previous messages [{"sender": "user/bot", "text": "..."}]
    
    Returns:
        Dict with 'answer', 'steps', and 'sources'
    """
    try:
        logger.info(f"Invoking agent with query: {query}")
        
        agent = get_cv_agent_executor()
        
        # Format chat history
        formatted_history = format_chat_history(chat_history or [])
        
        # Prepare input
        inputs = {
            "messages": formatted_history + [HumanMessage(content=query)]
        }
        
        # Invoke agent
        result = agent.invoke(inputs)
        
        # Extract the final answer
        final_message = result["messages"][-1]
        answer = final_message.content
        logger.info(f"Agent response(answer): {answer}")
        
        # Extract tool usage for sources
        sources = []
        for msg in result["messages"]:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    sources.append({
                        "tool": tool_call.get("name", "unknown"),
                        "input": tool_call.get("args", {}),
                    })
        
        return {
            "answer": answer,
            "steps": len(result["messages"]),
            "sources": sources
        }
        
    except Exception as e:
        logger.error(f"Error invoking agent: {e}", exc_info=True)
        return {
            "answer": f"I encountered an error while processing your query: {str(e)}",
            "steps": 0,
            "sources": []
        }

def simple_agent_query(query: str) -> str:
    """
    Convenience wrapper for testing - returns just the answer.
    
    Args:
        query: User's question
    
    Returns:
        Agent's answer as string
    """
    result = invoke_cv_agent(query, [])
    return result["answer"]