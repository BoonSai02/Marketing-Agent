import os
import re
import uuid
from typing import TypedDict, Annotated, Sequence, Optional

import streamlit as st
from dotenv import load_dotenv
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

# --- Setup and Configuration ---

load_dotenv()

# Set up API key
os.environ["GROQ_API_KEY"] = os.getenv('GROQ_API_KEY')

# Initialize LLM
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.7)

# Initialize web search tool
web_search_wrapper = DuckDuckGoSearchAPIWrapper()

# --- LangGraph Agent Definition ---

# Define the state
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    product_details: Optional[str]
    strategies: Optional[list[str]]
    selected_strategy: Optional[str]
    satisfaction: bool
    guided: bool

# --- Node Definitions ---

def gather_product_details(state: AgentState) -> dict:
    """Gathers product details from the user."""
    messages = state["messages"]
    if messages and isinstance(messages[-1], HumanMessage):
        user_input = messages[-1].content
        extract_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert at extracting product details from a user's message. Summarize the user's description into a structured format. Output ONLY in this format, no more no less:\nName: [name or 'unknown']\nFeatures: [comma-separated list or 'unknown']\nTarget Audience: [description or 'unknown']\nGoals: [description or 'unknown']"),
            ("human", "{user_input}"),
        ])
        extract_chain = extract_prompt | llm | StrOutputParser()
        product_details_raw = extract_chain.invoke({"user_input": user_input})
        
        if product_details_raw.strip().startswith('Name:') and '\n' in product_details_raw:
            if not all('unknown' in field.lower() for field in product_details_raw.split('\n')):
                confirmation = f"Understood. Based on your input, here's what I've gathered about your product:\n\n{product_details_raw.strip()}"
                return {"product_details": product_details_raw.strip(), "messages": [AIMessage(content=confirmation)]}

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful marketing assistant. Ask concise questions to gather key details about the product, service, or business you are being asked to market. Use a numbered list."),
        MessagesPlaceholder(variable_name="messages"),
    ])
    response = (prompt | llm | StrOutputParser()).invoke({"messages": messages})
    return {"messages": [AIMessage(content=response)]}

def generate_strategies(state: AgentState) -> dict:
    """Generates marketing strategies with specific source URLs."""
    product_details = state["product_details"]
    
    # Generate a dynamic search query based on the product details
    query_generation_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert at crafting effective web search queries. Based on the following product details, generate a single, concise search query to find the best marketing strategies. Output ONLY the search query itself, with no extra text or quotation marks."),
        ("human", "{product_details}"),
    ])
    query_generation_chain = query_generation_prompt | llm | StrOutputParser()
    search_query = query_generation_chain.invoke({"product_details": product_details})
    
    st.write(f"🔍 Searching the web for: `{search_query}`") # Show the user what's being searched
    search_results_list = web_search_wrapper.results(search_query, max_results=5)
    
    source_map = {i + 1: result['link'] for i, result in enumerate(search_results_list)}
    formatted_search_results = "\n\n".join(
        [f"Source [{i+1}]:\nTitle: {res['title']}\nSnippet: {res['snippet']}" for i, res in enumerate(search_results_list)]
    )
    
    citation_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a marketing expert. Based on the web search results provided below, generate 3-5 concise, actionable marketing strategies. For each strategy, you MUST cite the source number (e.g., 'Source: [1]') from which the idea was primarily derived. Output ONLY in this format, with each strategy on a new line:\n1. [1-2 sentence description]. (Source: [number])\n2. [1-2 sentence description]. (Source: [number])"),
        ("human", "Product details: {product_details}\n\nWeb Search Results:\n{search_results}"),
    ])
    
    citation_chain = citation_prompt | llm | StrOutputParser()
    strategies_with_citations = citation_chain.invoke({
        "product_details": product_details,
        "search_results": formatted_search_results
    })
    
    final_strategies = []
    final_response_lines = []
    pattern = re.compile(r'^\d+\.\s*(.*?)\s*\(\s*Source:\s*\[?(\d+)\]?\s*\)$')

    for line in strategies_with_citations.split('\n'):
        match = pattern.match(line.strip())
        if match:
            strategy_text = match.group(1).strip()
            source_num = int(match.group(2))
            source_url = source_map.get(source_num, "Source not found")
            
            final_strategies.append(strategy_text)
            final_response_lines.append(f"**Strategy {len(final_strategies)}:** {strategy_text}\n*Source: {source_url}*")

    if not final_response_lines:
        return {"messages": [AIMessage(content="I researched some strategies, but had trouble formatting them with specific sources. Please try describing your product again.")]}

    full_response = "Great! Based on my research, here are some strategies for you, with their sources:\n\n" + "\n\n".join(final_response_lines)
    
    return {
        "messages": [AIMessage(content=full_response)],
        "strategies": final_strategies,
    }

def select_strategy(state: AgentState) -> dict:
    """Processes the user's strategy selection."""
    messages = state["messages"]
    
    if messages and isinstance(messages[-1], HumanMessage):
        user_input = messages[-1].content
        match = re.search(r'\b(\d+)\b', user_input)
        if match:
            num = int(match.group(1)) - 1
            strategies = state.get("strategies", [])
            if 0 <= num < len(strategies):
                selected = strategies[num]
                return {"selected_strategy": selected}
        
        invalid_msg = f"That doesn't seem right. Please reply with a single number (e.g., '1', '2') from the list of strategies above."
        return {"messages": [AIMessage(content=invalid_msg)]}

    response = f"Please select a strategy by replying with the number (1 to {len(state.get('strategies', []))})."
    return {"messages": [AIMessage(content=response)]}


def guide_strategy(state: AgentState) -> dict:
    """Provides a detailed guide for the selected strategy."""
    selected = state["selected_strategy"]
    product = state["product_details"]

    query_generation_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert at crafting effective web search queries. Based on the following product and selected marketing strategy, generate a single, concise search query to find a step-by-step guide for implementation. Output ONLY the search query itself, with no extra text or quotation marks."),
        ("human", "Product: {product_details}\n\nStrategy: {strategy}"),
    ])
    query_generation_chain = query_generation_prompt | llm | StrOutputParser()
    search_query = query_generation_chain.invoke({
        "product_details": product,
        "strategy": selected
    })

    st.write(f"🔍 Searching the web for: `{search_query}`")
    search_results_list = web_search_wrapper.results(search_query, max_results=5)
    formatted_search_results = "\n".join([f"Title: {res['title']}\nSnippet: {res['snippet']}" for res in search_results_list])

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a marketing expert. Provide a clear, step-by-step approach to implement the selected strategy, including required documents or resources. Format the output clearly using Markdown. Output EXACTLY in this structure:\n\nGreat choice! Here is your step-by-step guide:\n\n### Steps:\n1. [step1]\n2. [step2]\n...\n\n### Required Documents:\n- [doc1]\n- [doc2]\n..."),
        ("human", "Product: {product}\nStrategy: {strategy}\nSearch: {search_results}"),
    ])
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({"product": product, "strategy": selected, "search_results": formatted_search_results})
    return {"messages": [AIMessage(content=response)], "guided": True}

def check_satisfaction(state: AgentState) -> dict:
    """Checks if the user is satisfied with the guidance."""
    messages = state["messages"]
    
    if messages and isinstance(messages[-1], HumanMessage):
        user_input_lower = messages[-1].content.lower()
        dissatisfaction_keywords = ["not suit", "another", "try different", "no", "change", "doesn't work", "not good"]
        satisfaction_keywords = ["yes", "good", "suits", "perfect", "works", "satisfied"]
        
        if any(kw in user_input_lower for kw in dissatisfaction_keywords):
            reset_msg = "Understood. Please select another strategy from the list I provided earlier."
            return {
                "selected_strategy": None,
                "satisfaction": False,
                "guided": False,
                "messages": [AIMessage(content=reset_msg)]
            }
        elif any(kw in user_input_lower for kw in satisfaction_keywords):
            response = "Excellent! I'm glad that strategy works for you. Good luck with your marketing campaign! This session has now ended."
            return {"messages": [AIMessage(content=response)], "satisfaction": True}
        else:
            return {"messages": [AIMessage(content="I'm not sure I understand. Does this strategy suit you? Please reply with 'yes' or 'no'.")]}

    return {"messages": [AIMessage(content="Does this strategy and guidance suit your needs? Reply 'yes' if satisfied, or 'no' to try another.")]}

# --- Graph Definition ---

def master_router(state: AgentState) -> str:
    """Routes to the correct node based on the current state."""
    if state.get("satisfaction"):
        return END
    if not state.get("product_details"):
        return "gather_product"
    if not state.get("strategies"):
        return "generate_strategies"
    if not state.get("selected_strategy"):
        return "select_strategy"
    if not state.get("guided"):
        return "guide_strategy"
    return "check_satisfaction"

def route_after_selection(state: AgentState) -> str:
    """Conditionally routes to the guide or ends the turn."""
    if state.get("selected_strategy"):
        return "guide_strategy"
    else:
        return END

workflow = StateGraph(AgentState)

workflow.add_node("gather_product", gather_product_details)
workflow.add_node("generate_strategies", generate_strategies)
workflow.add_node("select_strategy", select_strategy)
workflow.add_node("guide_strategy", guide_strategy)
workflow.add_node("check_satisfaction", check_satisfaction)

workflow.set_conditional_entry_point(master_router)

workflow.add_edge("gather_product", END)
workflow.add_edge("generate_strategies", END)

workflow.add_conditional_edges(
    "select_strategy",
    route_after_selection,
    {
        "guide_strategy": "guide_strategy",
        END: END
    }
)

workflow.add_edge("guide_strategy", END)
workflow.add_edge("check_satisfaction", END)

# --- Streamlit UI ---

st.set_page_config(page_title="AI Marketing Agent", page_icon="🤖")
st.title("🤖 AI Marketing Strategy Assistant")

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm your AI Marketing Assistant. To get started, please describe your product, its features, target audience, and your marketing goals."}]
if "checkpointer" not in st.session_state:
    st.session_state.checkpointer = MemorySaver()

# Compile the app with the persistent checkpointer
app = workflow.compile(checkpointer=st.session_state.checkpointer)

# Display chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Get user input
if prompt := st.chat_input("What are your product's details?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare graph input
    config = {"configurable": {"thread_id": st.session_state.session_id}}
    inputs = {"messages": [HumanMessage(content=prompt)]}

    # Stream and display graph responses
    with st.chat_message("assistant"):
        full_response = ""
        placeholder = st.empty()
        
        for chunk in app.stream(inputs, config, recursion_limit=100):
            for node_name, output_value in chunk.items():
                if output_value and "messages" in output_value and output_value["messages"]:
                    content = output_value['messages'][-1].content
                    if content:
                        full_response += content + "\n\n"
                        placeholder.markdown(full_response + "▌")
        
        placeholder.markdown(full_response)
    
    if full_response:
        st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    # Check if the graph has finished
    if not app.get_state(config).next:
        st.stop()