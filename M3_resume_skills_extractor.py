import re
from typing import Dict, List, Union


class SkillExtractor:
    def __init__(self):
        self.skill_keys = [
            # Standard variations
            'KEY COMPETENCIES', 'SKILLS', 'TECHNICAL SKILLS', 'CORE COMPETENCIES',
            'KEY SKILLS', 'TECHNOLOGIES', 'TOOLS & TECHNOLOGIES', 'SOFT SKILLS',
            'HARD SKILLS', 'KEY SKILLS & TECHNOLOGIES', 'TECHNICAL EXPERTISE',
            'AREAS OF EXPERTISE',

            # Domain-specific headers
            'FRONTEND SKILLS', 'FRONT-END SKILLS', 'FRONT END SKILLS',
            'BACKEND SKILLS', 'BACK-END SKILLS', 'BACK END SKILLS',
            'FULL STACK SKILLS', 'FULL-STACK SKILLS',
            'MOBILE SKILLS', 'DEVOPS SKILLS', 'CLOUD SKILLS',

            # Alternative phrasings
            'PROGRAMMING LANGUAGES', 'FRAMEWORKS', 'LIBRARIES',
            'SOFTWARE SKILLS', 'PROFESSIONAL SKILLS', 'AREAS OF EXPERTISE',
            'TECH STACK', 'TECHNICAL KNOWLEDGE', 'CORE SKILLS',

            # Subsection headers
            'PRIMARY SKILLS', 'SECONDARY SKILLS', 'ADDITIONAL SKILLS',
            'OTHER SKILLS', 'RELATED SKILLS'
        ]

    def extract_skills(self, parsed_data: Dict[str, Union[str, Dict]]) -> List[str]:
        all_skills = []

        for key in self.skill_keys:
            if key in parsed_data.get('sections', {}):
                skill_text = parsed_data['sections'][key]
                skills = re.split(r'[\n●•,;]', skill_text)
                skills = [skill.strip() for skill in skills if skill.strip()]
                all_skills.extend(skills)

        # Remove duplicates while preserving order
        seen = set()
        return [s for s in all_skills if not (s in seen or seen.add(s))]

    def clean_skills(self, skills_list: List[str]) -> List[str]:
        cleaned_skills = set()

        for item in skills_list:
            clean_item = ''.join(
                char for char in str(item)
                if char.isprintable() or char in ('/', '.', '-', '+')
            ).strip()

            if not clean_item:
                continue

            if ':' in clean_item:
                skills = clean_item.split(':', 1)[1]
                for skill in skills.split(','):
                    skill = skill.strip().lower()
                    if skill:
                        cleaned_skills.add(skill)
            else:
                cleaned_skills.add(clean_item.lower())

        return sorted(cleaned_skills)

    def extract_and_clean(self, parsed_data: Dict[str, Union[str, Dict]]) -> List[str]:
        raw_skills = self.extract_skills(parsed_data)
        return self.clean_skills(raw_skills)

    def extract_and_clean_batch(self, parsed_resumes: List[Dict[str, Union[str, Dict]]]) -> List[Dict[str, Union[List[str], str]]]:
        """Batch skill extraction and cleaning"""
        results = []
        for resume in parsed_resumes:
            try:
                skills = self.extract_and_clean(resume)
                results.append({"skills": skills})
            except Exception as e:
                results.append({"error": str(e)})
        return results
