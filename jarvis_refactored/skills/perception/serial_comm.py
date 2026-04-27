import asyncio
from typing import Dict, Any
from jarvis_refactored.interfaces import SkillInput, SkillOutput

# Mock implementation of serial communication
class MockSerial:
    def __init__(self):
        self._lock = asyncio.Lock()
        self.is_open = True

    async def write(self, data: bytes):
        async with self._lock:
            print(f"[SERIAL] Writing: {data}")
            await asyncio.sleep(0.1) # Simulate write time

    async def read(self, n=1) -> bytes:
        async with self._lock:
            await asyncio.sleep(0.1) # Simulate read time
            return b"OK"

    def close(self):
        self.is_open = False

async def serial_comm(skill_input: SkillInput) -> SkillOutput:
    logs = ["serial_comm skill invoked"]
    port = skill_input.payload.get("port", "/dev/ttyUSB0")
    command = skill_input.payload.get("command", "")
    metrics = {"bytes_written": 0}

    try:
        # In a real implementation, we would use pyserial_asyncio.open_serial_connection
        # For this example, we use a mock serial connection.
        serial = MockSerial()
        if not serial.is_open:
            raise ConnectionError("Serial port not available.")

        logs.append(f"Sending command '{command}' to {port}")
        await serial.write(command.encode())
        metrics["bytes_written"] = len(command)

        response = await serial.read(1024)
        logs.append(f"Received response: {response.decode()}")

        return SkillOutput(
            task_id=skill_input.task_id,
            status="SUCCESS",
            result={"response": response.decode()},
            logs=logs,
            metrics=metrics,
        )
    except Exception as e:
        return SkillOutput(
            task_id=skill_input.task_id,
            status="FAIL",
            result={"error": str(e)},
            logs=logs,
            metrics=metrics,
        )
    finally:
        if 'serial' in locals() and serial.is_open:
            serial.close()
            logs.append(f"Closed serial port {port}")
