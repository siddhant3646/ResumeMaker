"""
Resume Renderer - Simple FPDF2 implementation
Uses multi_cell with proper cursor positioning.
"""

import os
import re
import unicodedata
from pathlib import Path
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from pypdf import PdfReader


PURPLE = (75, 0, 130)  # Keep for reference but using black
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
        # Dashes - Standardize to em dash for consistency
        '\u2010': '—',  # Hyphen -> em dash
        '\u2011': '—',  # Non-breaking hyphen -> em dash
        '\u2012': '—',  # Figure dash -> em dash
        '\u2013': '—',  # En dash -> em dash
        '\u2014': '—',  # Em dash (keep)
        '\u2015': '—',  # Horizontal bar -> em dash
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
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        
    def section_header(self, title: str):
        title = sanitize_unicode_for_pdf(title)
        self.set_font("Times", "B", 11)
        self.set_text_color(*BLACK)
        self.multi_cell(0, 6, title.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*BLACK)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.set_text_color(*BLACK)
        self.ln(1)
    
    def icon_text_line(self, items: list, icon_size: float = 3.5):
        """Render a centered line with icon+text pairs.
        items: list of tuples [(icon_filename or None, text), ...]
        """
        # Sanitize all text items
        sanitized_items = [(icon_file, sanitize_unicode_for_pdf(text)) for icon_file, text in items]
        
        self.set_font("Times", "", 9)
        self.set_text_color(0, 0, 0)
        
        gap = 1.5  # consistent gap between all elements
        separator = "|"
        sep_width = self.get_string_width(separator)
        
        # Calculate total width
        total_width = 0
        for i, (icon_file, text) in enumerate(sanitized_items):
            if i > 0:
                total_width += gap + sep_width + gap  # gap | gap
            if icon_file and (ASSETS_DIR / icon_file).exists():
                total_width += icon_size + gap  # icon + gap before text
            total_width += self.get_string_width(text)
        
        # Start from center
        x = (self.w - total_width) / 2
        y = self.get_y()
        
        for i, (icon_file, text) in enumerate(sanitized_items):
            # Separator between items
            if i > 0:
                x += gap
                self.set_xy(x, y)
                self.cell(sep_width, icon_size, separator)
                x += sep_width + gap
            
            # Icon
            if icon_file and (ASSETS_DIR / icon_file).exists():
                try:
                    self.image(str(ASSETS_DIR / icon_file), x=x, y=y + 0.5, h=icon_size - 1)
                except Exception:
                    # If icon fails to render, skip it
                    pass
                x += icon_size + gap
            
            # Text
            text_w = self.get_string_width(text)
            self.set_xy(x, y)
            self.cell(text_w, icon_size, text)
            x += text_w
        
        self.ln(icon_size + 2)
    
    def write_bullet_with_bold(self, text: str, line_height: float = 5):
        """Write a bullet point with bold first words, metrics and ATS keywords."""
        # Sanitize text to remove Unicode characters that FPDF doesn't support
        text = sanitize_unicode_for_pdf(text)
        
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
        
        # Expanded ATS keywords to bold - Comprehensive industry terminology coverage
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
        
        # Build regex for keywords - case insensitive matching but preserve original case in output
        keyword_pattern = r'\b(' + '|'.join(re.escape(k) for k in sorted(ats_keywords, key=len, reverse=True)) + r')\b'
        
        # Find all bold segments
        bold_segments = set()
        
        # ALWAYS bold the first 3 words (Action Phrase)
        first_three_words = re.match(r'^(\W*\w+\W+\w+\W+\w+)', text)
        if first_three_words:
            bold_segments.add((first_three_words.start(), first_three_words.end()))
        
        for match in re.finditer(metric_pattern, text, re.IGNORECASE):
            bold_segments.add((match.start(), match.end()))
        for match in re.finditer(keyword_pattern, text, re.IGNORECASE):
            bold_segments.add((match.start(), match.end()))
        
        # Sort by position
        bold_list = sorted(bold_segments, key=lambda x: x[0])
        
        # Merge overlapping segments
        merged = []
        for start, end in bold_list:
            if merged and start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
            else:
                merged.append((start, end))
        
        # Write text with mixed fonts using cell() for better compatibility
        pos = 0
        x_start = self.get_x()
        y = self.get_y()
        page_width = self.w - self.r_margin
        
        for start, end in merged:
            # Normal text before
            if pos < start:
                self.set_font("Times", "", 10)
                normal_text = text[pos:start]
                # Check if we need to wrap
                text_width = self.get_string_width(normal_text)
                if x_start + text_width > page_width:
                    # Print what fits
                    self.set_xy(x_start, y)
                    self.cell(0, line_height, normal_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                    x_start = self.l_margin
                    y = self.get_y()
                else:
                    self.set_xy(x_start, y)
                    self.cell(text_width, line_height, normal_text)
                    x_start += text_width
            
            # Bold text
            bold_text = text[start:end]
            self.set_font("Times", "B", 10)
            text_width = self.get_string_width(bold_text)
            if x_start + text_width > page_width:
                self.set_xy(x_start, y)
                self.cell(0, line_height, bold_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                x_start = self.l_margin
                y = self.get_y()
            else:
                self.set_xy(x_start, y)
                self.cell(text_width, line_height, bold_text)
                x_start += text_width
            
            pos = end
        
        # Remaining normal text
        if pos < len(text):
            self.set_font("Times", "", 10)
            remaining_text = text[pos:]
            text_width = self.get_string_width(remaining_text)
            if x_start + text_width > page_width:
                self.set_xy(x_start, y)
                self.cell(0, line_height, remaining_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            else:
                self.set_xy(x_start, y)
                self.cell(text_width, line_height, remaining_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            self.ln(line_height)


def get_pdf_page_count(pdf_path: str) -> int:
    """Get the number of pages in a PDF file."""
    try:
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except Exception:
        return 1


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


def generate_pdf(resume, output_path: str = None, include_summary: bool = True, compact_mode: bool = False) -> str:
    """
    Generate PDF resume with optional summary and compact mode.
    
    Args:
        resume: TailoredResume object
        output_path: Output file path (if None, uses generated filename)
        include_summary: Whether to include the professional summary section
        compact_mode: Whether to use more compact spacing to fit on 1 page
    
    Returns:
        Absolute path to the generated PDF
    """
    # Generate filename if not provided
    if output_path is None:
        output_path = generate_filename(resume.basics.name)
    
    pdf = ResumePDF()
    
    # Adjust margins for compact mode
    if compact_mode:
        pdf.set_margins(10, 5, 10)  # Even smaller top margin
    else:
        pdf.set_margins(10, 7, 10)  # Standard minimal margins
    
    pdf.add_page()

    # === HEADER: NAME ===
    pdf.set_font("Times", "B", 20)
    pdf.set_text_color(*BLACK)
    name = sanitize_unicode_for_pdf(resume.basics.name)
    pdf.multi_cell(0, 10, name, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # === HEADER: CONTACT INFO LINE (Phone | Email | Location) ===
    pdf.set_font("Times", "", 10)
    pdf.set_text_color(*BLACK)
    
    contact_line = f"{resume.basics.phone} | {resume.basics.email} | {resume.basics.location}"
    contact_line = sanitize_unicode_for_pdf(contact_line)
    pdf.multi_cell(0, 6, contact_line, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # === HEADER: LINKS LINE (LinkedIn | GitHub) ===
    if resume.basics.links:
        link_parts = []
        for link in resume.basics.links[:2]:
            clean_link = link.replace("https://", "").replace("http://", "")
            if "linkedin" in link.lower():
                link_parts.append(f"LinkedIn: {clean_link}")
            elif "github" in link.lower():
                link_parts.append(f"GitHub: {clean_link}")
            else:
                link_parts.append(clean_link)
        
        links_line = " | ".join(link_parts)
        links_line = sanitize_unicode_for_pdf(links_line)
        pdf.set_font("Times", "", 10)
        pdf.multi_cell(0, 6, links_line, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # === HEADER: SEPARATOR LINE ===
    pdf.set_draw_color(*BLACK)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(2)

    if compact_mode:
        pdf.ln(1)
    else:
        pdf.ln(2)

    # === PROFESSIONAL SUMMARY (Optional) ===
    if include_summary and resume.summary:
        pdf.section_header("Professional Summary")
        
        # Apply bold formatting to keywords and metrics in summary
        summary_text = sanitize_unicode_for_pdf(resume.summary)
        # Ensure summary ends with a period
        summary_text = summary_text.rstrip()
        if summary_text and not summary_text.endswith(('.', '!', '?')):
            summary_text += '.'
        
        pdf.set_font("Times", "", 10)
        pdf.write_bullet_with_bold(summary_text, line_height=5)
        
        if compact_mode:
            pdf.ln(1)
        else:
            pdf.ln(2)

    # === SKILLS ===
    if resume.skills:
        pdf.section_header("Skills")

        # Languages & Frameworks
        if resume.skills.languages_frameworks:
            pdf.set_font("Times", "B", 10)
            pdf.write(5, "Languages & Frameworks: ")
            pdf.set_font("Times", "", 10)
            skills_text = sanitize_unicode_for_pdf(", ".join(resume.skills.languages_frameworks))
            pdf.write(5, skills_text)
            pdf.ln(5)

        # Tools
        if resume.skills.tools:
            pdf.set_font("Times", "B", 10)
            pdf.write(5, "Tools: ")
            pdf.set_font("Times", "", 10)
            tools_text = sanitize_unicode_for_pdf(", ".join(resume.skills.tools))
            pdf.write(5, tools_text)
            pdf.ln(5)

    # === EXPERIENCE ===
    if resume.experience:
        pdf.section_header("Work Experience")
        for exp in resume.experience:
            # Company, Location on left - Dates on right
            pdf.set_font("Times", "B", 11)
            company_text = sanitize_unicode_for_pdf(f"{exp.company}, {exp.location}")
            date_text = sanitize_unicode_for_pdf(f"{exp.startDate} — {exp.endDate}")

            # Calculate positions
            date_width = pdf.get_string_width(date_text)
            page_width = pdf.w - pdf.l_margin - pdf.r_margin

            # Draw company on left
            pdf.cell(page_width - date_width, 6, company_text)
            # Draw date on right
            pdf.cell(date_width, 6, date_text, align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            # Role (italic)
            pdf.set_font("Times", "I", 10)
            role_text = sanitize_unicode_for_pdf(exp.role)
            pdf.multi_cell(0, 5, role_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            # Bullets with bold keywords
            line_height = 4.5 if compact_mode else 5
            for bullet in exp.bullets:
                bullet_text = bullet[:500] if len(bullet) > 500 else bullet
                # Ensure bullet ends with a period
                bullet_text = bullet_text.rstrip()
                if bullet_text and not bullet_text.endswith(('.', '!', '?')):
                    bullet_text += '.'
                pdf.set_font("Times", "", 10)
                pdf.cell(3, line_height, "-")  # Bullet point - reduced width
                pdf.write_bullet_with_bold(bullet_text, line_height)

            pdf.ln(1)

    # === EDUCATION ===
    if resume.education:
        pdf.section_header("Education")
        for edu in resume.education:
            # Institution, Location on left - Dates on right
            pdf.set_font("Times", "B", 11)
            inst_text = sanitize_unicode_for_pdf(f"{edu.institution}, {edu.location}")
            date_text = sanitize_unicode_for_pdf(f"{edu.startDate} — {edu.endDate}")

            date_width = pdf.get_string_width(date_text)
            page_width = pdf.w - pdf.l_margin - pdf.r_margin

            pdf.cell(page_width - date_width, 6, inst_text)
            pdf.cell(date_width, 6, date_text, align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            # Degree info
            pdf.set_font("Times", "I", 10)
            degree_text = sanitize_unicode_for_pdf(f"{edu.studyType} in {edu.area}")
            pdf.cell(3, 5, "-")
            pdf.multi_cell(0, 5, degree_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # === PROJECTS ===
    if resume.projects:
        pdf.section_header("Project Work")
        for proj in resume.projects:
            pdf.set_font("Times", "B", 10)
            proj_name = sanitize_unicode_for_pdf(f"  - {proj.name}")
            pdf.multi_cell(0, 5, proj_name, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            # Process description with bold formatting for keywords and metrics
            desc = proj.description[:300] if len(proj.description) > 300 else proj.description
            # Ensure description ends with a period
            desc = desc.rstrip()
            if desc and not desc.endswith(('.', '!', '?')):
                desc += '.'
            desc = sanitize_unicode_for_pdf(desc)
            
            # Apply bold formatting to keywords and metrics in description
            pdf.set_font("Times", "", 10)
            pdf.cell(4, 5, " ")  # Indent
            pdf.write_bullet_with_bold(desc, line_height=5)
            
            # Tech stack with bold keywords
            pdf.set_font("Times", "I", 9)
            pdf.cell(4, 4, " ")  # Indent
            pdf.set_font("Times", "B", 9)
            pdf.cell(12, 4, "Tech: ")
            pdf.set_font("Times", "I", 9)
            tech_stack = sanitize_unicode_for_pdf(proj.techStack)
            pdf.multi_cell(0, 4, tech_stack, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1)

    # === ACHIEVEMENTS ===
    if resume.achievements:
        pdf.section_header("Leadership and Activities")
        for ach in resume.achievements:
            ach_text = ach[:400] if len(ach) > 400 else ach
            # Ensure bullet ends with a period
            ach_text = ach_text.rstrip()
            if ach_text and not ach_text.endswith(('.', '!', '?')):
                ach_text += '.'
            pdf.set_font("Times", "", 10)
            pdf.cell(3, 5, "-")
            pdf.write_bullet_with_bold(ach_text)
    
    # Save
    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir)
    
    pdf.output(output_path)
    return os.path.abspath(output_path)


def generate_pdf_with_page_check(resume, output_dir: str = None, max_attempts: int = 2) -> str:
    """
    Generate PDF with automatic 1-page constraint.
    If the resume exceeds 1 page, it will retry without the summary section.
    
    Args:
        resume: TailoredResume object
        output_dir: Output directory (if None, uses current directory)
        max_attempts: Maximum number of generation attempts
    
    Returns:
        Absolute path to the generated PDF (guaranteed to be 1 page or best effort)
    """
    import tempfile
    
    # Generate filename
    filename = generate_filename(resume.basics.name)
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
    if page_count > 1 and max_attempts >= 2 and resume.summary:
        pdf_path = generate_pdf(resume, output_path, include_summary=False, compact_mode=True)
        page_count = get_pdf_page_count(pdf_path)
        
        if page_count == 1:
            return pdf_path
    
    # Return whatever we have (even if 2 pages, it's the best we could do)
    return pdf_path


def render_and_save_pdf(resume, output_path: str = None, ensure_single_page: bool = True) -> str:
    """
    Render and save PDF with optional single-page guarantee.
    
    Args:
        resume: TailoredResume object
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


def preview_html(resume, output_path: str) -> str:
    html = f"<html><body><h1>{resume.basics.name}</h1></body></html>"
    with open(output_path, 'w') as f:
        f.write(html)
    return os.path.abspath(output_path)
