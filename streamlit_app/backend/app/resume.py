"""
Resume Processing - PDF parsing and generation
"""

import io
from typing import Dict, Any, List
import pdfplumber
import logging
from backend.app.models import ParsedResume, Basics, Experience, Education, Skills, Project, TailoredResume

logger = logging.getLogger(__name__)

class ResumeProcessor:
    """Handle PDF resume parsing and generation"""
    
    async def parse_pdf(self, content: bytes, api_key: str = None) -> ParsedResume:
        """Parse PDF resume and extract structured data using AI if available"""
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
                
                if api_key:
                    try:
                        from intelligence.ai_client import MistralAIClient
                        client = MistralAIClient(api_key)
                        prompt = f"""Parse this resume text and extract structured information into a complete JSON format.

 Resume Text:
 {text[:6000]}

 Instructions:
 1. Extract EVERYTHING. Do not skip education entries, achievements, or experience bullets.
 2. Ensure dates are in YYYY-MM or similar standardized format.
 3. Achievements should be a list of strings, not mixed into experience if they are standalone.

 Extract and return ONLY valid JSON with this exact structure:
 {{
     "basics": {{
         "name": "full name",
         "email": "email address",
         "phone": "phone number",
         "location": "city, country",
         "links": ["linkedin url", "github url"]
     }},
     "education": [
         {{
             "institution": "school name",
             "studyType": "degree (e.g. MBA, B.Tech)",
             "area": "field of study",
             "startDate": "start date",
             "endDate": "end date",
             "location": "location"
         }}
     ],
     "experience": [
         {{
             "company": "company name",
             "role": "job title",
             "startDate": "start date",
             "endDate": "end date",
             "location": "location",
             "bullets": ["bullet 1", "bullet 2"]
         }}
     ],
     "skills": {{
         "languages_frameworks": ["python", "java", "react"],
         "tools": ["docker", "aws"]
     }},
     "projects": [
         {{
             "name": "project name",
             "techStack": "technologies used",
             "description": "brief description"
         }}
     ],
     "achievements": ["achievement 1", "achievement 2"]
 }}"""
                        response_text = client.generate_content(prompt, temperature=0.1)
                        data = client.extract_json(response_text)
                        
                        if data:
                            from backend.app.models import Basics, Education, Experience, Skills, Project, ParsedResume
                            basics = Basics(**data.get('basics', {}))
                            education = [Education(**edu) for edu in data.get('education', [])]
                            experience = [Experience(**exp) for exp in data.get('experience', [])]
                            
                            skills_dict = data.get('skills', {})
                            skills = Skills(
                                languages_frameworks=skills_dict.get('languages_frameworks', []),
                                tools=skills_dict.get('tools', []),
                                methodologies=skills_dict.get('methodologies', [])
                            )
                            
                            projects = [Project(**proj) for proj in data.get('projects', [])]
                            
                            return ParsedResume(
                                basics=basics,
                                education=education,
                                experience=experience,
                                skills=skills,
                                projects=projects,
                                achievements=data.get('achievements', [])
                            )
                    except Exception as ai_e:
                        logger.error(f"AI extraction failed, falling back: {ai_e}")

                # Fallback to basic extraction
                parsed_data = self._extract_resume_data(text)
                return parsed_data
                
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            raise
    
    def _extract_resume_data(self, text: str) -> ParsedResume:
        """Extract structured resume data from raw text"""
        # Simple extraction - in production use AI
        lines = text.strip().split('\n')
        
        # Basic parsing (placeholder implementation)
        # In production, use Mistral to parse and structure
        basics = Basics(
            name=lines[0] if lines else "",
            email=self._extract_email(text),
            phone=self._extract_phone(text)
        )
        
        return ParsedResume(
            basics=basics,
            summary="",
            experience=[],
            education=[],
            skills=Skills(languages_frameworks=[], tools=[], methodologies=[]),
            projects=[],
            achievements=[]
        )
    
    def _extract_email(self, text: str) -> str:
        """Extract email from text"""
        import re
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(pattern, text)
        return match.group(0) if match else ""
    
    def _extract_phone(self, text: str) -> str:
        """Extract phone number from text"""
        import re
        pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        match = re.search(pattern, text)
        return match.group(0) if match else ""
    
    async def generate_pdf(self, resume: TailoredResume) -> io.BytesIO:
        """Generate PDF from tailored resume data using the advanced v2 renderer"""
        try:
            from backend.app.renderer import generate_pdf_to_bytes
            
            # The v2 renderer returns raw bytes, wrap in BytesIO for StreamingResponse
            pdf_raw_bytes = generate_pdf_to_bytes(resume, include_summary=False)
            return io.BytesIO(pdf_raw_bytes)
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}", exc_info=True)
            raise
