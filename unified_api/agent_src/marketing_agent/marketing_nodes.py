# src/nodes.py
import re
import os
from typing import TypedDict, Annotated, Sequence, Optional

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq

from ..config import GROQ_API_KEY

if GROQ_API_KEY:
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY

# Initialize shared components
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.7)
web_search_wrapper = DuckDuckGoSearchAPIWrapper()

# Define the state (shared with graph.py)
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    product_details: Optional[str]
    strategies: Optional[list[str]]
    selected_strategy: Optional[str]
    satisfaction: bool
    guided: bool
    user_email: Optional[str]
    strategy_guide: Optional[str]
    email_sent: bool
    formatted_strategies: Optional[str]

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
            # Check if we have enough details. At least Features, Target Audience, AND Goals must be known.
            details_map = {}
            for line in product_details_raw.split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    details_map[key.strip()] = val.strip().lower()
            
            missing_fields = [k for k, v in details_map.items() if 'unknown' in v]
            
            # If we have most details (allow Name to be unknown if others are present, but usually name is key)
            # Let's be strict: We need at least 3 fields to be known.
            known_fields_count = sum(1 for v in details_map.values() if 'unknown' not in v)
            
            if known_fields_count >= 3:
                confirmation = f"Understood. Based on your input, here's what I've gathered about your product:\n\n{product_details_raw.strip()}\n\nShall I proceed with generating strategies based on this?"
                return {"product_details": product_details_raw.strip(), "messages": [AIMessage(content=confirmation)]}

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a trendy, energetic marketing genius! 🚀 Your goal is to hype up the user and get the deets on their product. Don't be boring. Ask 3-4 punchy questions to understand their vibe, target audience, and goals. Use emojis and keep it fresh! If the user's previous answer was vague, ask for specific details."),
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
    
    print(f"--- Searching the web for: {search_query} ---")
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
    pattern = re.compile(r'\(Source:\s*\[?(\d+)\]?\)')

    for line in strategies_with_citations.split('\n'):
        line = line.strip()
        if not line: 
            continue
            
        # Check for source citation
        match = pattern.search(line)
        if match:
            source_num = int(match.group(1))
            source_url = source_map.get(source_num, "Source not found")
            
            # Remove the citation from the text to avoid duplication
            strategy_text = pattern.sub('', line).strip()
            # Clean up leading numbers/bullets if present
            strategy_text = re.sub(r'^\d+\.\s*', '', strategy_text)
            
            final_strategies.append(strategy_text)
            final_response_lines.append(f"**Strategy {len(final_strategies)}:** {strategy_text}\n*Source: {source_url}*")
        elif len(line) > 10 and line[0].isdigit(): 
            # Fallback: If it looks like a strategy but missed citation, include it anyway
            strategy_text = re.sub(r'^\d+\.\s*', '', line)
            final_strategies.append(strategy_text)
            final_response_lines.append(f"**Strategy {len(final_strategies)}:** {strategy_text}")

    if not final_response_lines:
        return {"messages": [AIMessage(content="I researched some strategies, but had trouble formatting them with specific sources. Please try describing your product again.")]}

    full_response = "Here are some killer strategies I found for you! 🔥\n\n" + "\n\n".join(final_response_lines) + "\n\nWhich of these strategies resonates with you the most? Reply with the number or name! 👇"
    
    return {
        "messages": [AIMessage(content=full_response)],
        "strategies": final_strategies,
        "formatted_strategies": full_response
    }

def select_strategy(state: AgentState) -> dict:
    """Processes the user's strategy selection using LLM for flexibility."""
    messages = state["messages"]
    strategies = state.get("strategies", [])
    
    if not strategies:
        return {"messages": [AIMessage(content="I don't have any strategies to select from yet. Let's generate some first!")]}

    if messages and isinstance(messages[-1], HumanMessage):
        user_input = messages[-1].content
        
        # Use LLM to match user input to a strategy index
        strategies_list_str = "\n".join([f"{i+1}. {s}" for i, s in enumerate(strategies)])
        
        selection_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful assistant helping a user select a marketing strategy from a list.
            The user might reply with a number (e.g., "1"), a ordinal (e.g., "the first one"), or a description (e.g., "the social media one").
            
            Here are the available strategies:
            {strategies_list}
            
            Based on the user's input: "{user_input}"
            
            Return ONLY the integer index (1-based) of the selected strategy.
            If the user's input is ambiguous or doesn't match any strategy, return '0'.
            Output ONLY the number."""),
        ])
        
        chain = selection_prompt | llm | StrOutputParser()
        result = chain.invoke({
            "strategies_list": strategies_list_str,
            "user_input": user_input
        })
        
        try:
            num = int(result.strip())
            if num > 0 and num <= len(strategies):
                selected = strategies[num - 1]
                return {"selected_strategy": selected}
        except ValueError:
            pass
        
        invalid_msg = f"I'm not sure which strategy you mean. You can simply reply with the number (e.g., '1') or the name of the strategy."
        return {"messages": [AIMessage(content=invalid_msg)]}

    response = f"Which strategy do you like best? You can tell me the number or just say the name! 🏆"
    return {"messages": [AIMessage(content=response)]}

def guide_strategy(state: AgentState) -> dict:
    """Provides a detailed guide for the selected strategy with tool recommendations."""
    selected = state["selected_strategy"]
    product = state["product_details"]

    # 1. Search for implementation guide
    query_generation_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert at crafting effective web search queries. Based on the following product and selected marketing strategy, generate a single, concise search query to find a step-by-step guide for implementation. Output ONLY the search query itself."),
        ("human", "Product: {product_details}\n\nStrategy: {strategy}"),
    ])
    query_chain = query_generation_prompt | llm | StrOutputParser()
    guide_query = query_chain.invoke({"product_details": product, "strategy": selected})

    print(f"--- Searching for guide: {guide_query} ---")
    guide_results = web_search_wrapper.results(guide_query, max_results=3)
    formatted_guide_results = "\n".join([f"Title: {res['title']}\nSnippet: {res['snippet']}" for res in guide_results])

    # 2. Search for tools
    tool_query = f"best software tools for {selected} marketing 2024"
    print(f"--- Searching for tools: {tool_query} ---")
    tool_results = web_search_wrapper.results(tool_query, max_results=3)
    formatted_tool_results = "\n".join([f"Title: {res['title']}\nSnippet: {res['snippet']}" for res in tool_results])

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a marketing expert. Provide a clear, step-by-step approach to implement the selected strategy. ALSO, recommend specific software tools that can help. Format the output clearly using Markdown. Output EXACTLY in this structure:\n\nGreat choice! Here is your step-by-step guide:\n\n### Steps:\n1. [step1]\n2. [step2]\n...\n\n### Recommended Tools 🛠️:\n- **[Tool Name]**: [Brief description]\n- **[Tool Name]**: [Brief description]\n...\n\n### Required Documents:\n- [doc1]\n- [doc2]\n..."),
        ("human", "Product: {product}\nStrategy: {strategy}\nGuide Search: {guide_results}\nTool Search: {tool_results}"),
    ])
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({
        "product": product, 
        "strategy": selected, 
        "guide_results": formatted_guide_results,
        "tool_results": formatted_tool_results
    })
    
    response += "\n\nReady to execute this? Or would you like me to email this guide to you? 📧"
    return {"messages": [AIMessage(content=response)], "guided": True, "strategy_guide": response}

def check_satisfaction(state: AgentState) -> dict:
    """Checks if the user is satisfied, wants to change, or has questions."""
    messages = state["messages"]
    strategy = state.get("selected_strategy")
    guide = state.get("strategy_guide", "")
    
    if messages and isinstance(messages[-1], HumanMessage):
        user_input = messages[-1].content
        
        # Use LLM to classify and respond
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a marketing expert assistant. 
            The user has selected the strategy: '{strategy}'.
            You have provided them with this guide:
            {guide}
            
            Analyze the user's latest input: "{user_input}"
            
            PRIORITY RULES:
            1. If the user mentions 'email', 'mail', 'send', 'send it', or asks to receive the guide/details, output EXACTLY: SATISFIED
            
            2. If the user confirms they are happy, says 'yeah', 'yes', 'good', 'perfect', 'ok', 'sure', 'I like it', 'go ahead', output EXACTLY: SATISFIED
            
            3. If the user dislikes it, says 'no', 'not good', 'change', 'strategies again', 'show strategies', 'change plan', or wants to try a different strategy, output EXACTLY: DISSATISFIED
            
            4. If the user says 'bye', 'goodbye', 'exit', 'quit', 'thanks', or 'thank you' (without asking for email), provide a friendly farewell message (e.g., "Happy marketing! 🚀"). Do NOT output SATISFIED.
            
            5. ONLY if none of the above apply: If the user asks a question, asks for clarification, or makes a general comment, provide a helpful, friendly response to answer them. Keep it concise and direct. Do NOT use phrases like "It seems like..." or "You mentioned...". Just answer the question directly.
            """),
        ])
        
        chain = prompt | llm | StrOutputParser()
        response = chain.invoke({
            "strategy": strategy,
            "guide": guide[:2000], # Truncate guide to avoid context limit if too huge, though 8b should handle it
            "user_input": user_input
        })
        
        cleaned_response = response.strip()
        cleaned_response_upper = cleaned_response.upper()
        
        if "SATISFIED" in cleaned_response_upper:
            return {
                "satisfaction": True,
                "email_sent": False, # Reset to allow sending again if requested
                "messages": [AIMessage(content="Awesome! I'm sending this guide to your email right now! 📧")]
            }
        elif "DISSATISFIED" in cleaned_response_upper:
            # If we have the formatted strategies saved, show them again
            strategies_msg = state.get("formatted_strategies")
            if not strategies_msg:
                # Fallback if not saved (backward compatibility or lost state)
                strategies = state.get("strategies", [])
                if strategies:
                    strategies_list = "\n".join([f"{i+1}. {s}" for i, s in enumerate(strategies)])
                    strategies_msg = f"Here are the strategies again:\n\n{strategies_list}\n\nWhich one would you like to try? 👇"
                else:
                    strategies_msg = "I can't find the previous strategies. Let's start over. Please describe your product again."
                    return {"product_details": None, "strategies": None, "selected_strategy": None, "satisfaction": False, "guided": False, "messages": [AIMessage(content=strategies_msg)]}

            return {
                "selected_strategy": None,
                "satisfaction": False,
                "guided": False,
                "messages": [AIMessage(content=f"No worries! Let's pivot.\n\n{strategies_msg}")]
            }
        else:
            # It's a question or comment, return the LLM's response
            # Also append this new Q&A to the strategy guide so it gets included in the email if requested later
            updated_guide = guide + f"\n\n**User Question:** {user_input}\n\n**Answer:** {cleaned_response}"
            return {
                "messages": [AIMessage(content=cleaned_response)],
                "strategy_guide": updated_guide
            }

    return {"messages": [AIMessage(content="Does this strategy and guide work for you? Reply 'yes' if you're happy, or 'no' to try another.")]}

async def send_email_node(state: AgentState) -> dict:
    """Sends the strategy guide via email."""
    from services.email_service import EmailService
    
    # In a real app, we'd get the user's email from the state or context
    # For now, we'll assume a placeholder or extract from messages if provided
    # But since we have auth, we should ideally pass the user's email in the state
    # For this demo, let's hardcode or ask for it? 
    # Actually, the user is logged in, so we should have their email.
    # But the agent state doesn't have it.
    # Let's assume we can get it from the user's profile if we had access.
    # For now, let's just simulate it or send to a test email if known, 
    # OR we can ask the user for their email in the chat if we don't have it.
    
    # However, to keep it simple and since we are in the backend, 
    # we might not have easy access to the request user here without passing it in.
    # Let's try to extract an email from the conversation or just say we sent it.
    
    # WAIT: The user is logged in. The `main.py` or `app.py` calling this graph 
    # should inject the user's email into the state.
    # Let's update AgentState to include 'user_email'.
    
    user_email = state.get("user_email")
    if not user_email:
        return {"messages": [AIMessage(content="I wanted to email you the guide, but I don't have your email address handy. You can copy the guide above!")]}

    # Use the saved strategy guide from state
    strategy_guide = state.get("strategy_guide")
            
    if not strategy_guide:
        # Fallback to searching messages if not in state (backward compatibility)
        for msg in reversed(state["messages"]):
            if isinstance(msg, AIMessage) and "Great choice!" in msg.content:
                strategy_guide = msg.content
                break
    
    if not strategy_guide:
        strategy_guide = "Here is your marketing strategy guide."

    subject = f"Your Marketing Strategy: {state.get('selected_strategy')}"
    
    # Helper to convert Markdown to HTML
    def markdown_to_html(text):
        # Escape HTML first (optional, but good practice)
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        # Headers
        text = re.sub(r'^### (.*?)$', r'<h3 style="color: #2c3e50; margin-top: 20px; margin-bottom: 10px;">\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.*?)$', r'<h2 style="color: #2c3e50; margin-top: 25px; margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 5px;">\1</h2>', text, flags=re.MULTILINE)
        
        # Bold
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        
        # Italic
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        
        # Lists (Bullet points)
        # We use divs with padding to simulate lists without worrying about closing <ul> tags
        text = re.sub(r'^\s*-\s+(.*?)$', r'<div style="margin-left: 20px; margin-bottom: 5px; color: #34495e;">• \1</div>', text, flags=re.MULTILINE)
        
        # Numbered Lists
        # We just style them nicely
        text = re.sub(r'^\s*(\d+\.)\s+(.*?)$', r'<div style="margin-left: 20px; margin-bottom: 8px; color: #34495e;"><b>\1</b> \2</div>', text, flags=re.MULTILINE)

        # Links
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" style="color: #3498db; text-decoration: none;">\1</a>', text)

        # Paragraphs / Newlines
        # Replace double newlines with paragraph breaks, single with line breaks
        # But we need to be careful not to break the HTML we just added.
        # A simple approach: Replace \n with <br> is usually safe enough for email if we don't have complex block structures.
        text = text.replace('\n', '<br>')
        
        return text

    formatted_body = markdown_to_html(strategy_guide)

    # Convert Markdown to HTML (simple conversion)
    html_body = f"""
    <html>
        <body style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #ffffff;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #2c3e50; margin: 0;">Marketing Strategy Guide</h1>
                    <p style="color: #7f8c8d; font-size: 14px;">Generated by Your AI Marketing Agent</p>
                </div>
                
                <div style="background-color: #f8f9fa; padding: 30px; border-radius: 12px; border: 1px solid #e9ecef;">
                    {formatted_body}
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #95a5a6; font-size: 12px;">
                    <p>Good luck with your campaign! 🚀</p>
                </div>
            </div>
        </body>
    </html>
    """
    
    await EmailService.send_generic_email(user_email, subject, html_body)
    
    confirmation_msg = f"""Sent! 🚀

**Here is the draft I sent to {user_email}:**

---
{strategy_guide}
---

Check your inbox!"""
    
    return {"messages": [AIMessage(content=confirmation_msg)], "email_sent": True}