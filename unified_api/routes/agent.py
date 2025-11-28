from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from agent_src.models import ChatRequest, ChatResponse
from agent_src.graph import app as graph_app
import uuid
import logging
import json

router = APIRouter(prefix="/api/agent", tags=["AI Agent"])
logger = logging.getLogger("agent.routes")

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint to interact with the marketing agent.
    """
    session_id = request.session_id or str(uuid.uuid4())
    logger.info(f"Starting chat session: {session_id}")

    config = {"configurable": {"thread_id": session_id}}
    
    # Create a generator to stream the response
    async def event_generator():
        try:
            inputs = {"messages": [HumanMessage(content=request.message)]}
            
            # Stream events for granular progress
            async for event in graph_app.astream_events(inputs, config, version="v1"):
                kind = event["event"]
                
                # Log tool calls (Search)
                if kind == "on_tool_start":
                    tool_name = event["name"]
                    if tool_name == "duckduckgo_search":
                        query = event["data"].get("input", {}).get("query", "something")
                        yield json.dumps({
                            "session_id": str(session_id),
                            "type": "progress",
                            "content": f"Searching for: {query}"
                        }) + "\n"
                
                # Log Custom Events (Deep Research Steps)
                elif kind == "on_custom_event":
                    event_name = event["name"]
                    if event_name == "progress":
                        data = event["data"]
                        step = data.get("step", "Processing...")
                        yield json.dumps({
                            "session_id": str(session_id),
                            "type": "progress",
                            "content": step
                        }) + "\n"

                # Log node output (Chat response)
                elif kind == "on_chain_end":
                    # We look for the final node output
                    data = event["data"].get("output")
                    if data and isinstance(data, dict) and "messages" in data and data["messages"]:
                        last_message = data["messages"][-1]
                        content = last_message.content
                        node_name = event["name"]
                        
                        # Only yield if it's a significant node
                        if node_name in ["manager", "gather_product", "process_more_info", "perform_deep_research", "write_report", "select_strategy", "guide_strategy", "check_satisfaction"]:
                            yield json.dumps({
                                "session_id": str(session_id),
                                "response": content,
                                "node": node_name
                            }) + "\n"
                        
        except Exception as e:
            logger.error(f"Error in chat session {session_id}: {e}", exc_info=True)
            yield json.dumps({
                "session_id": str(session_id),
                "response": "I encountered an error. Please try again.",
                "error": str(e)
            }) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")
