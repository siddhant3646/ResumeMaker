"""
Resume Renderer - Unified FPDF2 implementation
Supports both TailoredResume and ParsedResume models.
Works with CLI and Streamlit use cases.
"""

import copy
import os
import re
import unicodedata
from io import BytesIO
from pathlib import Path
from typing import Any, Optional, Union

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from pypdf import PdfReader


# Color constants
BLACK = (0, 0, 0)
ASSETS_DIR = Path(__file__).parent / "assets"


def normalize_date(date_str: str) -> str:
    """
    Normalize date format by adding a space between month and year if missing.
    Converts 'Jun2022' to 'Jun 2022', 'Jan2020' to 'Jan 2020', etc.
    """
    if not isinstance(date_str, str):
        return str(date_str) if date_str else ""
    
    import re
    # Pattern to match month abbreviation followed immediately by year (no space)
    # Matches: Jun2022, Jan2020, Mar2019, etc.
    pattern = r'^([a-zA-Z]{3,})(\d{4})$'
    match = re.match(pattern, date_str.strip())
    if match:
        month, year = match.groups()
        return f"{month} {year}"
    return date_str


def sanitize_unicode_for_pdf(text: str) -> str:
    """
    Replace Unicode characters with ASCII equivalents for FPDF compatibility.
    FPDF's core fonts (Times, Helvetica, Courier) only support ISO-8859-1 (Latin-1).
    This function maps common Unicode punctuation to ASCII equivalents.
    """
    if not isinstance(text, str):
        return str(text) if text else ""
    
    # Mapping of Unicode characters to ASCII equivalents
    unicode_replacements = {
        # Smart quotes
        '\u2018': "'",  # Left single quotation mark
        '\u2019': "'",  # Right single quotation mark (')
        '\u201a': "'",  # Single low-9 quotation mark
        '\u201b': "'",  # Single high-reversed-9 quotation mark
        '\u201c': '"',  # Left double quotation mark
        '\u201d': '"',  # Right double quotation mark
        '\u201e': '"',  # Double low-9 quotation mark
        '\u201f': '"',  # Double high-reversed-9 quotation mark
        # Dashes - Standardize to hyphen for consistency
        '\u2010': '-',  # Hyphen -> hyphen
        '\u2011': '-',  # Non-breaking hyphen -> hyphen
        '\u2012': '-',  # Figure dash -> hyphen
        '\u2013': '-',  # En dash -> hyphen
        '\u2014': '-',  # Em dash -> hyphen
        '\u2015': '-',  # Horizontal bar -> hyphen
        # Spaces and separators
        '\u00a0': ' ',  # Non-breaking space
        '\u202f': ' ',  # Narrow no-break space
        '\u2009': ' ',  # Thin space
        '\u2002': ' ',  # En space
        '\u2003': ' ',  # Em space
        '\u2007': ' ',  # Figure space
        # Other punctuation
        '\u2026': '...',  # Horizontal ellipsis
        '\u0027': "'",    # Apostrophe (straight single quote)
        '\u02c6': '^',    # Modifier letter circumflex
        '\u2039': '<',    # Single left-pointing angle quotation mark
        '\u203a': '>',    # Single right-pointing angle quotation mark
        '\u00ab': '<<',   # Left-pointing double angle quotation mark
        '\u00bb': '>>',   # Right-pointing double angle quotation mark
        '\u2212': '-',    # Minus sign
        '\u00d7': 'x',    # Multiplication sign
        '\u00f7': '/',    # Division sign
        '\u2022': '-',    # Bullet point
        '\u25cf': '-',    # Black circle (bullet)
        # Other common Unicode
        '—': '-',   # Em dash
        '–': '-',   # En dash
        '…': '...', # Ellipsis
        '•': '-',   # Bullet
        ''': "'",   # Left single quote
        ''': "'",   # Right single quote
        '"': '"',  # Left double quote
        '"': '"',  # Right double quote
    }
    
    # Replace known Unicode characters
    for unicode_char, ascii_char in unicode_replacements.items():
        text = text.replace(unicode_char, ascii_char)
    
    # Normalize remaining characters using NFKD decomposition,
    # then encode to ASCII ignoring any remaining non-ASCII characters
    try:
        # Decompose characters (e.g., é -> e + combining acute)
        normalized = unicodedata.normalize('NFKD', text)
        # Encode to ASCII, ignoring any remaining non-ASCII chars
        ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
        return ascii_text
    except Exception:
        # Fallback: just keep ASCII characters
        return ''.join(c for c in text if ord(c) < 128)


class ResumePDF(FPDF):
    """PDF generator for ATS-friendly resumes."""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
    
    def section_header(self, title: str):
        """Draw a section header with underline."""
        title = sanitize_unicode_for_pdf(title)
        self.set_font("Times", "B", 11)
        self.set_text_color(*BLACK)
        self.multi_cell(0, 6, title.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*BLACK)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.set_text_color(*BLACK)
        self.ln(1)
    
    def add_header_info(self, basics: Any):
        """Add name and contact information header - ATS optimized text-based layout."""
        # Name - centered and bold (larger)
        self.set_font("Times", "B", 20)
        self.set_text_color(*BLACK)
        name = sanitize_unicode_for_pdf(basics.name)
        self.cell(0, 10, name, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Contact info line: Phone | Email | Location
        self.set_font("Times", "", 10)
        self.set_text_color(*BLACK)
        
        contact_parts = []
        if basics.phone:
            contact_parts.append(basics.phone)
        if basics.email:
            contact_parts.append(basics.email)
        if basics.location:
            contact_parts.append(basics.location)
        
        if contact_parts:
            contact_line = " | ".join(contact_parts)
            contact_line = sanitize_unicode_for_pdf(contact_line)
            self.cell(0, 6, contact_line, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Links line: LinkedIn: username | GitHub: username
        if basics.links:
            link_parts = []
            for link in basics.links[:2]:
                clean_link = link.replace("https://", "").replace("http://", "")
                if "linkedin" in link.lower():
                    link_parts.append(f"LinkedIn: {clean_link}")
                elif "github" in link.lower():
                    link_parts.append(f"GitHub: {clean_link}")
                else:
                    link_parts.append(clean_link)
            
            if link_parts:
                links_line = " | ".join(link_parts)
                links_line = sanitize_unicode_for_pdf(links_line)
                self.set_font("Times", "", 10)
                self.cell(0, 6, links_line, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Separator line below header
        self.set_draw_color(*BLACK)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2)
    
    def add_summary(self, summary: str):
        """Add professional summary section - DEPRECATED - Never called to save space."""
        # This function is never called to save space for one-page layout
        pass
    
    def add_skills(self, skills: Any):
        """Add skills section in compact single-line format."""
        if not skills:
            return
            
        self.section_header("Technical Skills")
        self.set_font("Times", "", 10)
        self.set_text_color(*BLACK)
        
        # Handle both object attribute and dict access patterns
        languages = getattr(skills, 'languages_frameworks', None) or skills.get('languages_frameworks', [])
        tools = getattr(skills, 'tools', None) or skills.get('tools', [])
        
        # Combine all skills into single line
        all_skills = []
        if languages:
            all_skills.extend(languages)
        if tools:
            all_skills.extend(tools)
        
        if all_skills:
            skills_text = ", ".join(all_skills)
            self.multi_cell(0, 4, sanitize_unicode_for_pdf(skills_text),
                          new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        self.ln(1)
    
    def add_experience(self, experiences: list):
        """Add work experience section with smart bullet management."""
        if not experiences:
            return
        
        # Sort experiences by start date (most recent first)
        def parse_date(date_str):
            """Parse date string to comparable format."""
            if not date_str:
                return ""
            # Normalize first
            date_str = normalize_date(date_str)
            # Try to extract year
            import re
            year_match = re.search(r'\d{4}', date_str)
            if year_match:
                return year_match.group()
            return date_str
        
        sorted_experiences = sorted(experiences, 
                                    key=lambda x: parse_date(getattr(x, 'startDate', None) or x.get('startDate', '')),
                                    reverse=True)
            
        self.section_header("Professional Experience")
        
        for idx, exp in enumerate(sorted_experiences):
            # Company and Role
            self.set_font("Times", "B", 10)
            self.set_text_color(*BLACK)
            
            # Handle both object and dict access
            company = getattr(exp, 'company', None) or exp.get('company', '')
            location = getattr(exp, 'location', None) or exp.get('location', '')
            role = getattr(exp, 'role', None) or exp.get('role', '')
            start_date = getattr(exp, 'startDate', None) or exp.get('startDate', '')
            end_date = getattr(exp, 'endDate', None) or exp.get('endDate', '')
            bullets = getattr(exp, 'bullets', None) or exp.get('bullets', [])
            
            # Normalize date formats (e.g., "Jun2022" -> "Jun 2022")
            start_date = normalize_date(start_date)
            end_date = normalize_date(end_date)
            
            self.cell(0, 4, sanitize_unicode_for_pdf(role), new_x=XPos.RIGHT, new_y=YPos.LAST)
            
            # Date on the right
            date_str = f"{start_date} — {end_date}"
            self.cell(0, 4, sanitize_unicode_for_pdf(date_str), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            # Company and Location
            self.set_font("Times", "I", 10)
            self.set_text_color(*BLACK)
            self.cell(0, 4, sanitize_unicode_for_pdf(f"{company} | {location}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(0.5)
            
            # Smart bullet management
            is_most_recent = (idx == 0)
            
            if is_most_recent:
                # Most recent role: show all bullets (10-12 expected)
                bullets_to_show = bullets
            else:
                # Other roles: show only 1-2 bullets
                bullets_to_show = bullets[:2] if len(bullets) > 2 else bullets
            
            # Bullets with bold keywords
            for bullet in bullets_to_show:
                self.write_bullet_with_bold(bullet, line_height=4)
            
            # Add note if bullets were truncated
            if not is_most_recent and len(bullets) > 2:
                self.set_font("Times", "I", 9)
                self.set_text_color(100, 100, 100)  # Gray color
                self.cell(0, 3, f"[+{len(bullets) - 2} more achievements]", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                self.set_text_color(*BLACK)
            
            self.ln(1)
    
    def add_education(self, education: list):
        """Add education section."""
        if not education:
            return
            
        self.section_header("Education")
        
        for edu in education:
            # Handle both object and dict access
            institution = getattr(edu, 'institution', None) or edu.get('institution', '')
            location = getattr(edu, 'location', None) or edu.get('location', '')
            study_type = getattr(edu, 'studyType', None) or edu.get('studyType', '')
            area = getattr(edu, 'area', None) or edu.get('area', '')
            start_date = getattr(edu, 'startDate', None) or edu.get('startDate', '')
            end_date = getattr(edu, 'endDate', None) or edu.get('endDate', '')
            
            # Normalize date formats (e.g., "Jun2022" -> "Jun 2022")
            start_date = normalize_date(start_date)
            end_date = normalize_date(end_date)
            
            # Degree and Field
            self.set_font("Times", "B", 10)
            self.set_text_color(*BLACK)
            self.cell(0, 5, sanitize_unicode_for_pdf(f"{study_type} in {area}"),
                     new_x=XPos.RIGHT, new_y=YPos.LAST)
            
            # Date on right
            date_str = f"{start_date} — {end_date}"
            self.cell(0, 5, sanitize_unicode_for_pdf(date_str), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            # Institution and Location
            self.set_font("Times", "I", 10)
            self.set_text_color(*BLACK)
            self.cell(0, 5, sanitize_unicode_for_pdf(f"{institution} | {location}"),
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(1)
    
    def add_projects(self, projects: list):
        """Add projects section."""
        if not projects:
            return
            
        self.section_header("Projects")
        
        for proj in projects:
            # Handle both object and dict access
            name = getattr(proj, 'name', None) or proj.get('name', '')
            tech_stack = getattr(proj, 'techStack', None) or proj.get('techStack', '')
            description = getattr(proj, 'description', None) or proj.get('description', '')
            
            # Project name
            self.set_font("Times", "B", 10)
            self.set_text_color(*BLACK)
            self.cell(0, 5, sanitize_unicode_for_pdf(name), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            # Tech stack
            self.set_font("Times", "B", 9)
            self.set_text_color(*BLACK)
            self.cell(0, 4, sanitize_unicode_for_pdf(f"Tech Stack: {tech_stack}"),
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            # Description with bold formatting for keywords and metrics
            desc = description
            if desc and not desc.endswith(('.', '!', '?')):
                desc += '.'
            self.set_font("Times", "", 10)
            self.set_text_color(*BLACK)
            self.cell(4, 5, " ")  # Indent
            self.write_bullet_with_bold(desc, line_height=5)
            self.ln(1)  # Space after project
    
    def add_achievements(self, achievements: list):
        """Add achievements section."""
        if not achievements:
            return
            
        self.section_header("Achievements")
        
        for achievement in achievements:
            self.write_bullet_with_bold(achievement)
        
        self.ln(2)
    
    def _write_text_segment(self, text: str, line_height: float, bullet_indent: float, right_margin: float):
        """Write a text segment with proper word wrapping and spacing preservation."""
        words = text.split(' ')
        for i, word in enumerate(words):
            if not word:
                continue
            # Add space before word (except for first word at bullet start)
            if i > 0 or self.get_x() > self.l_margin + bullet_indent + 3:
                word_to_write = ' ' + word
            else:
                word_to_write = word
            
            word_width = self.get_string_width(word_to_write)
            
            if self.get_x() + word_width > right_margin - 5:
                # Use smaller line height for wrapped lines to reduce gaps
                self.ln(line_height * 0.8)
                self.set_x(self.l_margin + bullet_indent + 3)
                word_to_write = word  # No leading space at line start
            
            self.write(line_height, word_to_write)

    def write_bullet_with_bold(self, text: str, line_height: float = 4):
        """Write a bullet point with plain text formatting (no bold)."""
        text = sanitize_unicode_for_pdf(text)
        if not text:
            return
        
        bullet_indent = 6
        right_margin = self.w - self.r_margin
        
        # Start bullet
        self.set_font("Times", "", 10)
        self.cell(3, line_height, chr(149), new_x=XPos.RIGHT, new_y=YPos.LAST)
        
        # Write text without any bold formatting
        self._write_text_segment(text, line_height, bullet_indent, right_margin)
        
        # End bullet with line break - use smaller spacing
        self.ln(line_height)


def generate_filename(basics_name: str) -> str:
    """Generate filename in format: FirstNameLastNameResumeYear.pdf"""
    from datetime import datetime
    name_parts = basics_name.strip().split()
    if len(name_parts) >= 2:
        first_name = name_parts[0]
        last_name = name_parts[-1]
    else:
        first_name = name_parts[0] if name_parts else "Resume"
        last_name = ""
    
    current_year = datetime.now().year
    return f"{first_name}{last_name}Resume{current_year}.pdf"


def get_pdf_page_count(pdf_path: str) -> int:
    """Get the number of pages in a PDF file."""
    try:
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except Exception:
        return 1


def generate_pdf(resume: Any, output_path: Optional[str] = None, 
                 include_summary: bool = True, compact_mode: bool = False) -> str:
    """
    Generate PDF resume with optional summary and compact mode.
    
    Args:
        resume: Resume object (TailoredResume or ParsedResume)
        output_path: Output file path (if None, uses generated filename)
        include_summary: Whether to include the professional summary section
        compact_mode: Whether to use more compact spacing to fit on 1 page
    
    Returns:
        Absolute path to the generated PDF
    """
    # Handle both object and dict access for basics.name
    if hasattr(resume, 'basics'):
        basics = resume.basics
    else:
        basics = resume.get('basics', {})
    
    name = getattr(basics, 'name', None) or basics.get('name', 'Resume')
    
    # Generate filename if not provided
    if output_path is None:
        output_path = generate_filename(name)
    
    # Handle output as string or Path
    if isinstance(output_path, (str, Path)):
        out_dir = os.path.dirname(str(output_path))
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir)
    
    pdf = ResumePDF()
    
    # Adjust margins for compact mode
    if compact_mode:
        pdf.set_margins(10, 5, 10)
    else:
        pdf.set_margins(10, 7, 10)
    
    pdf.add_page()
    
    # Add header with name and contact info
    pdf.add_header_info(basics)
    
    # Add summary (optional)
    summary = getattr(resume, 'summary', None) or resume.get('summary', '')
    if include_summary and summary:
        pdf.add_summary(summary)
    
    # Add skills
    skills = getattr(resume, 'skills', None) or resume.get('skills')
    if skills:
        pdf.add_skills(skills)
    
    # Add experience
    experience = getattr(resume, 'experience', None) or resume.get('experience', [])
    if experience:
        pdf.add_experience(experience)
    
    # Add education
    education = getattr(resume, 'education', None) or resume.get('education', [])
    if education:
        pdf.add_education(education)
    
    # Add projects
    projects = getattr(resume, 'projects', None) or resume.get('projects', [])
    if projects:
        pdf.add_projects(projects)
    
    # Add achievements
    achievements = getattr(resume, 'achievements', None) or resume.get('achievements', [])
    if achievements:
        pdf.add_achievements(achievements)
    
    # Save to file
    pdf.output(output_path)
    return os.path.abspath(output_path)


def generate_pdf_to_bytes(resume: Any, include_summary: bool = False) -> bytes:
    """
    Generate PDF resume and return as bytes for Streamlit compatibility.
    NOTE: Summary is NEVER included to save space for 1-page layout.
    
    Args:
        resume: Resume object (TailoredResume or ParsedResume)
        include_summary: DEPRECATED - Summary is never included
        
    Returns:
        PDF as bytes
    """
    # Handle both object and dict access for basics.name
    if hasattr(resume, 'basics'):
        basics = resume.basics
    else:
        basics = resume.get('basics', {})
    
    pdf = ResumePDF()
    pdf.set_margins(8, 5, 8)  # Tighter margins for more content
    pdf.add_page()
    
    # Add header with name and contact info
    pdf.add_header_info(basics)
    
    # NO SUMMARY SECTION - skipped to save space for 1-page layout
    
    # Add skills
    skills = getattr(resume, 'skills', None) or resume.get('skills')
    if skills:
        pdf.add_skills(skills)
    
    # Add experience
    experience = getattr(resume, 'experience', None) or resume.get('experience', [])
    if experience:
        pdf.add_experience(experience)
    
    # Add education
    education = getattr(resume, 'education', None) or resume.get('education', [])
    if education:
        pdf.add_education(education)
    
    # Add projects
    projects = getattr(resume, 'projects', None) or resume.get('projects', [])
    if projects:
        pdf.add_projects(projects)
    
    # Add achievements
    achievements = getattr(resume, 'achievements', None) or resume.get('achievements', [])
    if achievements:
        pdf.add_achievements(achievements)
    
    # Output to bytes
    output = pdf.output()
    return bytes(output) if isinstance(output, bytearray) else output


def generate_pdf_with_page_check(resume: Any, output_dir: Optional[str] = None,
                                  max_attempts: int = 4) -> str:
    """
    Generate PDF with automatic 1-page constraint.
    NOTE: Summary is NEVER included (skipped to save space).
    Progressively removes sections if content exceeds 1 page:
    1. Full experience (10-12 bullets for recent role)
    2. Without projects (keep all experience)
    3. Without achievements (keep essential sections)
    4. Minimal version (experience + skills + education only)
    
    Args:
        resume: Resume object (TailoredResume or ParsedResume)
        output_dir: Output directory (if None, uses current directory)
        max_attempts: Maximum number of generation attempts (default 4)
    
    Returns:
        Absolute path to the generated PDF (guaranteed 1 page)
    """
    import copy
    
    # Handle both object and dict access for basics.name
    if hasattr(resume, 'basics'):
        basics = resume.basics
    else:
        basics = resume.get('basics', {})
    
    name = getattr(basics, 'name', None) or basics.get('name', 'Resume')
    
    # Generate filename
    filename = generate_filename(name)
    if output_dir:
        output_path = os.path.join(output_dir, filename)
    else:
        output_path = filename
    
    # Convert to dict for easy modification
    if hasattr(resume, 'dict'):
        resume_dict = resume.dict()
    elif hasattr(resume, 'model_dump'):
        resume_dict = resume.model_dump()
    else:
        resume_dict = dict(resume)
    
    # Store original values
    original_projects = resume_dict.get('projects', [])
    original_achievements = resume_dict.get('achievements', [])
    
    # NOTE: Summary is NEVER included to save space
    resume_dict['summary'] = ''
    
    # Try 1: Generate with full experience (10-12 bullets for most recent)
    temp_dict = copy.deepcopy(resume_dict)
    pdf_path = _generate_pdf_from_dict(temp_dict, output_path, compact_mode=False)
    page_count = get_pdf_page_count(pdf_path)
    
    if page_count == 1:
        return pdf_path
    
    # Try 2: Without projects (keep all experience bullets)
    if max_attempts >= 2:
        temp_dict = copy.deepcopy(resume_dict)
        temp_dict['projects'] = []
        pdf_path = _generate_pdf_from_dict(temp_dict, output_path, compact_mode=True)
        page_count = get_pdf_page_count(pdf_path)
        
        if page_count == 1:
            return pdf_path
    
    # Try 3: Without achievements (keep experience + skills + education + projects if they fit)
    if max_attempts >= 3:
        temp_dict = copy.deepcopy(resume_dict)
        temp_dict['achievements'] = []
        pdf_path = _generate_pdf_from_dict(temp_dict, output_path, compact_mode=True)
        page_count = get_pdf_page_count(pdf_path)
        
        if page_count == 1:
            return pdf_path
    
    # Try 4: Minimal version (experience + skills + education only)
    if max_attempts >= 4:
        temp_dict = copy.deepcopy(resume_dict)
        temp_dict['projects'] = []
        temp_dict['achievements'] = []
        pdf_path = _generate_pdf_from_dict(temp_dict, output_path, compact_mode=True)
        page_count = get_pdf_page_count(pdf_path)
        
        if page_count == 1:
            return pdf_path
    
    # Return the last attempt (minimum content version)
    return pdf_path


def _generate_pdf_from_dict(resume_dict: dict, output_path: str, compact_mode: bool = False) -> str:
    """Helper function to generate PDF from a resume dictionary."""
    pdf = ResumePDF()
    
    # Tighter margins for more content on one page
    if compact_mode:
        pdf.set_margins(8, 5, 8)
    else:
        pdf.set_margins(8, 5, 8)
    
    pdf.add_page()
    
    basics = resume_dict.get('basics', {})
    
    # Add header
    pdf.add_header_info(type('Basics', (), basics) if isinstance(basics, dict) else basics)
    
    # NO SUMMARY SECTION - skipped to save space
    
    # Add skills - handle both dict format and list format
    skills = resume_dict.get('skills')
    if skills:
        # Convert list format to dict format if needed
        if isinstance(skills, list):
            skills = {'languages_frameworks': skills, 'tools': []}
        pdf.add_skills(skills)
    
    # Add experience
    experience = resume_dict.get('experience', [])
    if experience:
        pdf.add_experience(experience)
    
    # Add education
    education = resume_dict.get('education', [])
    if education:
        pdf.add_education(education)
    
    # Add projects
    projects = resume_dict.get('projects', [])
    if projects:
        pdf.add_projects(projects)
    
    # Add achievements
    achievements = resume_dict.get('achievements', [])
    if achievements:
        pdf.add_achievements(achievements)
    
    pdf.output(output_path)
    return output_path


def render_and_save_pdf(resume: Any, output_path: Optional[str] = None, 
                        ensure_single_page: bool = True) -> str:
    """
    Render and save PDF with single-page guarantee.
    NOTE: Summary is NEVER included to save space.
    
    Args:
        resume: Resume object (TailoredResume or ParsedResume)
        output_path: Output file path (if None, uses generated filename)
        ensure_single_page: Always True - ensures 1-page layout
    
    Returns:
        Absolute path to the generated PDF
    """
    if ensure_single_page:
        output_dir = os.path.dirname(output_path) if output_path else None
        return generate_pdf_with_page_check(resume, output_dir)
    else:
        return generate_pdf(resume, output_path, include_summary=False, compact_mode=False)


def preview_html(resume: Any, output_path: str) -> str:
    """
    Generate a simple HTML preview of the resume.
    
    Args:
        resume: Resume object
        output_path: Path to save the HTML file
        
    Returns:
        Absolute path to the generated HTML file
    """
    # Handle both object and dict access
    if hasattr(resume, 'basics'):
        basics = resume.basics
        name = getattr(basics, 'name', 'Resume')
    else:
        name = resume.get('basics', {}).get('name', 'Resume')
    
    html = f"<html><body><h1>{sanitize_unicode_for_pdf(name)}</h1></body></html>"
    with open(output_path, 'w') as f:
        f.write(html)
    return os.path.abspath(output_path)


# Legacy alias for backward compatibility
generate_resume_pdf = generate_pdf_to_bytes
