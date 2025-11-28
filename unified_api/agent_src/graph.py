# src/graph.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .nodes import (
    AgentState,
    manager_node,
    gather_product_details,
    process_more_info,
    perform_deep_research,
    write_report,
    select_strategy,
    guide_strategy,
    check_satisfaction,
    reset_and_gather,
    correct_product_details,
)
from .config import USE_REDIS, redis_client

# Checkpointer
if USE_REDIS and redis_client:
    from langgraph.checkpoint.redis import RedisSaver
    checkpointer = RedisSaver(redis_client=redis_client)
else:
    checkpointer = MemorySaver()


# ──────────────────────────────
# FINAL & BULLETPROOF GRAPH
# ──────────────────────────────
workflow = StateGraph(AgentState)

# === NODES ===
workflow.add_node("manager", manager_node)
workflow.add_node("gather_product", gather_product_details)
workflow.add_node("process_more_info", process_more_info)
workflow.add_node("perform_deep_research", perform_deep_research)
workflow.add_node("write_report", write_report)
workflow.add_node("select_strategy", select_strategy)
workflow.add_node("guide_strategy", guide_strategy)
workflow.add_node("check_satisfaction", check_satisfaction)
workflow.add_node("reset_and_gather", reset_and_gather)
workflow.add_node("correct_product_details", correct_product_details)

# === ENTRY POINT ===
workflow.set_entry_point("manager")

# === MAIN ROUTING FROM MANAGER (smart & safe) ===
def route_from_manager(state: AgentState) -> str:
    # If manager already responded with a message → END turn (user speaks next)
    if state["messages"] and state["messages"][-1].type == "ai":
        return END

    msg = state["messages"][-1].content.lower() if state["messages"] else ""

    # Reset / Correction (handled inside manager_node now, but keep for safety)
    if any(p in msg for p in ["start over", "restart", "new product", "forget everything"]):
        return "reset_and_gather"
    if any(p in msg for p in ["actually the product", "it's actually", "wait no", "budget is now", "target is"]):
        return "correct_product_details"

    # Normal flow
    if state.get("satisfaction"):
        return "check_satisfaction"
    if state.get("asking_more_info"):
        return "process_more_info"
    if not state.get("product_name") or not state.get("product_description"):
        return "gather_product"
    if not state.get("research_queries_used"):
        return "perform_deep_research"
    if not state.get("strategies"):
        return "write_report"
    if not state.get("selected_strategy"):
        return "select_strategy"
    if not state.get("guided"):
        return "guide_strategy"
    return "check_satisfaction"


workflow.add_conditional_edges(
    "manager",
    route_from_manager,
    {
        "gather_product": "gather_product",
        "process_more_info": "process_more_info",
        "perform_deep_research": "perform_deep_research",
        "write_report": "write_report",
        "select_strategy": "select_strategy",
        "guide_strategy": "guide_strategy",
        "check_satisfaction": "check_satisfaction",
        "reset_and_gather": "reset_and_gather",
        "correct_product_details": "correct_product_details",
        END: END,  # ← This is the KEY: manager can END the turn
    }
)

# === LINEAR FLOW EDGES ===
workflow.add_edge("gather_product", "manager")
workflow.add_edge("process_more_info", "manager")
workflow.add_edge("perform_deep_research", "write_report")
workflow.add_edge("write_report", "manager")           # ← shows report → back to manager
workflow.add_edge("select_strategy", "manager")        # ← asks for number → back to manager
workflow.add_edge("guide_strategy", "check_satisfaction")
workflow.add_edge("reset_and_gather", "manager")
workflow.add_edge("correct_product_details", "manager")

# === SATISFACTION LOOP ===
workflow.add_conditional_edges(
    "check_satisfaction",
    lambda state: END if state.get("satisfaction") else "perform_deep_research",
    {
        END: END,
        "perform_deep_research": "perform_deep_research"
    }
)

# === COMPILE ===
app = workflow.compile(checkpointer=checkpointer)

# Optional: visualize
if __name__ == "__main__":
    try:
        png = app.get_graph().draw_mermaid_png()
        with open("workflow_graph.png", "wb") as f:
            f.write(png)
        print("Graph saved as workflow_graph.png")
    except Exception as e:
        print("Could not generate graph:", e)