from collections import deque
from jarvis_refactored.interfaces import SkillInput, SkillOutput, Task

class PriorityQueue:
    def __init__(self):
        self._queue = deque()

    def add_task(self, task: Task):
        # Simple priority implementation
        if task.priority > 5:
            self._queue.appendleft(task)
        else:
            self._queue.append(task)

    def get_task(self) -> Task:
        return self._queue.popleft()

    def is_empty(self) -> bool:
        return len(self._queue) == 0

task_queue = PriorityQueue()

def task_queue_skill(skill_input: SkillInput) -> SkillOutput:
    # This skill is for demonstration and doesn't have a real implementation
    return SkillOutput(status="SUCCESS", result={})
