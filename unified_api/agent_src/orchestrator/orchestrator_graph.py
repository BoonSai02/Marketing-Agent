from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import sqlite3
from ..config import USE_REDIS, redis_client

from .orchestrator_nodes import OrchestratorState, router_node, general_chat_node
from ..marketing_agent.marketing_graph import workflow as marketing_workflow

# Compile marketing subgraph
marketing_app = marketing_workflow.compile()

async def call_marketing_agent(state: OrchestratorState) -> dict:
    """
    Invokes the marketing agent subgraph.
    We pass the full state to it and get back the result.
    """
    # Invoke the subgraph with the full state
    # The marketing agent's AgentState is compatible with OrchestratorState (superset)
    print(f"--- Orchestrator calling Marketing Agent with state keys: {list(state.keys())} ---")
    result = await marketing_app.ainvoke(state)
    print(f"--- Marketing Agent returned keys: {list(result.keys())} ---")
    if "product_details" in result:
        print(f"--- product_details: {result['product_details']} ---")
    
    # Return the full result to update the Orchestrator's state
    # This ensures product_details, strategies, etc. are persisted
    return result

# Build the Orchestrator Graph
workflow = StateGraph(OrchestratorState)

workflow.add_node("router", router_node)
workflow.add_node("general_chat", general_chat_node)
workflow.add_node("marketing_agent", call_marketing_agent)

workflow.set_entry_point("router")

def route_logic(state: OrchestratorState) -> str:
    return state["next_agent"]

workflow.add_conditional_edges(
    "router",
    route_logic,
    {
        "marketing_agent": "marketing_agent",
        "general_chat": "general_chat",
        "END": END
    }
)

workflow.add_edge("general_chat", END)
workflow.add_edge("marketing_agent", END)

workflow.add_edge("general_chat", END)
workflow.add_edge("marketing_agent", END)

def compile_workflow(checkpointer=None):
    return workflow.compile(checkpointer=checkpointer)
