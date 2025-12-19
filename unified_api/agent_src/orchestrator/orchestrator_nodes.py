from typing import TypedDict, Annotated, Sequence, Literal, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
import os
from ..config import GROQ_API_KEY

if GROQ_API_KEY:
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.5)

class OrchestratorState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next_agent: Literal["marketing_agent", "general_chat", "END"]
    # Marketing Agent State Fields
    product_details: Optional[str]
    strategies: Optional[list[str]]
    selected_strategy: Optional[str]
    satisfaction: bool
    guided: bool
    user_email: Optional[str]
    strategy_guide: Optional[str]
    email_sent: bool

def router_node(state: OrchestratorState) -> dict:
    """
    Analyzes the user's input to determine the intent.
    Routes to 'marketing_agent' or 'general_chat'.
    """
    messages = state["messages"]
    if not messages:
        return {"next_agent": "general_chat"}
        
    last_message = messages[-1]
    if not isinstance(last_message, HumanMessage):
        return {"next_agent": "general_chat"}

    # Get the last few messages for context (e.g., last 3)
    # This helps if the user says "yes" to a previous question
    recent_messages = messages[-3:]
    conversation_context = "\n".join([f"{msg.type}: {msg.content}" for msg in recent_messages])

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an intelligent router for an AI Agent system.
        Your job is to classify the user's intent into one of two categories:
        1. 'marketing': The user wants marketing advice, strategies, product promotion, or business growth help. Also select this if the user is answering 'yes' to a question about needing marketing help.
        2. 'general': The user is greeting, asking who you are, or making small talk.

        Here is the recent conversation context:
        {context}

        Based on the last user message, output ONLY one word: 'marketing' or 'general'."""),
    ])
    
    chain = prompt | llm | StrOutputParser()
    intent = chain.invoke({"context": conversation_context}).strip().lower()
    
    if "marketing" in intent:
        return {"next_agent": "marketing_agent"}
    else:
        return {"next_agent": "general_chat"}

def general_chat_node(state: OrchestratorState) -> dict:
    """
    Handles general small talk and greetings.
    """
    messages = state["messages"]
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the Orchestrator of the AI Marketing System. You are helpful and polite. If the user greets you, greet them back and ask if they need help with marketing strategies. Keep it brief."),
        ("human", "{user_input}"),
    ])
    
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({"user_input": messages[-1].content})
    
    return {"messages": [AIMessage(content=response)], "next_agent": "END"}
