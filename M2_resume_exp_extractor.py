import requests
import json
import re
import os
from typing import Dict, List, Optional, Union

from dotenv import load_dotenv
load_dotenv()  # Optional: only if using .env

class ExperienceExtractorAndParser:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Missing GROQ_API_KEY in environment variables")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "meta-llama/llama-4-scout-17b-16e-instruct"

        self.default_priority = [
            {'PROFESSIONAL EXPERIENCE', 'EXPERIENCE', 'WORK EXPERIENCE', 'EMPLOYMENT HISTORY',
             'CAREER HISTORY', 'JOB HISTORY', 'INDUSTRY EXPERIENCE'},
            {'INTERNSHIPS', 'INTERNSHIP EXPERIENCE', 'CO-OP EXPERIENCE'},
            {'RESEARCH EXPERIENCE', 'RESEARCH POSITIONS'},
            {'FREELANCE EXPERIENCE', 'CONTRACT WORK'}
        ]

    def extract_experience_text(
        self,
        parsed_resume: Dict[str, Union[str, Dict]],
        *,
        priority_order: Optional[List[str]] = None,
        format_output: bool = False,
        separator: str = "\n\n"
    ) -> str:
        priority_sets = priority_order or self.default_priority
        found_sections = []

        for priority_group in priority_sets:
            for section_name, section_content in parsed_resume.get("sections", {}).items():
                if section_name.upper() in priority_group:
                    if format_output:
                        found_sections.append(f"{section_name.upper()}:\n{section_content}")
                    else:
                        found_sections.append(section_content)

        if format_output and found_sections:
            return separator.join(found_sections[:1])
        elif found_sections:
            return found_sections[0]
        return ""

    def _clean_response(self, raw_text: str):
        match = re.search(r"```json\s*(.*?)```", raw_text, re.DOTALL)
        if not match:
            match = re.search(r"(\{.*\})", raw_text, re.DOTALL)
        if not match:
            raise ValueError("No valid JSON block found in model output")
        cleaned_json = match.group(1)
        return json.loads(cleaned_json)

    def parse_contact_and_experience(self, combined_text: str) -> Dict:
        prompt = [
            {
                "role": "system",
                "content": (
                    "You are an expert resume parser. Extract and return a structured JSON with these fields:\n"
                    "- name (string)\n"
                    "- email (string)\n"
                    "- phone (string)\n"
                    "- experience: a list of objects with\n"
                    "   - job_title (string)\n"
                    "   - company (string)\n"
                    "   - duration: {start, end}\n"
                    "   - location (string)\n"
                    "   - responsibilities: list of strings\n"
                    "Return only valid JSON without explanation."
                )
            },
            {
                "role": "user",
                "content": f"Here is the relevant text from a resume:\n\n{combined_text}\n\nReturn structured JSON as specified."
            }
        ]

        response = requests.post(
            self.api_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            },
            json={
                "model": self.model,
                "messages": prompt,
                "temperature": 0.2
            }
        )

        if response.status_code != 200:
            raise Exception(f"Groq API error {response.status_code}: {response.text}")

        raw_output = response.json()["choices"][0]["message"]["content"]
        data = self._clean_response(raw_output)
        return {
            "contact_info": {
                "name": data.get("name"),
                "email": data.get("email"),
                "phone": data.get("phone")
            },
            "experience": data.get("experience", [])
        }

    def extract_and_parse(self, parsed_resume: Dict[str, Union[str, Dict]]) -> Dict:
        header_text = parsed_resume.get("sections", {}).get("HEADER", "")
        experience_text = self.extract_experience_text(parsed_resume, format_output=True)
        combined_text = f"{header_text.strip()}\n\n{experience_text.strip()}"

        if not combined_text.strip():
            return {
                "name": None,
                "email": None,
                "phone": None,
                "experience": []
            }
        return self.parse_contact_and_experience(combined_text)


    def extract_and_parse_batch(self, parsed_resumes: List[Dict[str, Union[str, Dict]]]) -> List[Dict[str, Union[Dict, str]]]:
        results = []
        for resume in parsed_resumes:
            try:
                result = self.extract_and_parse(resume)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})
        return results
