from typing import Dict, List, Union

class ResumeEducationExtractor:
    def __init__(self):
        # Priority-based keywords
        self.EDUCATION_KEYWORD_SETS = [
            'EDUCATION', 'ACADEMIC BACKGROUND', 'ACADEMIC QUALIFICATIONS',
            'EDUCATIONAL QUALIFICATIONS', 'EDUCATIONAL BACKGROUND',
            'EDUCATION AND CERTIFICATION', 'ACADEMIC QUALIFICATION',
            'EDUCATIONAL QUALIFICATION', 'EDUCATION AND CERTIFICATIONS',
            'EDUCATION & CERTIFICATIONS', 'EDUCATION & CERTIFICATION'
        ]

    def extract(self, parsed_resume: Dict[str, Union[str, Dict]]) -> List[str]:
        """
        Extracts education lines from one parsed resume.
        """
        for keyword in self.EDUCATION_KEYWORD_SETS:
            for section_name, section_content in parsed_resume.get("sections", {}).items():
                if section_name.upper() == keyword:
                    return [line.strip() for line in section_content.split("\n") if line.strip()]
        return []

    def extract_batch(self, parsed_resumes: List[Dict[str, Union[str, Dict]]]) -> List[Dict[str, Union[List[str], str]]]:
        """
        Batch extraction for a list of parsed resumes.
        Returns a list of dicts with extracted education or error.
        """
        results = []
        for resume in parsed_resumes:
            try:
                education_lines = self.extract(resume)
                results.append({"education": education_lines})
            except Exception as e:
                results.append({"error": str(e)})
        return results
