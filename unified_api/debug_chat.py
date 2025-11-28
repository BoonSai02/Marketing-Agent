import os
import sys
from langchain_core.messages import HumanMessage, AIMessage

# Add the parent directory to sys.path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent_src.graph import app as graph_app
from agent_src.nodes import AgentState

import asyncio

async def run_chat():
    print("--- Starting Debug Chat (Structured Input) ---")
    
    config = {"configurable": {"thread_id": "debug_session_form"}}
    
    # 1. Initial Greeting -> Expect Form
    print("\n[User]: Hi")
    inputs = {"messages": [HumanMessage(content="Hi")]}
    async for chunk in graph_app.astream(inputs, config):
        for node, val in chunk.items():
            print(f"Node: {node}")
            if val and "messages" in val:
                print(f"[Bot]: {val['messages'][-1].content}")

    # 2. Fill out the form
    form_response = (
        "Name of the product: SuperWidget\n"
        "Category: Tech Gadget\n"
        "Usage: Daily productivity\n"
        "Target Audience: Remote workers\n"
        "Key Features: AI-powered, long battery\n"
        "Goals: Increase sales by 20%"
    )
    print(f"\n[User]: {form_response}")
    inputs = {"messages": [HumanMessage(content=form_response)]}
    async for chunk in graph_app.astream(inputs, config):
        for node, val in chunk.items():
            print(f"Node: {node}")
            if val and "messages" in val:
                print(f"[Bot]: {val['messages'][-1].content}")

    # 3. Ask for more info -> User says No
    print("\n[User]: No")
    inputs = {"messages": [HumanMessage(content="No")]}
    async for chunk in graph_app.astream(inputs, config):
        for node, val in chunk.items():
            print(f"Node: {node}")
            if val and "messages" in val:
                print(f"[Bot]: {val['messages'][-1].content}")

    # 4. Select Strategy (Note: The report will likely output a list, so we simulate selecting '1')
    print("\n[User]: 1")
    inputs = {"messages": [HumanMessage(content="1")]}
    async for chunk in graph_app.astream(inputs, config):
        for node, val in chunk.items():
            print(f"Node: {node}")
            if val and "messages" in val:
                print(f"[Bot]: {val['messages'][-1].content}")

    # 5. Satisfied
    print("\n[User]: Yes, I am satisfied")
    inputs = {"messages": [HumanMessage(content="Yes, I am satisfied")]}
    async for chunk in graph_app.astream(inputs, config):
        for node, val in chunk.items():
            print(f"Node: {node}")
            if val and "messages" in val:
                print(f"[Bot]: {val['messages'][-1].content}")

if __name__ == "__main__":
    asyncio.run(run_chat())
