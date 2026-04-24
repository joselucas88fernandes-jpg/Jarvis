
import asyncio
import json
import logging
import random
import time
from functools import wraps

import google.api_core.exceptions
import httpx
from google import genai

# Assuming ui.py has a logging method, e.g., ui.write_log()
# from ui import JarvisUI

def retry_with_backoff(retries=5, initial_delay=1, backoff_factor=2, jitter=True):
    """
    A decorator for retrying a function with exponential backoff.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = initial_delay
            for i in range(retries):
                try:
                    return await func(*args, **kwargs)
                except (
                    google.api_core.exceptions.ResourceExhausted,
                    httpx.ReadTimeout,
                    httpx.ConnectError,
                ) as e:
                    if i == retries - 1:
                        logging.error(f"Function {func.__name__} failed after {retries} retries. Error: {e}")
                        raise
                    
                    current_delay = delay + (random.uniform(0, 1) if jitter else 0)
                    logging.warning(f"Rate limited/Connection error. Retrying {func.__name__} in {current_delay:.2f} seconds.")
                    await asyncio.sleep(current_delay)
                    delay *= backoff_factor
        return wrapper
    return decorator

class LLMManager:
    """
    Manages interactions with multiple LLM providers (Gemini and Ollama),
    with a failover mechanism and retry logic.
    """

    def __init__(self, gemini_api_key: str, ollama_host: str = "http://localhost:11434", ui=None):
        self.gemini_api_key = gemini_api_key
        self.ollama_host = ollama_host
        self.ui = ui
        self.current_provider = "gemini"

        genai.configure(api_key=self.gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        self.async_http_client = httpx.AsyncClient(timeout=60.0)

    def log_to_ui(self, message: str):
        if self.ui:
            self.ui.write_log(message)
        else:
            logging.info(message)

    def _translate_prompt_for_ollama(self, prompt: str) -> dict:
        """
        Translates a prompt from Gemini's format to Ollama's format.
        This is a simple implementation assuming the prompt is a string.
        """
        return {
            "model": "llama3", # Assuming Llama 3 is the model on Node 2
            "prompt": prompt,
            "stream": False
        }

    @retry_with_backoff()
    async def _generate_with_gemini(self, prompt: str) -> str:
        """Generates content using the Gemini API."""
        self.log_to_ui("SYS: Contacting Gemini API...")
        response = await self.gemini_model.generate_content_async(prompt)
        return response.text

    @retry_with_backoff(retries=3, initial_delay=3)
    async def _generate_with_ollama(self, prompt: str) -> str:
        """Generates content using a local Ollama instance."""
        self.log_to_ui("SYS: Contacting local Ollama API...")
        ollama_prompt = self._translate_prompt_for_ollama(prompt)
        response = await self.async_http_client.post(f"{self.ollama_host}/api/generate", json=ollama_prompt)
        response.raise_for_status()
        response_json = response.json()
        return response_json.get("response", "")

    async def generate_content(self, prompt: str, force_provider: str = None) -> str:
        """
        Generates content using the current provider, with failover to Ollama.
        """
        provider_to_use = force_provider if force_provider else self.current_provider

        if provider_to_use == "gemini":
            try:
                return await self._generate_with_gemini(prompt)
            except google.api_core.exceptions.ResourceExhausted:
                self.log_to_ui("SYS: Gemini quota exhausted. Switching to Local Processing due to Quota.")
                self.current_provider = "ollama"
                return await self._generate_with_ollama(prompt)
            except Exception as e:
                self.log_to_ui(f"SYS: Gemini failed. Error: {e}. Switching to Local Processing.")
                self.current_provider = "ollama"
                return await self._generate_with_ollama(prompt)
        
        elif provider_to_use == "ollama":
            return await self._generate_with_ollama(prompt)
            
        else:
            raise ValueError(f"Unknown provider: {provider_to_use}")

