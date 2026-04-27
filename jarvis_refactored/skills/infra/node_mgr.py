import time
from jarvis_refactored.interfaces import SkillInput, SkillOutput
from jarvis_refactored.core.db_manager import system_state

NODE_HEARTBEATS = {}
NODE_TIMEOUT = 10  # seconds

def node_mgr(skill_input: SkillInput) -> SkillOutput:
    nodes = ["ThinkPad", "AMD3", "Node 3"]
    node_status = {}

    # Mock data generation
    for node in nodes:
        node_status[node] = {
            "status": "ONLINE", # Adicionado para clareza no HUD
            "cpu": "0.5%",
            "ram": "0.6%",
            "temp": "60°C"
        }
        NODE_HEARTBEATS[node] = time.time()

    # Self-healing check
    for node, last_heartbeat in list(NODE_HEARTBEATS.items()):
        if time.time() - last_heartbeat > NODE_TIMEOUT:
            node_status[node] = {"status": "DOWN"}
            system_state.update_state("node_status", {node: {"status": "DOWN"}})

    # Atualiza o estado global
    system_state.update_state("hardware_status", node_status)

    # CORREÇÃO DE REFERÊNCIA: Usando 'node_status' em vez de 'node_data'
    return SkillOutput(
        task_id=skill_input.task_id,
        status="SUCCESS",
        result=node_status, 
        metrics={
            "execution_time": 0.005, 
            "active_nodes": len(node_status)
        },
        logs=["Monitoramento de nós atualizado com sucesso."]
    )