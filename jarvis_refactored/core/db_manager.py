import threading
from typing import Dict, Any, List

class SystemState:
    def __init__(self):
        self._state: Dict[str, Any] = {
            "active_tasks": [],
            "hardware_status": {},
            "node_status": {},
            "safety_status": {},
            "decision_trace": []
        }
        self._lock = threading.Lock()

    def get_state(self) -> Dict[str, Any]:
        with self._lock:
            # Deep copy for safety
            return {k: v.copy() if isinstance(v, (dict, list)) else v for k, v in self._state.items()}

    def update_state(self, key: str, value: Any):
        with self._lock:
            if key in ["hardware_status", "node_status"]:
                # Atomic update for specific keys
                if key not in self._state:
                    self._state[key] = {}
                self._state[key].update(value)
            elif key in self._state and isinstance(self._state[key], list):
                self._state[key].append(value)
            else:
                self._state[key] = value

system_state = SystemState()
