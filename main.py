from fastapi import FastAPI, Body
from jarvis_refactored.core.ws_comm import ws_manager, app as fastapi_app
from jarvis_refactored.skills.hud.telemetry_vis import telemetry_vis
from jarvis_refactored.skills.infra.node_mgr import node_mgr
from jarvis_refactored.interfaces import SkillInput
import json
import asyncio
import time

app = fastapi_app

# --- MOTOR DE PULSO AUTOMÁTICO ---
async def heartbeat_loop():
    """Executa a percepção de hardware e transmite para o HUD a cada 5 segundos"""
    print("Iniciando loop de telemetria...")
    while True:
        try:
            pulse_input = SkillInput(
                task_id=f"auto-pulse-{int(time.time())}",
                timestamp=time.time(),
                source="System_Heartbeat",
                payload={},
                context={}
            )
            # 1. Atualiza o estado interno (CPU/RAM/Nodes)
            node_mgr(pulse_input)
            
            # 2. Gera a visualização de telemetria
            telemetry_output = telemetry_vis(pulse_input)
            
            # 3. Faz o broadcast automático via WebSocket para o HUD
            if telemetry_output.status == "SUCCESS":
                await ws_manager.broadcast(json.dumps(telemetry_output.result))
            
        except Exception as e:
            print(f"Erro no pulso de sistema: {e}")
        
        await asyncio.sleep(5)

# --- EVENTOS DE CICLO DE VIDA ---
@app.on_event("startup")
async def startup_event():
    # Registra a tarefa no background do event loop do FastAPI
    asyncio.create_task(heartbeat_loop())
    print("Protocolo de batimento cardíaco ativado com sucesso.")

# --- ROTAS MANUAIS (Para debug e triggers externos) ---

@app.post("/v1/tasks")
async def execute_task(payload: dict = Body(...)):
    skill_name = payload.get("skill")
    if skill_name == "node_mgr":
        task_input = SkillInput(
            task_id=f"node-update-{int(time.time())}",
            timestamp=time.time(),
            source="Manual_Trigger",
            payload={},
            context={}
        )
        result = node_mgr(task_input)
        return {"status": "SUCCESS", "output": result}
    return {"status": "ERROR", "message": "Skill não mapeada."}

@app.post("/v1/status/broadcast")
async def status_broadcast():
    """Gatilho manual de broadcast caso o loop falhe"""
    broadcast_input = SkillInput(
        task_id="broadcast-task",
        timestamp=time.time(),
        source="System_Manual_Trigger",
        payload={},
        context={}
    )
    telemetry_output = telemetry_vis(broadcast_input)
    if telemetry_output.status == "SUCCESS":
        await ws_manager.broadcast(json.dumps(telemetry_output.result))
        return {"status": "Broadcast successful", "data": telemetry_output.result}
    return {"status": "Broadcast failed", "reason": telemetry_output.logs}