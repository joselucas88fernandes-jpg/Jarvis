
import asyncio
import os
import threading
from pathlib import Path

from agent.dev_agent import DeveloperAgent
from core.llm_manager import LLMManager
from ui import JarvisUI

# Assuming these settings are in a config file or environment variables
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OLLAMA_HOST = "http://<IP_OF_NODE_2>:11434" # Set Node 2's IP
COMPILER_NODE_IP = "<IP_OF_NODE_3>" # Set Node 3's IP
COMPILER_NODE_USER = "user"
COMPILER_NODE_KEY_PATH = "/path/to/your/ssh/key"

IDLE_THRESHOLD = 300  # 5 minutes

class JarvisLive:

    def __init__(self, ui: JarvisUI):
        self.ui = ui
        self.last_interaction_time = asyncio.get_event_loop().time()

        # Initialize LLM Manager and Developer Agent
        self.llm_manager = LLMManager(gemini_api_key=GEMINI_API_KEY, ollama_host=OLLAMA_HOST, ui=self.ui)
        self.dev_agent = DeveloperAgent(
            project_root=".",
            llm_manager=self.llm_manager,
            ui=self.ui,
            compiler_node_ip=COMPILER_NODE_IP,
            compiler_node_user=COMPILER_NODE_USER,
            compiler_node_key_path=COMPILER_NODE_KEY_PATH
        )

    def speak(self, text: str):
        self.ui.write_log(f"Jarvis: {text}")
        # This would be connected to the text-to-speech engine
        pass

    async def _autonomous_loop(self):
        """The main loop for autonomous self-improvement with a hybrid LLM strategy."""
        while True:
            await asyncio.sleep(60)
            idle_time = asyncio.get_event_loop().time() - self.last_interaction_time

            if idle_time > IDLE_THRESHOLD:
                self.ui.write_log("SYS: Idle threshold reached. Starting self-improvement cycle.")
                self.speak("I'm taking a moment to review my own systems for potential improvements.")

                try:
                    # 1. AI-Driven Codebase Analysis
                    analysis = await self.dev_agent.analyze_codebase()
                    if not analysis:
                        self.speak("My analysis did not yield any actionable improvements this time.")
                        continue

                    # 2. Autonomous Code Generation
                    new_code, test_code = await self.dev_agent.generate_code(analysis.get('logic_blueprint'))
                    if not new_code or not test_code:
                        self.speak("I was unable to generate the necessary code. I will try again later.")
                        continue

                    # 3. Distributed Sandbox Execution (with Safety Interlock)
                    # Using Node 3 for compilation to keep Node 1 free
                    test_successful = await self.dev_agent.create_sandbox(new_code, test_code, use_compiler_node=True)
                    if test_successful:
                        self.speak("The proposed improvements have passed all sandbox tests.")

                        # 4. Proactive Report & User Approval
                        diff_report = self.dev_agent._get_changed_snippets() # Simplified for this example
                        report = self.dev_agent.generate_proactive_report(analysis, diff_report)
                        self.speak(report)

                        # In a real scenario, you would wait for user input here.
                        # For this example, we'll simulate approval.
                        user_approved = True 

                        if user_approved:
                            # Implement the changes (e.g., replace file, commit to Git)
                            self.speak("Changes have been approved and are now being integrated.")
                            # self.dev_agent.commit_changes(...) 
                        else:
                            self.speak("Understood. I will discard the proposed changes.")

                    else:
                        self.speak("The generated code failed sandbox testing. I will discard the changes and re-evaluate.")

                except Exception as e:
                    self.ui.write_log(f"SYS: Self-improvement cycle failed. Error: {e}")
                    self.speak("I encountered an error during my self-improvement cycle. I will try again later.")
                finally:
                    self.last_interaction_time = asyncio.get_event_loop().time()  # Reset idle timer

    async def run(self):
        # Main application loop
        self.ui.write_log("SYS: JARVIS online.")
        # This would include the existing audio and interaction loops
        # For this example, we focus on the autonomous loop
        await self._autonomous_loop()


def main():
    # A mock UI for logging purposes
    class MockUI:
        def write_log(self, msg):
            print(msg)

    ui = MockUI()
    jarvis = JarvisLive(ui)
    
    try:
        asyncio.run(jarvis.run())
    except KeyboardInterrupt:
        print("\n🔴 Shutting down...")

if __name__ == "__main__":
    main()
