
import logging
import google.generativeai as genai
# Assume ollama is installed and configured
import ollama

class LLMManager:
    """
    Manages interaction with different LLM providers (Gemini, Ollama).
    Includes context condensation for resilient failover.
    """
    def __init__(self, ui=None):
        # In a real app, these would come from a config file
        self.gemini_api_key = "YOUR_GEMINI_API_KEY" 
        self.current_provider = "gemini"
        self.ui = ui
        try:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
        except Exception as e:
            self._log(f"Gemini initialization failed: {e}. Will rely on Ollama.", "warning")
            self.current_provider = "ollama"

    async def generate_text(self, prompt: str, conversation_history: list = None) -> str:
        """
        Generates text using the current LLM provider, with failover.
        """
        conversation_history = conversation_history or []
        try:
            if self.current_provider == "gemini":
                return await self._generate_with_gemini(prompt, conversation_history)
            else:
                return await self._generate_with_ollama(prompt, conversation_history)
        except Exception as e: # Broadly catching provider errors
            self._log(f"LLM Error with {self.current_provider}: {e}. Attempting failover.", "error")
            if self.current_provider == "gemini":
                self.current_provider = "ollama"
                self._log("Switched to Ollama due to Gemini failure.", "warning")
                
                # Mission 2: Context Condenser Logic
                condensed_prompt = await self.condense_context(prompt, conversation_history)
                return await self._generate_with_ollama(condensed_prompt, []) # History is now condensed
            else:
                self._log("Ollama also failed. No more providers available.", "critical")
                raise  # Re-raise the exception if Ollama also fails

    async def _generate_with_gemini(self, prompt: str, history: list) -> str:
        # Simplified: a real implementation would handle history formatting
        full_prompt = "\n".join([h['content'] for h in history]) + "\n" + prompt
        response = await self.gemini_model.generate_content_async(full_prompt)
        return response.text

    async def _generate_with_ollama(self, prompt: str, history: list) -> str:
        # Simplified: a real implementation would handle history formatting
        full_prompt = "\n".join([h['content'] for h in history]) + "\n" + prompt
        response = await ollama.AsyncClient().generate(model='mistral', prompt=full_prompt)
        return response['response']

    async def condense_context(self, failed_prompt: str, history: list) -> str:
        """
        Summarizes a long context into a dense prompt for smaller models.
        """
        self._log("LLM: Condensing context for failover...", "info")
        
        condensation_prompt = f"""
        The following conversation history and prompt failed on a large language model, likely due to a temporary error.
        Summarize the user's ultimate goal and all critical technical constraints into a dense, high-signal, self-contained prompt of no more than 500 tokens. The summary must be sufficient for a smaller, local language model to complete the task without the full history.
        
        HISTORY:
        {history}

        FAILED PROMPT:
        {failed_prompt}

        CONDENSED PROMPT:
        """
        # Use Gemini to summarize itself, as it's likely still available for short tasks
        try:
            response = await self.gemini_model.generate_content_async(condensation_prompt)
            self._log("LLM: Context condensed successfully.", "info")
            return response.text
        except Exception as e:
            self._log(f"Context condensation failed: {e}. Falling back to original prompt.", "error")
            return failed_prompt # Fallback if the summarization itself fails

    def _log(self, message: str, level: str):
        logging.info(message)
