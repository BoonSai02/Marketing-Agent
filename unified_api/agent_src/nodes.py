# src/nodes.py
import re
import asyncio
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
import logging
from typing import TypedDict, Annotated, Sequence, Optional, List, Dict
from pathlib import Path
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.callbacks.manager import adispatch_custom_event
from langchain_tavily import TavilySearch
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq

from .config import GROQ_API_KEY, TAVILY_API_KEY

# Load env
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# logging.basicConfig(level=logging.INFO)  <-- Removed to avoid conflict with main.py
logger = logging.getLogger("agent.nodes")

# LLM & Tool
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)
tavily_tool = TavilySearch(max_results=7)

# State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Product fields
    product_name: Optional[str]
    product_description: Optional[str]
    target_audience: Optional[str]
    primary_goal: Optional[str]
    budget_range: Optional[str]
    timeline: Optional[str]
    industry: Optional[str]
    unique_selling_proposition: Optional[str]
    current_marketing_channels: Optional[List[str]]
    geography: Optional[str]

    # Flow control
    conversation_phase: Optional[str] # 'greeting', 'readiness', 'gathering', etc.
    asking_more_info: Optional[bool]
    research_queries_used: Optional[List[str]]
    selected_sources: Optional[List[Dict]]
    summary_of_findings: Optional[str]
    strategies: Optional[List[str]]
    selected_strategy: Optional[str]
    guided: Optional[bool]
    satisfaction: Optional[bool]


# ==================== NODES ====================

async def perform_deep_research(state: AgentState) -> dict:
    logger.info("--- Node: perform_deep_research ---")
    
    ctx = f"""Product: {state.get('product_name', '')}
Description: {state.get('product_description', '')}
Industry: {state.get('industry', '')}
Target Audience: {state.get('target_audience', '')}
Primary Goal: {state.get('primary_goal', '')}
USP: {state.get('unique_selling_proposition', '')}
Geography: {state.get('geography', '')}
Budget: {state.get('budget_range', '')}
Timeline: {state.get('timeline', '')}"""

    # Send "searching..." message
    await adispatch_custom_event("progress", {"step": "searching..."})

    # Generate 3 queries
    query_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a world-class marketing researcher. Generate exactly 3 different, powerful search queries to find real, proven marketing strategies for this product.\n"
                   "1. Focus: Industry + Goal + Audience\n"
                   "2. Focus: USP + Product type + Goal\n"
                   "3. Focus: Geography + Budget/Timeline + Trends\n"
                   "Output only the 3 queries, one per line. No numbering, no extra text."),
        ("human", "{ctx}")
    ])

    try:
        query_chain = query_prompt | llm | StrOutputParser()
        raw_queries = await query_chain.ainvoke({"ctx": ctx})
        queries = [q.strip() for q in raw_queries.split("\n") if q.strip()][:3]
        if len(queries) < 3:
            queries = queries + [queries[0]] * (3 - len(queries))  # fallback
    except Exception as e:
        logger.error(f"Query generation failed: {e}")
        queries = [
            f"{state.get('industry', 'marketing')} strategies for {state.get('product_name', 'product')}",
            f"how to market {state.get('unique_selling_proposition', 'innovative')} products",
            f"best marketing campaigns {state.get('geography', '')} 2025"
        ]

    logger.info(f"Research queries: {queries}")

    all_results = []
    seen_urls = set()

    for query in queries:
        await adispatch_custom_event("progress", {"step": f"Searching: {query[:70]}..."})
        try:
            results = tavily_tool.invoke({"query": query})
            if isinstance(results, dict):
                results = results.get("results", [results])
            
            for item in results:
                url = item.get("url")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append({
                        "title": item.get("title", "No title"),
                        "url": url,
                        "snippet": item.get("content", "")[:1000]
                    })
        except Exception as e:
            logger.error(f"Tavily failed on '{query}': {e}")

    # Let LLM pick the best 5–7 authoritative sources
    results_text = "\n".join([f"{i+1}. {r['title']} — {r['url']}" for i, r in enumerate(all_results[:20])])

    select_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a strict curator. From the search results below, select ONLY the 5–7 most authoritative, relevant, and high-quality sources for marketing strategies.\n"
                   "Prioritize: HubSpot, Neil Patel, Backlinko, GrowthHackers, HBR, WordStream, etc.\n"
                   "Avoid: Reddit, Quora, YouTube, listicles, low-quality blogs.\n\n"
                   "Output valid JSON exactly like this:\n"
                   "{{\n"
                   "  \"selected_sources\": [\n"
                   "    {{\"rank\": 1, \"title\": \"...\", \"url\": \"...\", \"domain\": \"...\", \"why_relevant\": \"...\"}}\n"
                   "  ],\n"
                   "  \"summary_of_findings\": \"2–3 sentence insight about the marketing landscape\"\n"
                   "}}"),
        ("human", "Product context:\n{ctx}\n\nSearch results:\n{results_text}")
    ])

    try:
        chain = select_prompt | llm | JsonOutputParser()
        selection = await chain.ainvoke({"ctx": ctx, "results_text": results_text or "No results"})

        sources = selection.get("selected_sources", [])[:7]
        for s in sources:
            url = s.get("url", "")
            s["domain"] = url.split("/")[2].replace("www.", "") if url else "unknown"

        summary = selection.get("summary_of_findings", "Research completed successfully.")

    except Exception as e:
        logger.error(f"Source selection failed: {e}")
        sources = [{"rank": i+1, "title": r["title"], "url": r["url"], "domain": "fallback", "why_relevant": "Selected during fallback"} 
                  for i, r in enumerate(all_results[:5])]
        summary = "Solid strategies found (fallback mode)."

    await adispatch_custom_event("progress", {"step": f"Curated {len(sources)} premium sources!"})

    return {
        "research_queries_used": queries,
        "selected_sources": sources,
        "summary_of_findings": summary
    }

async def write_report(state: AgentState) -> dict:
    logger.info("--- Node: write_report ---")
    sources = state.get("selected_sources", [])
    summary = state.get("summary_of_findings", "")
    
    ctx = f"Product: {state.get('product_name', 'Unknown')}\nDescription: {state.get('product_description', 'Unknown')}\nGoal: {state.get('primary_goal', 'Unknown')}"

    sources_str = "\n".join([f"{i+1}. [{s['title']}]({s['url']})" for i, s in enumerate(sources)])

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are Emily, a warm expert marketer. Write a beautiful report with exactly 5 unique strategies. "
                   "Each: **Approach X: Name**\nExplanation in simple language\n*Reference: [Title](URL)*\n\n"
                   "End with a motivating conclusion."),
        ("human", "Context:\n{ctx}\nSummary: {summary}\nSources:\n{sources_str}")
    ])
    
    report = await (prompt | llm | StrOutputParser()).ainvoke({"ctx": ctx, "summary": summary, "sources_str": sources_str})

    # Extract strategy titles for selection
    extract = ChatPromptTemplate.from_messages([
        ("system", "Extract exactly 5 strategy names as a numbered list."),
        ("human", report)
    ])
    strategies = [s.strip()[s.strip().find(" "):].strip() for s in (await (extract | llm | StrOutputParser()).ainvoke({})).split("\n") if s.strip() and any(c.isdigit() for c in s)]

    report += "\n\n**References**\n" + "\n".join([f"- [{s['title']}]({s['url']})" for s in sources])

    await adispatch_custom_event("progress", {"step": "Report ready!"})
    
    return {
        "messages": [AIMessage(content=report)],
        "strategies": strategies[:5]
    }


def gather_product_details(state: AgentState) -> dict:
    return {"messages": [AIMessage(content="Hey! I'm Emily, your marketing strategist 🤖✨\n\nWhat product are you launching? Tell me the name and what it does — I'm super excited to help you crush it!")]}


def process_more_info(state: AgentState) -> dict:
    user_msg = state["messages"][-1].content.lower()
    if any(x in user_msg for x in ["no", "nope", "that's all", "enough", "proceed", "go ahead"]):
        return {
            "asking_more_info": False,
            # "messages": [AIMessage(content="Awesome! Researching the best strategies for you right now... hold tight! 🔍")]
        }
    else:
        return {"messages": [AIMessage(content="Got it! Anything else you'd like to add? (Or just say 'no' to continue)")]}


def select_strategy(state: AgentState) -> dict:
    count = len(state.get("strategies", []))
    msg = f"I found **{count} powerful marketing strategies** for **{state['product_name']}**!\n\n" \
          "Which one excites you most? Just reply with the number (1–5) or ask me anything!\n\n" \
          "Here they are again for easy picking:"
    return {"messages": [AIMessage(content=msg)]}


async def guide_strategy(state: AgentState) -> dict:
    strategy = state["selected_strategy"]
    product = state["product_name"]

    # Send searching message
    await adispatch_custom_event("progress", {"step": "searching about the details of that marketing strategy..."})

    search_q = await (ChatPromptTemplate.from_messages([
        ("system", "Create one perfect search query for a step-by-step guide on this strategy. Output ONLY the query."),
        ("human", "Product: {product}\nStrategy: {strategy}")
    ]) | llm | StrOutputParser()).ainvoke({"product": product, "strategy": strategy})

    results = tavily_tool.invoke({"query": search_q})
    if isinstance(results, dict):
        results = results.get("results", [results])
        
    context = "\n".join([f"{r['title']}: {r['content'][:500]}" for r in results[:4]])

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Write a clear, friendly step-by-step guide with required documents. Use Markdown."),
        ("human", "Product: {product}\nStrategy: {strategy}\nResearch: {context}")
    ])
    guide = await (prompt | llm | StrOutputParser()).ainvoke({"product": product, "strategy": strategy, "context": context})

    return {
        "messages": [AIMessage(content=guide)],
        "guided": True
    }


def check_satisfaction(state: AgentState) -> dict:
    return {"messages": [AIMessage(content="Good to hear that! Is there anything else I can help you with?\n<BUTTONS>Yes,No</BUTTONS>")]}


def reset_and_gather(state: AgentState) -> dict:
    return {
        "product_name": None, "product_description": None, "target_audience": None, "primary_goal": None,
        "budget_range": None, "timeline": None, "industry": None, "unique_selling_proposition": None,
        "current_marketing_channels": None, "geography": None,
        "research_queries_used": None, "selected_sources": None, "summary_of_findings": None,
        "strategies": None, "selected_strategy": None, "guided": None, "satisfaction": None,
        "asking_more_info": False,
        "conversation_phase": "gathering",
        "messages": state["messages"] + [AIMessage(content="Totally cool! Starting fresh — tell me about your new product! 🚀\n\n<SHOW_PRODUCT_FORM>")]
    }


async def correct_product_details(state: AgentState) -> dict:
    conv = "\n".join([f"{m.type}: {m.content}" for m in state["messages"][-15:]])
    
    try:
        new_data = await (ChatPromptTemplate.from_messages([
            ("system", "User is correcting product details. Re-extract ALL fields from latest messages. Output JSON."),
            ("human", conv)
        ]) | llm | JsonOutputParser()).ainvoke({})
        
        channels = new_data.get("current_marketing_channels", [])
        if isinstance(channels, str):
            channels = [c.strip() for c in channels.split(",") if c.strip()]

        return {
            **new_data,
            "current_marketing_channels": channels,
            "research_queries_used": None,
            "strategies": None,
            "selected_strategy": None,
            "guided": None,
            "messages": state["messages"] + [AIMessage(content="Thanks for the update! Researching fresh strategies with the new info... 🔄")]
        }
    except:
        return {"messages": state["messages"] + [AIMessage(content="Got the changes! Updating everything now...")]}

async def extract_initial_product(state: AgentState) -> dict:
    conv = "\n".join([f"{m.type}: {m.content}" for m in state["messages"]])

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Extract product details from the conversation — be extremely forgiving.
Even if user says "heyy" or "I have a product", extract what you can.
Output ONLY VALID JSON (no markdown formatting, no ```json wrappers).
Keys (use null if missing):

{
  "product_name": str or null,
  "product_description": str or null,
  "target_audience": str or null,
  "primary_goal": str or null,
  "budget_range": str or null,
  "timeline": str or null,
  "industry": str or null,
  "unique_selling_proposition": str or null,
  "current_marketing_channels": list or null,
  "geography": str or null
}"""),
        ("human", "{conv}")
    ])

    try:
        result = await (prompt | llm | JsonOutputParser()).ainvoke({"conv": conv})
        
        channels = result.get("current_marketing_channels")
        if isinstance(channels, str):
            channels = [c.strip() for c in channels.split(",") if c.strip()]
        elif not channels:
            channels = []

        return {
            "product_name": result.get("product_name") or "Your Product",
            "product_description": result.get("product_description") or "A cool product you're building",
            "target_audience": result.get("target_audience"),
            "primary_goal": result.get("primary_goal"),
            "budget_range": result.get("budget_range"),
            "timeline": result.get("timeline"),
            "industry": result.get("industry"),
            "unique_selling_proposition": result.get("unique_selling_proposition"),
            "current_marketing_channels": channels,
            "geography": result.get("geography"),
            # "messages": state["messages"] + [AIMessage(content="Got it! This sounds awesome 🔥\n\nWant to add more details (budget, timeline, etc.)? Or shall I jump straight into finding the best marketing strategies for you?")]
        }
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return {
            "product_name": "Your Product",
            "product_description": "Something cool you're working on",
            "asking_more_info": False,
            # "messages": state["messages"] + [AIMessage(content="Love the vibe! Even if I didn’t catch everything perfectly — I'm ready to help.\n\nWant to add more details or should we dive into strategies?")]
        }


async def manager_node(state: AgentState) -> dict:
    """
    The brain of the agent. Acts like Grok:
    - Answers ANY question instantly and naturally
    - Never says "I can't" or "I'm not allowed"
    - Always brings it back to helping with marketing
    - Detects resets, corrections, strategy changes automatically
    """
    messages = state["messages"]
    if not messages:
        return {}

    # Safety: If last message is AI, stop (don't process own output)
    if isinstance(messages[-1], AIMessage):
        return {}

    user_msg = messages[-1].content
    user_lower = user_msg.lower()
    
    # Current phase
    phase = state.get("conversation_phase", "greeting")

    # ── 1. FULL RESET DETECTION ───────────────────────────────
    # ── 1. FULL RESET DETECTION ───────────────────────────────
    reset_patterns = [
        r"start over", r"restart", r"new product", r"different product",
        r"forget everything", r"begin again", r"new idea", r"wrong product",
        r"change.*product", r"changing.*product", r"reset",
        r"chang.*product" # Catch typos like "chainging"
    ]
    if any(re.search(p, user_lower) for p in reset_patterns):
        return reset_and_gather(state)

    # ── 2. PRODUCT CORRECTION / UPDATE ────────────────────────
    correction_phrases = [
        "actually the product", "wait no", "it's actually", "no it's",
        "budget is now", "target audience is", "it's for", "we're in",
        "changed my mind", "actually we target", "usp is", "industry is"
    ]
    if any(p in user_lower for p in correction_phrases):
        return await correct_product_details(state)

    # ── 3. STRATEGY CHANGE (after guide was given) ─────────────
    if state.get("guided") and state.get("selected_strategy"):
        change_phrases = ["another one", "different strategy", "try number", "what about #", "instead", "not that one", "show me another"]
        if any(p in user_lower for p in change_phrases) or re.search(r"\b(number|#)\s*\d+", user_msg):
            return {
                "selected_strategy": None,
                "guided": None,
                "messages": messages + [AIMessage(content="No problem at all! Which strategy would you like to explore instead? Just say the number or describe what you're feeling!")]
            }

    # ── 4. STRATEGY SELECTION (Initial) ───────────────────────
    if state.get("strategies") and not state.get("selected_strategy"):
        # Check for number 1-5
        match = re.search(r"\b([1-5])\b", user_msg)
        if match:
            idx = int(match.group(1)) - 1
            if 0 <= idx < len(state["strategies"]):
                return {"selected_strategy": state["strategies"][idx]}

    # ── 1.5 START MARKETING INTENT DETECTION ──────────────────
    start_patterns = [
        r"market a product", r"launch a product", r"start marketing",
        r"create a strategy", r"need a strategy", r"help me market",
        r"marketing strategy", r"go to form", r"fill form"
    ]
    if any(re.search(p, user_lower) for p in start_patterns):
        return {
            "conversation_phase": "gathering",
            "messages": messages + [AIMessage(content="Awesome! Let's get down to business. Fill in the details below so I can build your strategy:\n\n<SHOW_PRODUCT_FORM>")]
        }

    # ── 4. NEW FLOW LOGIC ─────────────────────────────────────
    
    # Handle "Hi" / Greeting -> Ask Readiness
    if phase == "greeting" and any(w in user_lower for w in ["hi", "hello", "hey", "greetings", "start"]):
        return {
            "conversation_phase": "readiness",
            "messages": messages + [AIMessage(content="Welcome! Good to see you here! I'm your helpful assistant who gives marketing strategies. Are you ready with your product details?\n<BUTTONS>Yes,No</BUTTONS>")]
        }

    # Handle Readiness Response
    if phase == "readiness":
        affirmative = ["yes", "yeah", "yep", "sure", "ok", "okay", "certainly", "definitely", "absolutely"]
        if any(w in user_lower for w in affirmative):
            # User is ready -> Trigger form
            return {
                "conversation_phase": "gathering",
                "messages": messages + [AIMessage(content="Great! Please fill your details:\n\n<SHOW_PRODUCT_FORM>")]
            }
        elif "no" in user_lower:
            # User is not ready -> Ask about other topics
            return {
                "conversation_phase": "exploring",
                "messages": messages + [AIMessage(content="Okay! Would you like to know about something related to #product or #marketing approach?\n<BUTTONS>Yes,No</BUTTONS>")]
            }

    # Handle "Exploring" Response
    if phase == "exploring":
        if "yes" in user_lower:
             return {
                 "conversation_phase": "general_chat",
                 "messages": messages + [AIMessage(content="Sure! What would you like to know? Ask me anything about marketing or product strategy.")]
             }
        elif "no" in user_lower:
             return {
                 "conversation_phase": "readiness",
                 "messages": messages + [AIMessage(content="Alright! Let me know when you're ready to start. Just say 'Hi' or 'Ready'.")]
             }

    # ── 4.5 TRANSITION TO RESEARCH ─────────────────────────────
    # If we have product details and haven't researched yet -> GO IMMEDIATELY
    if state.get("product_name") and not state.get("research_queries_used"):
        return {}

    # ── 5. USER IS JUST CHATTING / ASKING ANY QUESTION ───────
    # This is the GROK magic: answer everything, then gently refocus
    if not state.get("product_name") and phase not in ["readiness", "exploring", "general_chat"]:
        # First message ever (if not caught by greeting) -> extract product
        return await extract_initial_product(state)

    # If we have product data → always answer any question with personality
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are Emily — a brilliant, witty, no-BS marketing strategist (think Grok + top-tier growth marketer).

Rules:
- Answer ANY question directly, honestly, and with personality
- Never be robotic or say "as an AI I can't"
- Always be helpful, fun, and human
- After answering, gently bring it back to the marketing mission when it makes sense
- If user is stuck or confused → help them move forward
- Keep tone: warm, confident, slightly playful
- If the user asks about a specific strategy, explain it.

Current product context (use only if relevant):
Product: {product_name}
Goal: {primary_goal}
Audience: {target_audience}
Budget: {budget_range}
USP: {unique_selling_proposition}"""),
        ("placeholder", "{history}"),
        ("human", "{user_msg}")
    ])

    chain = prompt | llm | StrOutputParser()

    try:
        # full_history = "\n".join([f"{m.type}: {m.content}" for m in messages[-10:]])  # last 10 for context
        response = await chain.ainvoke({
            "history": messages[-10:],
            "user_msg": user_msg,
            "product_name": state.get("product_name", "your product"),
            "primary_goal": state.get("primary_goal", "growth"),
            "target_audience": state.get("target_audience", "your audience"),
            "budget_range": state.get("budget_range", "your budget"),
            "unique_selling_proposition": state.get("unique_selling_proposition", "what makes it special")
        })
    except Exception as e:
        logger.error(f"Manager response failed: {e}")
        response = "Haha, you got me for a sec! Anyway — what’s on your mind about your product?"

    # Always return as AI message — keeps flow alive
    return {
        "messages": messages + [AIMessage(content=response)]
    }