"""Ollama LLM client for local model inference"""
import requests
import json
from typing import Optional, Dict, List
from src.config import settings


class OllamaClient:
    """Client for interacting with Ollama local models"""

    def __init__(self, api_url: Optional[str] = None, model: Optional[str] = None):
        self.api_url = api_url or settings.OLLAMA_API_URL
        self.model = model or settings.OLLAMA_MODEL

    def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        top_p: float = 0.95,
        top_k: int = 40,
        stream: bool = False
    ) -> Dict:
        """Generate text using Ollama model"""
        url = f"{self.api_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "num_predict": 2048
            }
        }

        try:
            if stream:
                return self._stream_generate(url, payload)
            else:
                response = requests.post(url, json=payload, timeout=120)
                response.raise_for_status()
                return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama API error: {e}")

    def _stream_generate(self, url: str, payload: Dict) -> Dict:
        """Handle streaming responses from Ollama"""
        full_response = ""
        try:
            response = requests.post(
                url, json=payload, stream=True, timeout=120)
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if "response" in chunk:
                        full_response += chunk["response"]
                    if chunk.get("done", False):
                        return {
                            "response": full_response,
                            "done": True
                        }
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama streaming error: {e}")

        return {"response": full_response, "done": True}

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        stream: bool = False
    ) -> Dict:
        """Chat interface with Ollama model"""
        url = f"{self.api_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": 2048
            }
        }

        try:
            if stream:
                return self._stream_chat(url, payload)
            else:
                response = requests.post(url, json=payload, timeout=120)
                response.raise_for_status()
                return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama chat error: {e}")

    def _stream_chat(self, url: str, payload: Dict) -> Dict:
        """Handle streaming chat responses"""
        full_response = ""
        try:
            response = requests.post(
                url, json=payload, stream=True, timeout=120)
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if "message" in chunk and "content" in chunk["message"]:
                        full_response += chunk["message"]["content"]
                    if chunk.get("done", False):
                        return {
                            "message": {"content": full_response},
                            "done": True
                        }
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama chat streaming error: {e}")

        return {"message": {"content": full_response}, "done": True}

    def check_health(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = requests.get(f"{self.api_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
