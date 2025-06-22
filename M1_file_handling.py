import fitz  # PyMuPDF
from docx import Document
import pytesseract
from PIL import Image
from io import BytesIO
from pathlib import Path
import re
from typing import Dict, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor

SUPPORTED_TYPES = {
    '.pdf': 'pdf',
    '.docx': 'docx',
    '.png': 'image',
    '.jpg': 'image',
    '.jpeg': 'image'
}

class ResumeParser:
    def __init__(self):
        self.section_headers = [
    # Education
    'EDUCATION', 'ACADEMIC BACKGROUND', 'ACADEMIC QUALIFICATIONS', 'EDUCATIONAL QUALIFICATIONS',
    'EDUCATIONAL BACKGROUND', 'EDUCATIONAL QUALIFICATION',

    # Experience
    'EXPERIENCE', 'WORK EXPERIENCE', 'EMPLOYMENT HISTORY', 'PROFESSIONAL EXPERIENCE', 'JOB HISTORY', 'JOB PROFILE',
    'RELEVANT EXPERIENCE', 'CAREER HISTORY', 'WORK HISTORY', 'INDUSTRY EXPERIENCE', 'FREELANCE EXPERIENCE',
    'INTERNSHIP EXPERIENCE', 'INTERNSHIPS', 'CO-OP EXPERIENCE', 'RESEARCH EXPERIENCE', 'RESEARCH POSITIONS',
    'CONTRACT WORK', 'CAREER SUMMARY', 'VOLUNTEER EXPERIENCE', 'LEADERSHIP EXPERIENCE',

    # Skills
    'SKILLS', 'TECHNICAL SKILLS', 'CORE COMPETENCIES', 'KEY SKILLS', 'TECHNOLOGIES', 'TOOLS & TECHNOLOGIES',
    'SOFT SKILLS', 'SOFTWARE SKILLS', 'HARDWARE SKILLS', 'KEY COMPETENCIES', 'HARD SKILLS',
    'KEY SKILLS & TECHNOLOGIES', 'FRONT END', 'BACK END', 'FRONTEND', 'BACKEND', 'TOOLS', 'FRONT-END', 'BACK-END',
    'SKILLS SUMMARY', 'SKILLS AND ABILITIES', 'SKILLS & ABILITIES',

    # Projects
    'PROJECTS', 'PERSONAL PROJECTS', 'TECHNICAL PROJECTS', 'RESEARCH PROJECTS', 'PROJECTS UNDERTAKEN',
    'PROJECT EXPERIENCE', 'PROJECTS EXPERIENCE', 'PROJECTS AND ACTIVITIES', 'PROJECTS & ACTIVITIES',
    'ACADEMIC PROJECTS', 'DATA ANALYTICS PROJECTS UNDERTAKEN', 'DATA ANALYSIS PROJECTS UNDERTAKEN',
    'DATA SCIENTIST PROJECTS UNDERTAKEN', 'DATA SCIENCE PROJECTS UNDERTAKEN', 'DATA ENGINEERING PROJECTS UNDERTAKEN',
    'DATA ENGINEER PROJECTS UNDERTAKEN',

    # Certifications
    'CERTIFICATION', 'CERTIFICATIONS', 'CERTIFICATES', 'TRAINING', 'COURSES', 'PROFESSIONAL DEVELOPMENT',
    'COURSES AND CERTIFICATIONS', 'COURSES & CERTIFICATIONS',

    # Awards
    'AWARDS', 'ACHIEVEMENTS', 'HONORS', 'HONORS & AWARDS', 'RECOGNITION', 'AWARDS & ACHIEVEMENTS',

    # Summary / Profile
    'SUMMARY', 'PROFESSIONAL SUMMARY', 'EXECUTIVE SUMMARY', 'PROFILE', 'PROFILE SUMMARY', 'PERSONAL STATEMENT',
    'PERSONAL DETAILS', 'CAREER OBJECTIVE', 'CAREER OBJECTIVES',

    # Objective
    'OBJECTIVE', 'PROFESSIONAL OBJECTIVE', 'GOAL',

    # Miscellaneous
    'LANGUAGES', 'PUBLICATIONS', 'VOLUNTEERING', 'INTERESTS', 'HOBBIES', 'REFERENCES', 'EXTRACURRICULAR ACTIVITIES',
    'ADDITIONAL INFORMATION', 'COMMUNITY SERVICE', 'MILITARY SERVICE', 'SPEAKING ENGAGEMENTS', 'PRESENTATIONS',
    'PORTFOLIO', 'PROFESSIONAL AFFILIATIONS', 'MEMBERSHIPS', 'PAPERS', 'CONTACT INFORMATION', 'PERSONAL INFORMATION',
    'BIOGRAPHY', 'DECLARATION'
]

    def extract_text(self, file_input: Union[str, Path, BytesIO, object]) -> Optional[str]:
        """Universal text extractor"""
        if isinstance(file_input, (str, Path)):
            file_path = Path(file_input)
            suffix = file_path.suffix.lower()
            if suffix not in SUPPORTED_TYPES:
                raise ValueError(f"Unsupported file type: {suffix}")
            with open(file_path, 'rb') as f:
                file_content = f.read()
            return self._process_content(file_content, SUPPORTED_TYPES[suffix])
        
        elif hasattr(file_input, 'read'):
            file_content = file_input.read()
            file_input.seek(0)
            suffix = Path(file_input.filename).suffix.lower()
            return self._process_content(file_content, SUPPORTED_TYPES.get(suffix))
        
        raise TypeError("Input must be a path, file-like object, or stream")

    def _process_content(self, content: bytes, file_type: str) -> str:
        try:
            if file_type == 'pdf':
                return self._extract_pdf(BytesIO(content))
            elif file_type == 'docx':
                return self._extract_docx(BytesIO(content))
            elif file_type == 'image':
                return self._extract_image(BytesIO(content))
            else:
                raise ValueError(f"Unsupported type: {file_type}")
        except Exception as e:
            raise RuntimeError(f"Text extraction failed: {str(e)}")

    def _extract_pdf(self, file_stream: BytesIO) -> str:
        doc = fitz.open(stream=file_stream, filetype="pdf")
        return "\n".join(page.get_text() for page in doc)

    def _extract_docx(self, file_stream: BytesIO) -> str:
        return "\n".join(p.text for p in Document(file_stream).paragraphs if p.text)

    def _extract_image(self, file_stream: BytesIO) -> str:
        with Image.open(file_stream) as img:
            return pytesseract.image_to_string(img)

    def extract_sections(self, text: str) -> Dict[str, str]:
        sections = {}
        current_section = "HEADER"
        current_content = []
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            is_header = False
            for header in self.section_headers:
                pattern = r'^' + ''.join(f'{char}\s*' for char in header) + r'\s*[:-]?\s*$'
                if re.match(pattern, line, re.IGNORECASE):
                    if current_content:
                        sections[current_section] = '\n'.join(current_content)
                    current_section = header
                    current_content = []
                    is_header = True
                    break
            if not is_header:
                current_content.append(line)
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        return sections


    def extract_contact_info(self, text: str) -> Dict[str, str]:
        contact_info = {}

        # Basic name extraction from HEADER
        for line in text.split('\n'):
            line = line.strip()
            if line:
                contact_info['name'] = line
                break  # First non-empty line

        # Email and phone patterns
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        phone_pattern = r'(\+\d{1,3}[-.]?)?\s*\(?\d{3}\)?[-.]?\s*\d{3}[-.]?\s*\d{4}'

        if match := re.search(email_pattern, text):
            contact_info['email'] = match.group()
        if match := re.search(phone_pattern, text):
            contact_info['phone'] = match.group()

        return contact_info


    def parse_resume(self, file_input) -> Dict:
        try:
            text = self.extract_text(file_input)
            if not text:
                return {'error': 'No text extracted'}
            return {
                'sections': self.extract_sections(text),
                #'contact_info': self.extract_contact_info(text),
              }
        except Exception as e:
            return {'error': str(e)}

    def parse_resumes(self, file_inputs: List) -> List[Dict]:
        """Sequential batch parser"""
        return [self.parse_resume(file_input) for file_input in file_inputs]

    def parse_resumes_parallel(self, file_inputs: List, max_workers: int = 4) -> List[Dict]:
        """Parallel batch parser using threads"""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            return list(executor.map(self.parse_resume, file_inputs))
