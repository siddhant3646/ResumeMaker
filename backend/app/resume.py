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
        try:
            from fpdf import FPDF
            import unicodedata
            
            def safe_txt(text) -> str:
                if text is None: 
                    return ""
                text = str(text)
                replacements = {
                    '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
                    '\u2013': '-', '\u2014': '-', '\u2026': '...', '\u2022': '*',
                    '\u00a0': ' ', '\t': '    ',
                    '\u2010': '-', '\u2011': '-', '\u2012': '-',
                }
                for k, v in replacements.items():
                    text = text.replace(k, v)
                normalized = unicodedata.normalize('NFKD', text)
                return normalized.encode('latin-1', errors='replace').decode('latin-1')
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            name = getattr(resume.basics, 'name', None) or "Resume"
            email = getattr(resume.basics, 'email', None) or ""
            phone = getattr(resume.basics, 'phone', None) or ""
            
            pdf.set_font("Helvetica", 'B', 16)
            pdf.cell(0, 10, text=safe_txt(name), new_x="LMARGIN", new_y="NEXT", align='C')
            
            pdf.set_font("Helvetica", size=10)
            contact_parts = [p for p in [email, phone] if p]
            if contact_parts:
                pdf.cell(0, 8, text=safe_txt(" | ".join(contact_parts)), new_x="LMARGIN", new_y="NEXT", align='C')
            
            pdf.ln(5)
            
            summary = getattr(resume, 'summary', None)
            if summary:
                pdf.set_font("Helvetica", 'B', 11)
                pdf.cell(0, 8, text="Professional Summary", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", size=10)
                pdf.multi_cell(0, 6, text=safe_txt(summary))
                pdf.ln(5)
            
            experience = getattr(resume, 'experience', None) or []
            if experience:
                pdf.set_font("Helvetica", 'B', 11)
                pdf.cell(0, 8, text="Professional Experience", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
                
                for exp in experience:
                    role = getattr(exp, 'role', '') or ""
                    company = getattr(exp, 'company', '') or ""
                    
                    pdf.set_font("Helvetica", 'B', 10)
                    header = f"{role} at {company}" if role and company else role or company
                    if header:
                        pdf.cell(0, 7, text=safe_txt(header), new_x="LMARGIN", new_y="NEXT")
                    
                    pdf.set_font("Helvetica", size=10)
                    bullets = getattr(exp, 'bullets', None) or []
                    for bullet in bullets:
                        if bullet:
                            pdf.multi_cell(0, 6, text=safe_txt(f"  * {bullet}"))
                    pdf.ln(3)
            
            skills = getattr(resume, 'skills', None)
            if skills:
                all_skills = []
                langs = getattr(skills, 'languages_frameworks', None) or []
                tools = getattr(skills, 'tools', None) or []
                methods = getattr(skills, 'methodologies', None) or []
                all_skills = langs + tools + methods
                
                if all_skills:
                    pdf.set_font("Helvetica", 'B', 11)
                    pdf.cell(0, 8, text="Skills", new_x="LMARGIN", new_y="NEXT")
                    pdf.set_font("Helvetica", size=10)
                    pdf.multi_cell(0, 6, text=safe_txt(", ".join(all_skills)))
                    pdf.ln(5)
            
            education = getattr(resume, 'education', None) or []
            if education:
                pdf.set_font("Helvetica", 'B', 11)
                pdf.cell(0, 8, text="Education", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
                
                for edu in education:
                    institution = getattr(edu, 'institution', '') or ""
                    degree = getattr(edu, 'degree', '') or ""
                    field = getattr(edu, 'field', '') or ""
                    
                    pdf.set_font("Helvetica", 'B', 10)
                    if institution:
                        pdf.cell(0, 7, text=safe_txt(institution), new_x="LMARGIN", new_y="NEXT")
                    
                    pdf.set_font("Helvetica", size=10)
                    degree_text = f"{degree} in {field}" if field else degree
                    if degree_text:
                        pdf.cell(0, 6, text=safe_txt(degree_text), new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(2)
            
            out = pdf.output(dest='S')
            if isinstance(out, str):
                out = out.encode('latin-1')
            pdf_bytes = io.BytesIO(out)
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}", exc_info=True)
            raise
