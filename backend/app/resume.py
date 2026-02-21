"""
Resume Processing - PDF parsing and generation
"""

import io
from typing import Dict, Any, List
import pdfplumber
import logging
from app.models import ParsedResume, Basics, Experience, Education, Skills, Project, TailoredResume

logger = logging.getLogger(__name__)

class ResumeProcessor:
    """Handle PDF resume parsing and generation"""
    
    async def parse_pdf(self, content: bytes) -> ParsedResume:
        """Parse PDF resume and extract structured data"""
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
                
                # Parse structured data from text
                # In production, use AI to extract structured data
                # For now, create a basic structure
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
        """Generate PDF from tailored resume data"""
        # Use existing renderer logic
        try:
            from fpdf import FPDF
            import unicodedata
            
            def safe_txt(text: str) -> str:
                if not text: return ""
                replacements = {
                    '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
                    '\u2013': '-', '\u2014': '-', '\u2026': '...', '\u2022': '-',
                    '\u00a0': ' ', '\t': '    '
                }
                for k, v in replacements.items():
                    text = text.replace(k, v)
                return unicodedata.normalize('NFKD', str(text)).encode('ascii', 'ignore').decode('ascii')
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            # Basic PDF generation
            pdf.cell(200, 10, txt=safe_txt(resume.basics.name), ln=True, align='C')
            pdf.cell(200, 10, txt=safe_txt(resume.basics.email), ln=True, align='C')
            if getattr(resume.basics, 'phone', None):
                pdf.cell(200, 10, txt=safe_txt(resume.basics.phone), ln=True, align='C')
            
            if resume.summary:
                pdf.ln(10)
                pdf.multi_cell(0, 10, txt=safe_txt(resume.summary))
            
            # Add experience
            for exp in resume.experience:
                pdf.ln(5)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, txt=safe_txt(f"{exp.role} at {exp.company}"), ln=True)
                pdf.set_font("Arial", size=12)
                for bullet in exp.bullets:
                    pdf.multi_cell(0, 10, txt=safe_txt(f"- {bullet}"))
            
            out = pdf.output(dest='S')
            if isinstance(out, str):
                out = out.encode('latin-1')
            pdf_bytes = io.BytesIO(out)
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise
