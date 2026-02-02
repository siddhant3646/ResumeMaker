"""
Resume Renderer - Unified FPDF2 implementation
Supports both TailoredResume and ParsedResume models.
Works with CLI and Streamlit use cases.
"""

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
        """Add professional summary section with bold formatting for keywords and metrics."""
        if not summary:
            return
            
        self.section_header("Professional Summary")
        
        # Apply bold formatting to keywords and metrics in summary
        summary_text = sanitize_unicode_for_pdf(summary)
        if summary_text and not summary_text.endswith(('.', '!', '?')):
            summary_text += '.'
        
        self.set_font("Times", "", 10)
        self.set_text_color(*BLACK)
        self.write_bullet_with_bold(summary_text, line_height=5)
        self.ln(2)
    
    def add_skills(self, skills: Any):
        """Add skills section."""
        if not skills:
            return
            
        self.section_header("Technical Skills")
        self.set_font("Times", "", 10)
        self.set_text_color(*BLACK)
        
        # Handle both object attribute and dict access patterns
        languages = getattr(skills, 'languages_frameworks', None) or skills.get('languages_frameworks', [])
        tools = getattr(skills, 'tools', None) or skills.get('tools', [])
        
        if languages:
            self.set_font("Times", "B", 10)
            self.cell(0, 5, "Languages & Frameworks: ", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_font("Times", "", 10)
            self.multi_cell(0, 5, sanitize_unicode_for_pdf(", ".join(languages)),
                          new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        if tools:
            self.set_font("Times", "B", 10)
            self.cell(0, 5, "Tools & Platforms: ", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_font("Times", "", 10)
            self.multi_cell(0, 5, sanitize_unicode_for_pdf(", ".join(tools)),
                          new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        self.ln(2)
    
    def add_experience(self, experiences: list):
        """Add work experience section."""
        if not experiences:
            return
            
        self.section_header("Professional Experience")
        
        for exp in experiences:
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
            
            self.cell(0, 5, sanitize_unicode_for_pdf(role), new_x=XPos.RIGHT, new_y=YPos.LAST)
            
            # Date on the right
            date_str = f"{start_date} — {end_date}"
            self.cell(0, 5, sanitize_unicode_for_pdf(date_str), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            # Company and Location
            self.set_font("Times", "I", 10)
            self.set_text_color(*BLACK)
            self.cell(0, 5, sanitize_unicode_for_pdf(f"{company} | {location}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(1)
            
            # Bullets with bold keywords
            for bullet in bullets:
                self.write_bullet_with_bold(bullet)
            
            self.ln(2)
    
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
    
    def write_bullet_with_bold(self, text: str, line_height: float = 5):
        """Write a bullet point with bold first words, metrics and ATS keywords."""
        text = sanitize_unicode_for_pdf(text)
        if not text:
            return
        
        # Comprehensive patterns for metrics
        metric_patterns = [
            r'\d+[%+]',                           # Percentages: 40%, 25+
            r'\d+\s*(?:ms|milliseconds?)',        # Milliseconds: 200ms, 450 ms
            r'\d+\s*(?:seconds?|secs?)',          # Seconds: 2 seconds, 5 secs
            r'\d+\s*(?:minutes?|mins?)',          # Minutes: 45 minutes, 8 mins
            r'\d+\s*(?:hours?|hrs?)',             # Hours: 2 hours
            r'\d+\s*(?:days?|weeks?|months?)',    # Time periods: 3 weeks, 2 days
            r'\d+\s*x\b',                         # Multipliers: 3x, 10x
            r'\$[\d,]+[MKB]?',                    # Money: $500K, $2M, $150
            r'\d+[KMB]\+?\s*(?:users?|requests?|transactions?|daily)?',  # Scale: 50K users, 2M+ requests
            r'\d+\+?\s*(?:microservices?|services?|APIs?)',              # Counts: 15 microservices, 8+ APIs
            r'P\d+\s*(?:latency|response)',       # P99 latency, P95 response
            r'\d+\.\d+%',                         # Decimal percentages: 99.97%
            r'sub-\d+\s*(?:ms|seconds?)',         # Sub-metrics: sub-200ms
            r'\d+\s*(?:requests?/second|req/s|rps|QPS)',  # Throughput: 10K requests/second
            r'\d+\+\s*(?:clients?|stories|defects|members?)',  # Counts with +: 15+ clients, 80+ stories
        ]
        metric_pattern = '(' + '|'.join(metric_patterns) + ')'
        
        # ATS keywords to bold
        ats_keywords = [
            # Programming Languages
            'Java', 'Python', 'JavaScript', 'TypeScript', 'Go', 'Golang', 'Rust', 'C++', 'C#', 'Ruby', 'PHP', 'Scala', 'Kotlin',
            'XML', 'JSON', 'YAML',
            # Frontend
            'React', 'React.js', 'ReactJS', 'Angular', 'Vue', 'Vue.js', 'Next.js', 'HTML', 'CSS', 'SASS', 'Redux', 'Webpack',
            # Backend
            'Node.js', 'NodeJS', 'Express', 'Express.js', 'Spring Boot', 'Spring', 'SpringBoot', 'Django', 'FastAPI', 'Flask', 'Rails', 'NestJS',
            # Databases
            'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch', 'DynamoDB', 'Cassandra', 'Oracle', 'SQL', 'NoSQL', 'SQLite',
            'Firebase', 'Firestore', 'Database', 'DB',
            # Cloud & DevOps
            'AWS', 'EC2', 'S3', 'Lambda', 'RDS', 'CloudWatch', 'ECS', 'EKS', 'VPC', 'ELB', 'ALB', 'Route 53',
            'GCP', 'Google Cloud', 'Azure', 'Heroku', 'Pivotal Cloud Foundry', 'PCF',
            'Docker', 'Kubernetes', 'K8s', 'Terraform', 'Ansible', 'Helm', 'Jenkins', 'CI/CD', 'CICD',
            # Tools & Platforms
            'GitLab', 'GitHub', 'Git', 'Bitbucket', 'Jira', 'Confluence', 'Maven', 'Gradle', 'npm', 'yarn', 'pip',
            'CircleCI', 'Travis', 'ArgoCD', 'TeamCity',
            # Testing
            'Playwright', 'Selenium', 'Cucumber', 'JUnit', 'Jest', 'Mocha', 'Pytest', 'TestNG', 'Mockito',
            # Messaging & Streaming
            'Kafka', 'RabbitMQ', 'SQS', 'SNS', 'Pub/Sub', 'ActiveMQ', 'Apache Kafka', 'Apache Flink', 'Apache Spark', 'Apache Airflow', 'Apache Storm',
            # API & Security
            'REST', 'RESTful', 'GraphQL', 'gRPC', 'API', 'APIs', 'OAuth', 'OAuth2', 'JWT', 'OWASP', '3Scale',
            'Microservices', 'Serverless', 'Event-driven', 'Fortify', 'SSL', 'TLS', 'HTTPS',
            # Data & ML
            'Hadoop', 'DBT', 'Spark', 'Presto', 'Hive', 'TensorFlow', 'PyTorch', 'ML', 'AI', 'NLP', 'LLM', 'BERT', 'GPT',
            'YOLOv10', 'YOLO', 'TensorFlow Lite', 'Deep Learning', 'Machine Learning', 'Neural Network',
            # Monitoring & Observability
            'Grafana', 'Prometheus', 'Splunk', 'Datadog', 'New Relic', 'ELK', 'Kibana', 'Postman', 'Fortify', 'SonarQube',
            # Methodologies & Patterns
            'Agile', 'Scrum', 'Kanban', 'TDD', 'BDD', 'DevOps', 'SRE', 'SOLID', 'Design Pattern', 'System Design',
            'Data Structures', 'Algorithms', 'Object-oriented', 'OOP', 'CAP Theorem',
            # Action Verbs (Strong Impact)
            'Architected', 'Engineered', 'Designed', 'Authored', 'Developed', 'Implemented', 'Deployed',
            'Optimized', 'Reduced', 'Increased', 'Improved', 'Achieved', 'Slashed', 'Accelerated', 'Enhanced', 'Elevated',
            'Led', 'Managed', 'Directed', 'Spearheaded', 'Championed', 'Pioneered', 'Mentored', 'Coordinated',
            'Built', 'Created', 'Automated', 'Migrated', 'Integrated', 'Collaborated', 'Orchestrated', 'Forged', 'Constructed',
            'Resolved', 'Revamped', 'Strengthened', 'Audited', 'Secured', 'Hardened', 'Remediated', 'Prevented', 'Identified',
            'Streamlined', 'Transformed', 'Refactored', 'Debugged', 'Tested', 'Deployed', 'Published',
            # Company & Location Names
            'Fiserv', 'Noida', 'Pune', 'Bhopal', 'India',
            'Vellore Institute of Technology', 'Symbiosis International University',
            # Education & Certifications
            'MBA', 'B.Tech', 'Bachelor', 'Master', 'Computer Science', 'Business Analytics', 'Engineering',
            # Metrics & Measurement Terms
            'Efficiency', 'Performance', 'Reliability', 'Scalability', 'Throughput', 'Latency', 'Availability',
            'Coverage', 'Accuracy', 'Precision', 'Recall',
        ]
        
        # Build regex for keywords - case insensitive matching
        keyword_pattern = r'\b(' + '|'.join(re.escape(k) for k in sorted(ats_keywords, key=len, reverse=True)) + r')\b'
        
        # Find all bold segments
        bold_segments = set()
        
        # ALWAYS bold the first 3 words (Action Phrase)
        first_three_words = re.match(r'^(\W*\w+\W+\w+\W+\w+)', text)
        if first_three_words:
            bold_segments.add((first_three_words.start(), first_three_words.end()))
        
        # Find metrics
        for match in re.finditer(metric_pattern, text, re.IGNORECASE):
            bold_segments.add((match.start(), match.end()))
        
        # Find ATS keywords
        for match in re.finditer(keyword_pattern, text, re.IGNORECASE):
            bold_segments.add((match.start(), match.end()))
        
        # Sort by position and merge overlapping segments
        bold_list = sorted(bold_segments, key=lambda x: x[0])
        merged = []
        for start, end in bold_list:
            if merged and start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
            else:
                merged.append((start, end))
        
        # Render text with bold segments
        bullet_indent = 6
        right_margin = self.w - self.r_margin
        
        # Start bullet
        self.set_font("Times", "", 10)
        bullet_x = self.get_x()
        bullet_y = self.get_y()
        self.cell(3, line_height, chr(149), new_x=XPos.RIGHT, new_y=YPos.LAST)
        
        pos = 0
        for start, end in merged:
            # Normal text before bold segment
            if pos < start:
                self.set_font("Times", "", 10)
                normal_text = text[pos:start]
                words = normal_text.split()
                for i, word in enumerate(words):
                    word_to_write = word + (' ' if i < len(words) - 1 else '')
                    word_width = self.get_string_width(word_to_write)
                    
                    if self.get_x() + word_width > right_margin - 5:
                        self.ln(line_height)
                        self.set_x(self.l_margin + bullet_indent)
                    
                    self.write(line_height, word_to_write)
            
            # Bold text segment
            self.set_font("Times", "B", 10)
            bold_text = text[start:end]
            words = bold_text.split()
            for i, word in enumerate(words):
                word_to_write = word + (' ' if i < len(words) - 1 else '')
                word_width = self.get_string_width(word_to_write)
                
                if self.get_x() + word_width > right_margin - 5:
                    self.ln(line_height)
                    self.set_x(self.l_margin + bullet_indent)
                
                self.write(line_height, word_to_write)
            
            pos = end
        
        # Remaining normal text after last bold segment
        if pos < len(text):
            self.set_font("Times", "", 10)
            remaining_text = text[pos:]
            words = remaining_text.split()
            for i, word in enumerate(words):
                word_to_write = word + (' ' if i < len(words) - 1 else '')
                word_width = self.get_string_width(word_to_write)
                
                if self.get_x() + word_width > right_margin - 5:
                    self.ln(line_height)
                    self.set_x(self.l_margin + bullet_indent)
                
                self.write(line_height, word_to_write)
        
        # End bullet with line break
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


def generate_pdf_to_bytes(resume: Any, include_summary: bool = True) -> bytes:
    """
    Generate PDF resume and return as bytes for Streamlit compatibility.
    
    Args:
        resume: Resume object (TailoredResume or ParsedResume)
        include_summary: Whether to include the professional summary section
        
    Returns:
        PDF as bytes
    """
    # Handle both object and dict access for basics.name
    if hasattr(resume, 'basics'):
        basics = resume.basics
    else:
        basics = resume.get('basics', {})
    
    pdf = ResumePDF()
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
    
    # Output to bytes
    output = pdf.output()
    return bytes(output) if isinstance(output, bytearray) else output


def generate_pdf_with_page_check(resume: Any, output_dir: Optional[str] = None, 
                                  max_attempts: int = 2) -> str:
    """
    Generate PDF with automatic 1-page constraint.
    If the resume exceeds 1 page, it will retry without the summary section.
    
    Args:
        resume: Resume object (TailoredResume or ParsedResume)
        output_dir: Output directory (if None, uses current directory)
        max_attempts: Maximum number of generation attempts
    
    Returns:
        Absolute path to the generated PDF
    """
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
    
    # Try 1: Generate with summary
    pdf_path = generate_pdf(resume, output_path, include_summary=True, compact_mode=False)
    page_count = get_pdf_page_count(pdf_path)
    
    if page_count == 1:
        return pdf_path
    
    # Try 2: Generate without summary, compact mode
    summary = getattr(resume, 'summary', None) or resume.get('summary', '')
    if page_count > 1 and max_attempts >= 2 and summary:
        pdf_path = generate_pdf(resume, output_path, include_summary=False, compact_mode=True)
        page_count = get_pdf_page_count(pdf_path)
        
        if page_count == 1:
            return pdf_path
    
    # Return whatever we have
    return pdf_path


def render_and_save_pdf(resume: Any, output_path: Optional[str] = None, 
                        ensure_single_page: bool = True) -> str:
    """
    Render and save PDF with optional single-page guarantee.
    
    Args:
        resume: Resume object (TailoredResume or ParsedResume)
        output_path: Output file path (if None, uses generated filename)
        ensure_single_page: If True, will remove summary to fit on 1 page
    
    Returns:
        Absolute path to the generated PDF
    """
    if ensure_single_page:
        output_dir = os.path.dirname(output_path) if output_path else None
        return generate_pdf_with_page_check(resume, output_dir)
    else:
        return generate_pdf(resume, output_path, include_summary=True, compact_mode=False)


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
