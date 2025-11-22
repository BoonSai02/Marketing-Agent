from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage
from agent_src.models import ChatRequest, ChatResponse
from agent_src.graph import app as graph_app
import uuid
import logging

router = APIRouter(prefix="/api/agent", tags=["AI Agent"])
logger = logging.getLogger("agent.routes")

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint for chat interactions. Provides a session_id if not given, invokes the graph,
    and returns the assistant's response. Sessions are persisted in Redis for continuity.
    """
    # Generate or use session_id as thread_id for persistence
    session_id = request.session_id or uuid.uuid4()
    config = {"configurable": {"thread_id": str(session_id)}}

    # Prepare inputs
    inputs = {"messages": [HumanMessage(content=request.message)]}

    try:
        # Stream the graph output (non-streaming for simplicity; can be adapted for SSE)
        full_response = ""
        for chunk in graph_app.stream(inputs, config, recursion_limit=100):
            for node_name, output_value in chunk.items():
                if output_value and "messages" in output_value and output_value["messages"]:
                    content = output_value['messages'][-1].content
                    if content:
                        full_response += content + "\n\n"

        if not full_response:
            # It's possible the graph didn't generate new tokens if it was just a state update or similar,
            # but usually it should return something.
            # If it's empty, we might want to check the state or just return empty.
            # For now, let's assume it's an error if completely empty, or maybe just return empty string.
            pass 

        # Check if session is complete (e.g., satisfaction=True or no next steps)
        final_state = graph_app.get_state(config)
        is_complete = bool(final_state.values.get("satisfaction", False)) or not final_state.next

        return ChatResponse(
            response=full_response.strip(),
            session_id=session_id,
            is_complete=is_complete
        )

    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")
