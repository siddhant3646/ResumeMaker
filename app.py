#!/usr/bin/env python3
"""
Resume Tailor - Streamlit Web Application

A secure web application that takes a Resume (PDF or Text) and a Job Description,
parses the resume into structured JSON using gemma-3-27b-it, then generates a
tailored ATS-friendly resume using Groq API.

Security Features:
- API keys are encrypted and stored in the repository
- Decryption password is stored in Streamlit Cloud secrets
- No plain-text API keys in source code

Hosted on: Streamlit Community Cloud
"""

import base64
import io
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Optional

import pdfplumber
import streamlit as st
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from groq import Groq
from pydantic import BaseModel, Field

# Try to import google-generativeai
try:
    import google.generativeai as genai
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False


# ============================================================================
# Configuration & Security
# ============================================================================

def derive_key_from_password(password: str, salt: bytes) -> bytes:
    """Derive an encryption key from a password using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def decrypt_api_key(encrypted_string: str, password: str) -> str:
    """
    Decrypt an API key using Fernet symmetric encryption.
    
    Args:
        encrypted_string: The encrypted API key string
        password: The password used for encryption
        
    Returns:
        The decrypted API key
    """
    # Decode from base64
    combined = base64.urlsafe_b64decode(encrypted_string.encode())
    # Extract salt (first 16 bytes) and encrypted data
    salt = combined[:16]
    encrypted_data = combined[16:]
    # Derive key and decrypt
    key = derive_key_from_password(password, salt)
    f = Fernet(key)
    return f.decrypt(encrypted_data).decode()


def get_decrypted_api_keys() -> dict[str, Optional[str]]:
    """
    Get decrypted API keys from Streamlit secrets.
    
    Returns:
        Dictionary with 'google' and 'groq' keys containing decrypted API keys
    """
    keys = {
        "google": None,
        "groq": None
    }
    
    try:
        # Get encryption password from secrets
        password = st.secrets.get("ENCRYPTION_PASSWORD")
        if not password:
            st.error("🔐 ENCRYPTION_PASSWORD not found in secrets!")
            return keys
        
        # Decrypt Google API key
        encrypted_google = st.secrets.get("GOOGLE_API_KEY_ENCRYPTED")
        if encrypted_google:
            keys["google"] = decrypt_api_key(encrypted_google, password)
        
        # Decrypt Groq API key
        encrypted_groq = st.secrets.get("GROQ_API_KEY_ENCRYPTED")
        if encrypted_groq:
            keys["groq"] = decrypt_api_key(encrypted_groq, password)
            
    except Exception as e:
        st.error(f"🔐 Decryption error: {e}")
    
    return keys


# ============================================================================
# Pydantic Models - Resume Schema
# ============================================================================

class Basics(BaseModel):
    """Basic contact information"""
    name: str
    email: str
    phone: str
    location: str
    links: list[str] = Field(default_factory=list)


class Education(BaseModel):
    """Education entry"""
    institution: str
    area: str
    studyType: str
    startDate: str
    endDate: str
    location: str


class Experience(BaseModel):
    """Work experience entry"""
    company: str
    location: str
    role: str
    startDate: str
    endDate: str
    bullets: list[str] = Field(default_factory=list)


class Project(BaseModel):
    """Project entry"""
    name: str
    techStack: str
    description: str


class Skills(BaseModel):
    """Categorized skills"""
    languages_frameworks: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)


class ParsedResume(BaseModel):
    """Complete parsed resume structure"""
    basics: Basics
    summary: str
    education: list[Education] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    skills: Skills = Field(default_factory=Skills)
    projects: list[Project] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)


# ============================================================================
# Resume Parsing - Using Google AI Studio (gemma-3-27b-it)
# ============================================================================

PARSING_PROMPT = """You are an expert Resume Parser. Your task is to extract structured information from the provided resume text and return it as a valid JSON object.

## Instructions:

1. Extract all relevant information from the resume text
2. Structure it according to the schema below
3. Return ONLY a valid JSON object - no markdown, no explanations

## Output Schema:

{
  "basics": {
    "name": "Full Name",
    "email": "email@example.com",
    "phone": "+1-xxx-xxx-xxxx",
    "location": "City, State/Country",
    "links": ["https://linkedin.com/in/...", "https://github.com/..."]
  },
  "summary": "Professional summary paragraph",
  "education": [
    {
      "institution": "University Name",
      "area": "Field of Study",
      "studyType": "Degree Type",
      "startDate": "Month Year",
      "endDate": "Month Year or Present",
      "location": "City, Country"
    }
  ],
  "experience": [
    {
      "company": "Company Name",
      "location": "City, Country",
      "role": "Job Title",
      "startDate": "Month Year",
      "endDate": "Month Year or Present",
      "bullets": ["Achievement bullet 1", "Achievement bullet 2", ...]
    }
  ],
  "skills": {
    "languages_frameworks": ["Python", "JavaScript", "React", ...],
    "tools": ["Docker", "AWS", "Git", ...]
  },
  "projects": [
    {
      "name": "Project Name",
      "techStack": "Technologies used",
      "description": "Brief description"
    }
  ],
  "achievements": ["Achievement 1", "Award 1", ...]
}

## Important Rules:

1. Extract ALL work experience entries with complete bullet points
2. Parse the professional summary accurately
3. Split skills into languages/frameworks vs tools/platforms
4. Include ALL projects mentioned
5. Extract ALL achievements, awards, certifications
6. Preserve dates exactly as they appear
7. Use empty arrays [] if a section is not present
8. Return ONLY valid JSON - no markdown code blocks, no additional text

---

## Resume Text:

{resume_text}

---

Return the structured JSON:"""


def parse_resume_with_gemma(
    resume_text: str, 
    api_key: str
) -> ParsedResume:
    """
    Parse resume text into structured JSON using gemma-3-27b-it via Google AI Studio.
    
    Args:
        resume_text: The text extracted from the resume
        api_key: Google AI Studio API key
        
    Returns:
        ParsedResume object with structured data
    """
    if not GOOGLE_GENAI_AVAILABLE:
        raise ImportError("google-generativeai library not available")
    
    # Configure the API
    genai.configure(api_key=api_key)
    
    # Use gemma-3-27b-it model
    model = genai.GenerativeModel("gemma-3-27b-it")
    
    # Build the prompt
    prompt = PARSING_PROMPT.format(resume_text=resume_text)
    
    # Generate response
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.1,
            max_output_tokens=8192,
        )
    )
    
    if not response.text:
        raise ValueError("Empty response from parsing API")
    
    # Clean up response text
    response_text = response.text.strip()
    
    # Remove markdown code blocks if present
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    elif response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    response_text = response_text.strip()
    
    # Parse JSON into Pydantic model
    try:
        parsed_data = json.loads(response_text)
        return ParsedResume(**parsed_data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse API response as JSON: {e}")
    except Exception as e:
        raise ValueError(f"Failed to validate response schema: {e}")


# ============================================================================
# Resume Tailoring - Using Groq
# ============================================================================

TAILORING_PROMPT = """You are a SENIOR TECHNICAL RECRUITER and EXPERT RESUME WRITER with 15+ years of experience hiring for Fortune 500 companies. You are an expert in ATS systems and what makes senior hiring managers say "Let's interview this person."

---

## CRITICAL RULES (FOLLOW EXACTLY)

### RULE 1: DIVERSE METRICS (NOT JUST PERCENTAGES)
NEVER rely only on percentages. Mix different metric types for credibility.

**AVOID: Percentage-only metrics (looks like guessing)**
- ❌ BAD: "Improved performance by 40%"
- ❌ BAD: "Reduced errors by 25%"

**USE DIVERSE METRIC TYPES:**

**Time-Based:**
- "Reduced P99 latency from 400ms to 280ms"
- "Cut deployment time from 45 minutes to 8 minutes"
- "Achieved sub-200ms response times"

**Scale/Volume:**
- "Processing 2M+ daily transactions"
- "Serving 50K concurrent users"
- "Handling 10K requests/second"

**Counts:**
- "Resolved 80+ user stories and 35 complex defects"
- "Built 15 new microservices"
- "Mentored 5 junior developers"

**Quality/Reliability:**
- "Achieved 99.97% uptime across 15 services"
- "Maintained zero security incidents for 18 months"

### RULE 2: HIGHLIGHT SECURITY ACHIEVEMENTS PROMINENTLY
Feature security credentials prominently in summary and achievements.

### RULE 3: PROJECTS = ENGINEERING CHALLENGES
Focus on engineering challenges: edge deployment, data pipelines, optimization, NOT just ML accuracy.

### RULE 4: POWER VERBS
- "Contributed to" → "Authored" or "Designed"
- "Participated in" → "Led" or "Drove"
- "Helped with" → "Spearheaded" or "Orchestrated"
- "Worked on" → "Engineered" or "Architected"

**STRONG VERBS:**
- Architecture: Architected, Designed, Authored, Engineered
- Optimization: Optimized, Reduced, Slashed, Accelerated
- Leadership: Spearheaded, Championed, Pioneered, Directed
- Security: Hardened, Secured, Remediated, Fortified

### RULE 5: EXPERIENCE BULLETS
Start each bullet directly with a strong action verb. NO category headers.

**CORRECT FORMAT:**
"[Power Verb] + [specific achievement] + [technology used] + [quantified result]"

---

## OUTPUT REQUIREMENTS

### Professional Summary (3 Sentences)
1. Years of experience + core tech stack matching JD
2. Biggest SPECIFIC achievement (with precise metrics)
3. Key differentiator (security expertise, mentorship, system design)

### Skills (MUST be an object with two keys)
```json
"skills": {{
  "languages_frameworks": ["Skill1", "Skill2"],
  "tools": ["Tool1", "Tool2"]
}}
```

### Experience (8-10 bullets per role - FIT ON 1 PAGE)
**CRITICAL: Must fit on exactly 1 page.**

**CRITICAL: Preserve startDate and endDate EXACTLY as in input.**

Each bullet must include:
1. Start with POWER VERB
2. SPECIFIC metric (latency, throughput, error rate)
3. Technology and method used
4. Absolute number + percentage where applicable

### Projects (1-2 bullets each)
Focus on engineering challenges, not just model accuracy.

### Achievements (3 items only)
- Security achievements FIRST
- Best Performer / Awards  
- Leadership roles

---

## 1-PAGE CONSTRAINT
**The resume MUST fit on exactly 1 page. NO spillover to page 2.**

---

## Input Master Resume (JSON):

```json
{master_resume_json}
```

## Job Description:

{job_description}

---

## Output Format:
Return a JSON object matching the TailoredResume schema exactly.

Return ONLY valid JSON, no markdown code blocks, no explanations."""


def tailor_resume_with_groq(
    master_resume: dict,
    job_description: str,
    api_key: str
) -> Generator[str, None, None]:
    """
    Tailor resume based on job description using Groq API.
    
    Args:
        master_resume: The parsed resume as a dictionary
        job_description: The job description text
        api_key: Groq API key
        
    Yields:
        Chunks of the generated response
    """
    client = Groq(api_key=api_key)
    
    # Build the prompt
    prompt = TAILORING_PROMPT.format(
        master_resume_json=json.dumps(master_resume, indent=2),
        job_description=job_description
    )
    
    # Create completion with the exact structure requested
    completion = client.chat.completions.create(
        model="groq/compound",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=1,
        max_completion_tokens=1024,
        top_p=1,
        stream=True,
        stop=None,
        compound_custom={"tools":{"enabled_tools":["web_search","code_interpreter","visit_website"]}}
    )
    
    # Handle streaming response
    for chunk in completion:
        yield chunk.choices[0].delta.content or ""


def parse_tailored_response(response_text: str) -> ParsedResume:
    """
    Parse the Groq response into a ParsedResume object.
    
    Args:
        response_text: The full text response from Groq
        
    Returns:
        ParsedResume object
    """
    # Clean up response text
    text = response_text.strip()
    
    # Remove markdown code blocks if present
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    
    # Parse JSON into Pydantic model
    try:
        parsed_data = json.loads(text)
        return ParsedResume(**parsed_data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse tailored response as JSON: {e}")
    except Exception as e:
        raise ValueError(f"Failed to validate tailored response: {e}")


# ============================================================================
# PDF Generation
# ============================================================================

BLACK = (0, 0, 0)
GRAY = (80, 80, 80)


class ResumePDF(FPDF):
    """PDF generator for ATS-friendly resumes."""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        
    def section_header(self, title: str):
        """Draw a section header with underline."""
        self.set_font("Times", "B", 11)
        self.set_text_color(*BLACK)
        self.multi_cell(0, 6, title.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*BLACK)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.set_text_color(*BLACK)
        self.ln(1)
    
    def add_header_info(self, basics: Basics):
        """Add name and contact information header."""
        # Name - centered and bold
        self.set_font("Times", "B", 14)
        self.set_text_color(*BLACK)
        self.cell(0, 8, basics.name, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Contact info - centered on one line
        self.set_font("Times", "", 9)
        contact_parts = [basics.email, basics.phone, basics.location]
        if basics.links:
            contact_parts.extend(basics.links[:2])  # Limit to first 2 links
        
        contact_line = " | ".join(filter(None, contact_parts))
        self.cell(0, 5, contact_line, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)
    
    def add_summary(self, summary: str):
        """Add professional summary section."""
        self.section_header("Professional Summary")
        self.set_font("Times", "", 10)
        self.set_text_color(*BLACK)
        self.multi_cell(0, 5, summary, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)
    
    def add_skills(self, skills: Skills):
        """Add skills section."""
        self.section_header("Technical Skills")
        self.set_font("Times", "", 10)
        self.set_text_color(*BLACK)
        
        if skills.languages_frameworks:
            self.set_font("Times", "B", 10)
            self.cell(0, 5, "Languages & Frameworks: ", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_font("Times", "", 10)
            self.multi_cell(0, 5, ", ".join(skills.languages_frameworks), 
                          new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        if skills.tools:
            self.set_font("Times", "B", 10)
            self.cell(0, 5, "Tools & Platforms: ", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_font("Times", "", 10)
            self.multi_cell(0, 5, ", ".join(skills.tools), 
                          new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        self.ln(2)
    
    def add_experience(self, experiences: list[Experience]):
        """Add work experience section."""
        self.section_header("Professional Experience")
        
        for exp in experiences:
            # Company and Role
            self.set_font("Times", "B", 10)
            self.set_text_color(*BLACK)
            self.cell(0, 5, f"{exp.role}", new_x=XPos.RIGHT, new_y=YPos.LAST)
            
            # Date on the right
            date_str = f"{exp.startDate} - {exp.endDate}"
            self.cell(0, 5, date_str, align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            # Company and Location
            self.set_font("Times", "I", 10)
            self.set_text_color(*GRAY)
            self.cell(0, 5, f"{exp.company} | {exp.location}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(1)
            
            # Bullets
            self.set_font("Times", "", 10)
            self.set_text_color(*BLACK)
            for bullet in exp.bullets:
                # Add bullet character
                x = self.get_x()
                y = self.get_y()
                self.set_xy(x + 3, y)
                self.cell(3, 5, chr(149), new_x=XPos.RIGHT, new_y=YPos.LAST)
                
                # Bullet text with proper wrapping
                self.multi_cell(0, 5, bullet, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            self.ln(2)
    
    def add_education(self, education: list[Education]):
        """Add education section."""
        self.section_header("Education")
        
        for edu in education:
            # Degree and Field
            self.set_font("Times", "B", 10)
            self.set_text_color(*BLACK)
            self.cell(0, 5, f"{edu.studyType} in {edu.area}", 
                     new_x=XPos.RIGHT, new_y=YPos.LAST)
            
            # Date on right
            date_str = f"{edu.startDate} - {edu.endDate}"
            self.cell(0, 5, date_str, align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            # Institution and Location
            self.set_font("Times", "I", 10)
            self.set_text_color(*GRAY)
            self.cell(0, 5, f"{edu.institution} | {edu.location}", 
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(1)
    
    def add_projects(self, projects: list[Project]):
        """Add projects section."""
        self.section_header("Projects")
        
        for proj in projects:
            # Project name
            self.set_font("Times", "B", 10)
            self.set_text_color(*BLACK)
            self.cell(0, 5, proj.name, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            # Tech stack
            self.set_font("Times", "I", 9)
            self.set_text_color(*GRAY)
            self.cell(0, 4, f"Tech Stack: {proj.techStack}", 
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            # Description
            self.set_font("Times", "", 10)
            self.set_text_color(*BLACK)
            self.multi_cell(0, 5, proj.description, 
                          new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(1)
    
    def add_achievements(self, achievements: list[str]):
        """Add achievements section."""
        self.section_header("Achievements")
        
        self.set_font("Times", "", 10)
        self.set_text_color(*BLACK)
        
        for achievement in achievements:
            x = self.get_x()
            y = self.get_y()
            self.set_xy(x + 3, y)
            self.cell(3, 5, chr(149), new_x=XPos.RIGHT, new_y=YPos.LAST)
            self.multi_cell(0, 5, achievement, new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def generate_resume_pdf(resume_data: ParsedResume) -> bytes:
    """
    Generate an ATS-friendly PDF resume from parsed resume data.
    
    Args:
        resume_data: ParsedResume object with all resume information
        
    Returns:
        PDF as bytes
    """
    pdf = ResumePDF()
    pdf.add_page()
    
    # Add all sections
    pdf.add_header_info(resume_data.basics)
    pdf.add_summary(resume_data.summary)
    pdf.add_skills(resume_data.skills)
    
    if resume_data.experience:
        pdf.add_experience(resume_data.experience)
    
    if resume_data.projects:
        pdf.add_projects(resume_data.projects)
    
    if resume_data.education:
        pdf.add_education(resume_data.education)
    
    if resume_data.achievements:
        pdf.add_achievements(resume_data.achievements)
    
    # Output to bytes
    return pdf.output()


# ============================================================================
# File Extraction
# ============================================================================

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from a PDF file using pdfplumber.
    
    Args:
        file_bytes: PDF file content as bytes
        
    Returns:
        Extracted text content
    """
    text_parts = []
    
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    
    return "\n\n".join(text_parts)


# ============================================================================
# Streamlit UI
# ============================================================================

def init_session_state():
    """Initialize Streamlit session state variables."""
    if 'parsed_resume' not in st.session_state:
        st.session_state.parsed_resume = None
    if 'tailored_resume' not in st.session_state:
        st.session_state.tailored_resume = None
    if 'tailored_response_text' not in st.session_state:
        st.session_state.tailored_response_text = ""
    if 'step' not in st.session_state:
        st.session_state.step = 1


def sanitize_filename(name: str) -> str:
    """Sanitize a string to be used as a filename."""
    sanitized = re.sub(r'[<>:"/\\|?*]', '', name)
    sanitized = sanitized.replace(' ', '_')
    return sanitized[:50]


def main():
    """Main Streamlit application."""
    init_session_state()
    
    # Page configuration
    st.set_page_config(
        page_title="Resume Tailor",
        page_icon="",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Header
    st.title(" Resume Tailor")
    st.markdown("AI-Powered Resume Customization for ATS Success")
    st.markdown("---")
    
    # Get API keys (decrypted from secrets)
    api_keys = get_decrypted_api_keys()
    
    # Check if keys are available
    if not api_keys["google"] or not api_keys["groq"]:
        st.error("🔐 API keys not configured properly!")
        st.info("""
        Please configure your secrets in Streamlit Cloud:
        1. Go to https://share.streamlit.io/
        2. Find your app and click 'Settings'
        3. Go to 'Secrets' section
        4. Add these secrets:
           - ENCRYPTION_PASSWORD: (your password)
           - GOOGLE_API_KEY_ENCRYPTED: (encrypted Google AI key)
           - GROQ_API_KEY_ENCRYPTED: (encrypted Groq key)
        
        Use `python encrypt_keys.py` to generate encrypted keys.
        """)
        st.stop()
    
    # Step 1: Upload Resume
    st.header("Step 1: Upload Your Resume")
    
    resume_input_method = st.radio(
        "How would you like to provide your resume?",
        ["Upload PDF", "Paste Text"],
        horizontal=True
    )
    
    resume_text = ""
    
    if resume_input_method == "Upload PDF":
        uploaded_file = st.file_uploader(
            "Upload your resume (PDF)",
            type=["pdf"],
            help="Upload your master resume as a PDF file"
        )
        
        if uploaded_file:
            try:
                with st.spinner("📄 Extracting text from PDF..."):
                    file_bytes = uploaded_file.read()
                    resume_text = extract_text_from_pdf(file_bytes)
                    
                if resume_text:
                    st.success(f"✅ Extracted {len(resume_text)} characters from PDF")
                    with st.expander("Preview extracted text"):
                        st.text(resume_text[:1000] + "..." if len(resume_text) > 1000 else resume_text)
                else:
                    st.error("❌ Could not extract text from PDF. Please try pasting the text instead.")
            except Exception as e:
                st.error(f"❌ Error extracting PDF: {e}")
    else:
        resume_text = st.text_area(
            "Paste your resume text here",
            height=300,
            placeholder="Paste the full text of your resume here..."
        )
    
    st.markdown("---")
    
    # Step 2: Job Description
    st.header("Step 2: Paste Job Description")
    
    job_description = st.text_area(
        "Job Description",
        height=250,
        placeholder="Paste the job description here...",
        help="This will be used to tailor your resume to the specific job requirements"
    )
    
    st.markdown("---")
    
    # Step 3: Generate
    st.header("Step 3: Generate Tailored Resume")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        generate_button = st.button(
            "🚀 Generate Tailored Resume",
            type="primary",
            use_container_width=True,
            disabled=not (resume_text and job_description and len(job_description) > 50)
        )
    
    # Initialize variables for scope
    tailored_resume = None
    
    if generate_button:
        if not resume_text:
            st.error("❌ Please provide your resume first!")
            st.stop()
        
        if len(job_description) < 50:
            st.error("❌ Job description is too short. Please provide a complete job description.")
            st.stop()
        
        try:
            # Step 1: Parse Resume with Gemma
            st.subheader("Step 1: Parsing Resume")
            with st.spinner("🤖 Parsing your resume with gemma-3-27b-it..."):
                st.session_state.parsed_resume = parse_resume_with_gemma(
                    resume_text=resume_text,
                    api_key=api_keys["google"]
                )
            
            parsed = st.session_state.parsed_resume
            st.success(f"✅ Parsed resume for: {parsed.basics.name}")
            st.info(f"📊 Found: {len(parsed.experience)} experience entries, "
                   f"{len(parsed.projects)} projects, "
                   f"{len(parsed.education)} education entries")
            
            # Step 2: Tailor Resume with Groq
            st.subheader("Step 2: Tailoring for Job Description")
            
            response_container = st.empty()
            full_response = []
            
            with st.spinner("🎯 Tailoring resume with Groq compound model..."):
                # Convert Pydantic model to dict for JSON serialization
                master_resume_dict = parsed.model_dump()
                
                # Stream the response
                for chunk in tailor_resume_with_groq(
                    master_resume=master_resume_dict,
                    job_description=job_description,
                    api_key=api_keys["groq"]
                ):
                    full_response.append(chunk)
                    # Update display with accumulated response
                    if len(full_response) % 20 == 0:  # Update every 20 chunks
                        response_container.code("".join(full_response), language="json")
            
            # Final display
            st.session_state.tailored_response_text = "".join(full_response)
            response_container.empty()
            
            # Parse the tailored response
            st.session_state.tailored_resume = parse_tailored_response(
                st.session_state.tailored_response_text
            )
            tailored_resume = st.session_state.tailored_resume
            
            st.success("✅ Resume tailored successfully!")
            
            # Move to next step
            st.session_state.step = 2
            
        except Exception as e:
            st.error(f"❌ Error during generation: {e}")
            st.exception(e)
            st.stop()
    
    # Display Results
    if st.session_state.tailored_resume:
        st.markdown("---")
        st.header(" Tailored Resume Results")
        
        tailored_resume = st.session_state.tailored_resume
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["📄 Preview", "📋 JSON", "💾 Download"])
        
        with tab1:
            # Display basic info
            st.subheader(tailored_resume.basics.name)
            st.caption(f"{tailored_resume.basics.email} | {tailored_resume.basics.phone} | {tailored_resume.basics.location}")
            
            # Summary
            st.markdown("**Professional Summary**")
            st.write(tailored_resume.summary)
            
            # Experience
            if tailored_resume.experience:
                st.markdown("**Experience**")
                for exp in tailored_resume.experience[:3]:  # Show first 3
                    with st.container():
                        st.markdown(f"**{exp.role}** at {exp.company} ({exp.startDate} - {exp.endDate})")
                        for bullet in exp.bullets[:3]:  # Show first 3 bullets
                            st.markdown(f"- {bullet}")
            
            # Skills
            if tailored_resume.skills:
                st.markdown("**Skills**")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("*Languages & Frameworks:*")
                    st.write(", ".join(tailored_resume.skills.languages_frameworks[:10]))
                with col2:
                    st.markdown("*Tools:*")
                    st.write(", ".join(tailored_resume.skills.tools[:10]))
        
        with tab2:
            # Show JSON
            st.json(tailored_resume.model_dump())
        
        with tab3:
            # Generate and offer PDF download
            st.subheader("Download Tailored Resume")
            
            try:
                pdf_bytes = generate_resume_pdf(tailored_resume)
                
                # Generate filename
                company_name = "Company"
                # Try to extract company from JD
                jd_lower = job_description.lower()
                company_matches = [
                    "google", "microsoft", "amazon", "apple", "meta", "facebook",
                    "netflix", "uber", "airbnb", "linkedin", "twitter", "salesforce",
                    "oracle", "ibm", "intel", "nvidia", "adobe", "spotify"
                ]
                for company in company_matches:
                    if company in jd_lower:
                        company_name = company.title()
                        break
                
                filename = f"Resume_{sanitize_filename(tailored_resume.basics.name)}_{sanitize_filename(company_name)}_{datetime.now().strftime('%Y%m%d')}.pdf"
                
                st.download_button(
                    label="📥 Download Resume PDF",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True
                )
                
                # Also offer JSON download
                json_bytes = json.dumps(tailored_resume.model_dump(), indent=2).encode()
                st.download_button(
                    label="📥 Download JSON Data",
                    data=json_bytes,
                    file_name=filename.replace(".pdf", ".json"),
                    mime="application/json",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"Error generating PDF: {e}")
    
    # Footer
    st.markdown("---")
    st.caption("🔒 Secure Resume Tailoring | Your data is processed securely and not stored permanently.")


if __name__ == "__main__":
    main()
