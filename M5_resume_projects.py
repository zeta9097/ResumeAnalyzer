import re
from typing import Dict, List, Union


class ProjectsExtractor:
    def __init__(self):
        self.project_keys = [
            # Standard variations
            'PROJECTS', 'PERSONAL PROJECTS', 'TECHNICAL PROJECTS', 'RESEARCH PROJECTS', 'RESEARCH EXPERIENCE', 
            'PROJECTS UNDERTAKEN', 'PROJECT EXPERIENCE', 'PROJECTS EXPERIENCE', 'PROJECTS AND ACTIVITIES', 
            'PROJECTS & ACTIVITIES', 'ACADEMIC PROJECTS', 

            # Academic/Research Focused
            'ACADEMIC RESEARCH PROJECTS', 'RESEARCH WORK', 'RESEARCH INITIATIVES', 'SCIENTIFIC PROJECTS',
            'THESIS PROJECT', 'DISSERTATION PROJECT', 'CAPSTONE PROJECT', 'FINAL YEAR PROJECT', 'GRADUATION PROJECT',

            # Industry/Work Focused
            'WORK PROJECTS', 'PROFESSIONAL PROJECTS', 'INDUSTRY PROJECTS', 'CLIENT PROJECTS', 'CONSULTING PROJECTS',
            'FREELANCE PROJECTS', 'CONTRACT PROJECTS', 'ENGINEERING PROJECTS', 'DEVELOPMENT PROJECTS',

            # Tech-Specific
            'SOFTWARE PROJECTS', 'CODING PROJECTS', 'PROGRAMMING PROJECTS', 'MACHINE LEARNING PROJECTS', 'AI PROJECTS',
            'DATA PROJECTS', 'ANALYTICS PROJECTS', 'BUSINESS INTELLIGENCE PROJECTS', 'CLOUD PROJECTS', 'DEVOPS PROJECTS',
            'CYBERSECURITY PROJECTS', 'DATA ANALYTICS PROJECTS', 'DATA SCIENCE PROJECTS', 'DATA ENGINEERING PROJECTS',
            'DATA ANALYTICS PROJECTS UNDERTAKEN', 'DATA ANALYSIS PROJECTS UNDERTAKEN',
            'DATA SCIENTIST PROJECTS UNDERTAKEN', 'DATA SCIENCE PROJECTS UNDERTAKEN',
            'DATA ENGINEERING PROJECTS UNDERTAKEN', 'DATA ENGINEER PROJECTS UNDERTAKEN',

            # General/Other Variations
            'SELECTED PROJECTS', 'KEY PROJECTS', 'MAJOR PROJECTS', 'NOTABLE PROJECTS', 'RECENT PROJECTS', 'PAST PROJECTS',
            'COMPLETED PROJECTS', 'ONGOING PROJECTS', 'SIDE PROJECTS', 'OPEN SOURCE PROJECTS', 'VOLUNTEER PROJECTS',
            'TEAM PROJECTS', 'INDIVIDUAL PROJECTS', 'GROUP PROJECTS', 'COLLABORATIVE PROJECTS'
        ]

    def extract_projects(self, parsed_data: Dict[str, Union[str, Dict]]) -> List[str]:
        all_projects = []

        for key in self.project_keys:
            if key in parsed_data.get('sections', {}):
                project_text = parsed_data['sections'][key].strip()
                
                # Option 1: Keep the entire section as one project
                all_projects.append(project_text)

        # Remove duplicates while preserving order
        seen = set()
        return [p for p in all_projects if not (p in seen or seen.add(p))]

    def extract_and_clean(self, parsed_data: Dict[str, Union[str, Dict]]) -> List[str]:
        """Extracts and cleans projects (if needed)."""
        raw_projects = self.extract_projects(parsed_data)
        # Add any cleaning logic here (e.g., lowercase, remove special chars)
        return raw_projects

    def extract_and_clean_batch(self, parsed_resumes: List[Dict[str, Union[str, Dict]]]) -> List[Dict[str, Union[List[str], str]]]:
        """Batch project extraction and cleaning"""
        results = []
        for resume in parsed_resumes:
            try:
                projects = self.extract_and_clean(resume)
                results.append({"projects": projects})  # Changed "skills" to "projects" for consistency
            except Exception as e:
                results.append({"error": str(e)})
        return results