import os
import sys
import json
import time
import threading
import pyautogui
from pathlib import Path
from datetime import datetime
from memory.local_vectordb import add_memory, query_memories
from agent.planner import create_plan
from agent.executor import execute_step

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
LOGS_DIR = BASE_DIR / "logs"
LOG_FILE = LOGS_DIR / "autogpt_audit.log"

def write_audit_log(message: str):
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(log_entry)

class AutoGPTRunner:
    def __init__(self):
        self.max_cycles = 10
        self.run_until_complete = False
        self.is_running = False
        self._thread = None
        self.current_task = ""
        self.logs_signal_callback = None

    def start_task(self, goal: str, max_cycles: int, until_complete: bool):
        if self.is_running:
            return
        self.current_task = goal
        self.max_cycles = max_cycles
        self.run_until_complete = until_complete
        self.is_running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.is_running = False
        write_audit_log("AutoGPT engine stopped manually by user.")

    def _run_loop(self):
        write_audit_log(f"Starting autonomous task: '{self.current_task}'")
        plan = create_plan(self.current_task)
        if not plan or "steps" not in plan:
            write_audit_log("Failed to generate task plan. Autonomous loop aborted.")
            self.is_running = False
            return

        steps = plan["steps"]
        cycle = 0
        step_idx = 0

        while self.is_running:
            if not self.run_until_complete and cycle >= self.max_cycles:
                write_audit_log(f"Cycle limit reached ({self.max_cycles}). Autonomous task paused.")
                break

            if step_idx >= len(steps):
                write_audit_log("All planned steps completed successfully!")
                break

            step = steps[step_idx]
            write_audit_log(f"Cycle {cycle + 1} - Executing Step {step.get('step')}: {step.get('description')}")
            
            if self.logs_signal_callback:
                self.logs_signal_callback(f"Cycle {cycle + 1}: Executing [{step.get('tool')}]")

            try:
                result = execute_step(step)
                write_audit_log(f"Step {step.get('step')} Result: {result}")
                step_idx += 1
            except Exception as error:
                write_audit_log(f"Step {step.get('step')} Failed with error: {error}")
                break

            cycle += 1
            time.sleep(1.0)

        self.is_running = False
        write_audit_log(f"Finished autonomous task: '{self.current_task}'")

    def learn_app_interaction(self, app_name: str, duration: int = 10) -> list:
        write_audit_log(f"Starting mouse/keyboard interaction capture for app: '{app_name}'")
        interactions = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            position = pyautogui.position()
            interactions.append({
                "time": time.time() - start_time,
                "x": position.x,
                "y": position.y
            })
            time.sleep(0.5)

        saved_value = json.dumps(interactions)
        add_memory(f"app_flow_{app_name}", saved_value, "Learned")
        write_audit_log(f"Successfully learned interactions for '{app_name}' and saved to vector DB.")
        return interactions

    def play_app_interaction(self, app_name: str):
        write_audit_log(f"Retrieving learned interactions for app: '{app_name}'")
        memories = query_memories(f"app_flow_{app_name}", category="Learned", top_k=1)
        if not memories:
            write_audit_log(f"No interactions learned for app '{app_name}'.")
            return
            
        try:
            interactions = json.loads(memories[0]["value"])
            for interaction in interactions:
                pyautogui.moveTo(interaction["x"], interaction["y"], duration=0.2)
                time.sleep(0.3)
            write_audit_log(f"Successfully replayed interactions for app '{app_name}'.")
        except Exception as error:
            write_audit_log(f"Error during app interaction replay: {error}")
