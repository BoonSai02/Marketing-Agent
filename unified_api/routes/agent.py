from fastapi import APIRouter, HTTPException, Depends, Request
from langchain_core.messages import HumanMessage
from agent_src.models import ChatRequest, ChatResponse
# from agent_src.orchestrator.orchestrator_graph import app as graph_app
from dependencies import get_current_user
import uuid
import logging

router = APIRouter(prefix="/api/agent", tags=["AI Agent"])
logger = logging.getLogger("agent.routes")

from services.auth_service import AuthService

auth_service = AuthService()

@router.get("/sessions")
async def get_sessions(current_user: dict = Depends(get_current_user)):
    """
    Retrieves all chat sessions for the current user.
    """
    return await auth_service.get_user_sessions(current_user["id"])

@router.get("/history")
async def get_chat_history(req: Request, session_id: str = None, current_user: dict = Depends(get_current_user)):
    """
    Retrieves the chat history for a specific session or the last session.
    """
    user_id = current_user["id"]
    
    if session_id:
        target_session_id = session_id
    else:
        target_session_id = await auth_service.get_last_session(user_id)
    
    if not target_session_id:
        return {"messages": [], "session_id": None}
        
    graph_app = req.app.state.graph_app
    config = {"configurable": {"thread_id": target_session_id}}
    
    try:
        state = await graph_app.aget_state(config)
        if not state.values:
             return {"messages": [], "session_id": target_session_id}
             
        messages = state.values.get("messages", [])
        # Convert messages to frontend format
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted_messages.append({"content": msg.content, "isUser": True})
            elif hasattr(msg, "content") and msg.content:
                formatted_messages.append({"content": msg.content, "isUser": False})
                
        return {"messages": formatted_messages, "session_id": target_session_id}
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}")
        return {"messages": [], "session_id": target_session_id}

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, req: Request, current_user: dict = Depends(get_current_user)):
    """
    Endpoint for chat interactions. Provides a session_id if not given, invokes the graph,
    and returns the assistant's response. Sessions are persisted in Redis for continuity.
    """
    # Get graph_app from app state
    graph_app = req.app.state.graph_app

    # Generate or use session_id as thread_id for persistence
    is_new_session = False
    if not request.session_id:
        session_id = uuid.uuid4()
        is_new_session = True
    else:
        session_id = request.session_id
        
    config = {"configurable": {"thread_id": str(session_id)}}
    
    # Create session record if new
    if is_new_session:
        # Use first 50 chars of message as title
        title = request.message[:50] + "..." if len(request.message) > 50 else request.message
        await auth_service.create_session(current_user["id"], str(session_id), title=title)
    
    # Update user's last session
    await auth_service.update_last_session(current_user["id"], str(session_id))

    # Prepare inputs
    # Inject user_email into the state
    inputs = {
        "messages": [HumanMessage(content=request.message)],
        "user_email": current_user.get("email")
    }

    try:
        # Stream the graph output (non-streaming for simplicity; can be adapted for SSE)
        full_response = ""
        async for chunk in graph_app.astream(inputs, config, recursion_limit=100):
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
        final_state = await graph_app.aget_state(config)
        is_complete = bool(final_state.values.get("satisfaction", False)) or not final_state.next
        
        # Extract strategies if available
        strategies = final_state.values.get("strategies")

        return ChatResponse(
            response=full_response.strip(),
            session_id=str(session_id),
            is_complete=is_complete,
            strategies=strategies
        )

    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")
