import httpx
import json
import re
import os
import asyncio
from typing import List, Dict, Any


class ResumeJDScorerAsync:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Missing GROQ_API_KEY in environment variables")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.model = "meta-llama/llama-4-scout-17b-16e-instruct"

    def _extract_resume_dict(self, parsed_resume: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "skills": parsed_resume.get("skills", []),
            "education": parsed_resume.get("education", []),
            "experience": parsed_resume.get("experience", []),
            "projects": parsed_resume.get("projects", [])  # Added project support
        }

    def _extract_jd_dict(self, parsed_jd: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "skills": parsed_jd.get("skills", []),
            "responsibilities": parsed_jd.get("responsibilities", []),
            "experience_reqs": parsed_jd.get("experience_reqs", []),
            "education_reqs": parsed_jd.get("education_reqs", [])
        }

    def build_prompt(self, resume_json: Dict, jd_json: Dict) -> str:
        return f"""
You are a domain-agnostic resume and job evaluator.

Given a candidate's resume and a job description, return only the following structured JSON:

- "education_score": float (0.0 to 1.0)
- "skills_score": float (0.0 to 1.0)
- "experience_score": float (0.0 to 1.0)
- "project_relevance_score": float (0.0 to 1.0)
- "final_score": float (calculated as: 35% experience, 45% skills, 10% education, 10% projects)
- "domain_match_score": float (0.0 to 1.0) (semantic alignment of resume domain and job domain)
- "adjusted_final_score": float (final_score * domain_match_score)
- "missing_skills": list of strings (skills clearly required by the job but **not found semantically or explicitly** in the resume)

### Matching Rules:

- Use **semantic understanding**, not just literal word matching.
- If the resume lacks work experience but contains strong job-relevant projects, allow **projects to partly compensate** for missing experience.
- Only reward projects that are clearly **aligned** with job skills, tools, or responsibilities.
- If the JD does not specify education requirements, assign education_score = 1.0
- If no projects are found, assign project_relevance_score = 0.0

Return only raw JSON. Do NOT use markdown, explanations, or backticks.

### Job Description JSON:
{json.dumps(jd_json, indent=2)}

### Candidate Resume JSON:
{json.dumps(resume_json, indent=2)}
"""

    async def score_resume(self, client: httpx.AsyncClient, parsed_resume: Dict[str, Any], parsed_jd: Dict[str, Any]) -> Dict[str, Any]:
        resume_dict = self._extract_resume_dict(parsed_resume)
        jd_dict = self._extract_jd_dict(parsed_jd)
        prompt = self.build_prompt(resume_dict, jd_dict)

        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert resume evaluator."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }

        try:
            response = await client.post(self.api_url, headers=self.headers, json=body, timeout=60)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]

            cleaned = content.strip().strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()

            json_match = re.search(r"\{[\s\S]*?\}", cleaned)
            if json_match:
                return json.loads(json_match.group())

            raise ValueError("No valid JSON object found in LLM response.")
        except Exception as e:
            print("Failed to score resume:", e)
            print("Raw content:\n", content)
            return {"error": str(e)}

    async def score_resumes_batch(
        self,
        parsed_resumes: List[Dict[str, Any]],
        parsed_jd: Dict[str, Any],
        include_contact: bool = False
    ) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            tasks = [
                self.score_resume(client, resume, parsed_jd)
                for resume in parsed_resumes
            ]
            raw_scores = await asyncio.gather(*tasks)

            scored_with_metadata = []
            for resume, score in zip(parsed_resumes, raw_scores):
                contact = resume.get("contact_info", {}) or {}
                name = contact.get("name") or contact.get("email") or "Unknown"

                entry = {
                    "name": name.title(),
                    "match_percent": round(score.get("adjusted_final_score", 0.0) * 100, 2)
                        if isinstance(score.get("adjusted_final_score"), (int, float)) else "NaN",
                    "skills_score": round(score.get("skills_score", 0.0) * 100, 2),
                    "experience_score": round(score.get("experience_score", 0.0) * 100, 2),
                    "education_score": round(score.get("education_score", 0.0) * 100, 2),
                    "project_score": round(score.get("project_relevance_score", 0.0) * 100, 2),
                    "domain_match_score": round(score.get("domain_match_score", 0.0) * 100, 2),
                    "missing_skills": score.get("missing_skills", []),
                    "original_file_name": resume.get("original_file_name", "Unknown")
                }

                if include_contact:
                    entry["email"] = contact.get("email") or "N/A"
                    entry["phone"] = contact.get("phone") or "N/A"
                    


                scored_with_metadata.append(entry)

            return scored_with_metadata

