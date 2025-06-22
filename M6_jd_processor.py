import requests
import json
import os

class JDExtractorGroq:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Missing GROQ_API_KEY in environment variables")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "meta-llama/llama-4-scout-17b-16e-instruct"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def extract(self, jd_text, temperature=0.3, max_tokens=1024):
        messages = [
            {
                "role": "system",
                "content": """You are an expert JD parser. Extract required fields in valid JSON format.
                Return ONLY the JSON object without any additional text or explanation.
                Use this structure:
                {
                    "skills": [],
                    "responsibilities": [],
                    "experience_requirements": [],
                    "education_requirements": []
                }"""
            },
            {
                "role": "user",
                "content": f"Extract information from this job description:\n{jd_text}"
            }
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"}  # Forces the model to return JSON
        }

        response = requests.post(self.api_url, headers=self.headers, json=payload)
        response.raise_for_status()
        
        # Extract the JSON string from the response
        json_str = response.json()["choices"][0]["message"]["content"]
        
        # Parse the JSON string into a Python dictionary
        try:
            return json.loads(json_str)  # Returns a dict
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response", "raw_output": json_str}