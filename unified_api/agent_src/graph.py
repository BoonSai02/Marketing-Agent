# src/graph.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .nodes import (
    AgentState,
    gather_product_details,
    generate_strategies,
    select_strategy,
    guide_strategy,
    check_satisfaction,
)
from .config import USE_REDIS, redis_client

# Use RedisSaver if configured and available, otherwise fall back to MemorySaver
if USE_REDIS and redis_client:
    from langgraph.checkpoint.redis import RedisSaver
    checkpointer = RedisSaver(redis_client=redis_client)
else:
    checkpointer = MemorySaver()

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

# Build the workflow graph
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

# Compile the graph with the selected checkpointer
app = workflow.compile(checkpointer=checkpointer)

if __name__ == '__main__':
    # To generate and save the graph as a PNG file
    png_data = app.get_graph().draw_mermaid_png()
    with open("workflow_graph.png", "wb") as f:
        f.write(png_data)
    print("Graph saved as workflow_graph.png")

    # To display in an IPython environment (like a Jupyter notebook), you would use:
    # from IPython.display import display, Image
    # display(Image(png_data))
