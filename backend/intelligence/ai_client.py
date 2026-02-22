import requests
import json
import re
from typing import List, Dict, Optional, Any

class MistralAIClient:
    """Centralized client for Mistral Large 3 via NVIDIA API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        self.model_name = "mistralai/mistral-large-3-675b-instruct-2512"

    def generate_content(self, prompt: str, temperature: float = 0.15, max_tokens: int = 4096) -> str:
        """Call Mistral Large 3 with standard parameters"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 1.00,
            "frequency_penalty": 0.00,
            "presence_penalty": 0.00,
            "stream": False
        }

        try:
            response = requests.post(self.invoke_url, headers=headers, json=payload, timeout=90)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Mistral API error: {e}")
            raise

    def extract_json(self, text: str) -> Dict[str, Any]:
        """Utility to extract JSON from model response"""
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                return {}
        return {}
