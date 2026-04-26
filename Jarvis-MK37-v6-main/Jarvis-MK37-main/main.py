
import asyncio
import logging
import httpx
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager

from agent.dev_agent import DeveloperAgent
from core.llm_manager import LLMManager
from core.db_manager import DatabaseManager # To be created
from ui import JarvisUI # Assuming a UI manager that can handle WebSocket

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
NODE_ID = os.environ.get("JARVIS_NODE_ID", "NODE_1")
FAILOVER_NODE_IP = os.environ.get("FAILOVER_NODE_IP")
HEARTBEAT_INTERVAL = 60

# --- Global Instances ---
# The lifespan manager ensures these are initialized on startup and closed on shutdown
app_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Logic ---
    logging.info("SYS: Initializing Jarvis Core...")
    db_manager = DatabaseManager()
    await db_manager.connect()
    
    ui_manager = JarvisUI() # This will now manage WebSocket connections
    llm_manager = LLMManager(ui=ui_manager)
    dev_agent = DeveloperAgent(project_root=".", llm_manager=llm_manager, db_manager=db_manager, ui=ui_manager)

    app_state.update({
        "db": db_manager,
        "ui": ui_manager,
        "agent": dev_agent,
    })

    # Mission 1: Recovery Logic
    logging.info("SYS: Checking for unfinished tasks...")
    unfinished_tasks = await db_manager.get_unfinished_tasks()
    if unfinished_tasks:
        logging.info(f"SYS: Found {len(unfinished_tasks)} unfinished tasks. Resuming...")
        # For now, we just log them. A full implementation would re-spawn agent tasks.
        for task in unfinished_tasks:
            logging.info(f"  - Resuming task {task['id']}: {task['goal']}")
            # asyncio.create_task(dev_agent.resume_task(task))
    
    # Start background tasks
    if NODE_ID == "NODE_1":
        logging.info("SYS: Node 1 configured as Primary Orchestrator.")
        app_state["autonomous_loop_task"] = asyncio.create_task(dev_agent.autonomous_loop())
    elif NODE_ID == "NODE_2" and FAILOVER_NODE_IP:
        logging.info(f"SYS: Node 2 configured as Failover Monitor for {FAILOVER_NODE_IP}.")
        app_state["heartbeat_task"] = asyncio.create_task(heartbeat_monitor(FAILOVER_NODE_IP, app_state))

    yield

    # --- Shutdown Logic ---
    logging.info("SYS: Shutting down Jarvis Core...")
    if "autonomous_loop_task" in app_state and not app_state["autonomous_loop_task"].done():
        app_state["autonomous_loop_task"].cancel()
    if "heartbeat_task" in app_state and not app_state["heartbeat_task"].done():
        app_state["heartbeat_task"].cancel()
    
    await app_state["db"].disconnect()
    logging.info("SYS: Shutdown complete.")


app = FastAPI(lifespan=lifespan)


# --- API Endpoints ---
@app.get("/health")
async def health_check():
    """Endpoint for heartbeat monitoring."""
    return {"status": "online", "node_id": NODE_ID}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint for the Next.js HUD to receive real-time updates."""
    ui_manager = app_state["ui"]
    await ui_manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive, listening for any client-side messages if needed
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ui_manager.disconnect(websocket)
        logging.info("UI: HUD disconnected.")


# --- Background Tasks ---
async def heartbeat_monitor(primary_node_ip: str, state: dict):
    """Monitors the health of the primary orchestrator."""
    async with httpx.AsyncClient() as client:
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            try:
                response = await client.get(f"http://{primary_node_ip}:8000/health")
                response.raise_for_status()
                logging.info(f"SYS: Heartbeat check passed. Node 1 ({primary_node_ip}) is online.")
            except (httpx.ConnectError, httpx.HTTPStatusError) as e:
                logging.error(f"SYS: HEARTBEAT FAILED. Node 1 is unresponsive. Error: {e}")
                await enter_safe_state(state)
                break

async def enter_safe_state(state: dict):
    """Halts all autonomous operations and logs the incident."""
    message = "Warning: The primary orchestrator is offline. Entering a safe, dormant state."
    logging.warning(f"SYS: {message}")
    await state["ui"].broadcast(f"SYS: {message}")
    
    # Log to a critical incident file (local fallback)
    os.makedirs("logs", exist_ok=True)
    with open("logs/critical_incident.log", "a") as f:
        f.write(f"Node 1 failure detected at {asyncio.get_event_loop().time()}. This node ({NODE_ID}) entered safe state.\n")
    
    # Further actions could include attempting to take over as primary if using a Raft consensus.
    # For now, we halt.

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
