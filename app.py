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
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Optional, Union

import pdfplumber
import streamlit as st
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from pydantic import BaseModel, Field

# Try to import google-generativeai
try:
    import google.generativeai as genai
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False


# ============================================================================
# Model Router - Tiered Fallback System with Daily Counters
# ============================================================================

class ModelRouter:
    """
    Manages tiered model selection with daily request counters.
    
    Tier 1: gemini-2.0-flash (20 requests/day)
    Tier 2: gemini-2.5-flash-preview-05-06 (20 requests/day)
    Tier 3: gemini-2.5-flash-lite-preview-06-17 (20 requests/day)
    Tier 4: gemma-3-27b-it (unlimited)
    
    Counters reset at midnight UTC daily.
    """
    
    # Model configuration
    MODELS = [
        {"name": "gemini-2.0-flash", "limit": 20, "tier": 1},
        {"name": "gemini-2.5-flash-preview-05-06", "limit": 20, "tier": 2},
        {"name": "gemini-2.5-flash-lite-preview-06-17", "limit": 20, "tier": 3},
        {"name": "gemma-3-27b-it", "limit": float('inf'), "tier": 4},  # Unlimited
    ]
    
    def __init__(self):
        """Initialize or load counters from session state."""
        self._init_counters()
    
    def _init_counters(self):
        """Initialize counters in session state if not present."""
        # Check if we need to reset (new day in UTC)
        current_date = datetime.utcnow().strftime("%Y-%m-%d")
        
        if 'model_router_date' not in st.session_state:
            st.session_state.model_router_date = current_date
        
        # Reset counters if it's a new day
        if st.session_state.model_router_date != current_date:
            st.session_state.model_router_date = current_date
            for model in self.MODELS:
                st.session_state[f"model_counter_{model['name']}"] = 0
        
        # Initialize counters if not present
        for model in self.MODELS:
            key = f"model_counter_{model['name']}"
            if key not in st.session_state:
                st.session_state[key] = 0
    
    def get_model_for_request(self) -> str:
        """
        Get the appropriate model based on daily usage counters.
        
        Returns:
            Model name to use for the request
        """
        self._init_counters()  # Ensure counters are fresh
        
        for model in self.MODELS:
            counter_key = f"model_counter_{model['name']}"
            current_count = st.session_state.get(counter_key, 0)
            
            if current_count < model['limit']:
                # Increment counter and return this model
                st.session_state[counter_key] = current_count + 1
                return model['name']
        
        # Fallback to last model (gemma-3-27b-it) which has unlimited usage
        # Still increment counter for tracking
        counter_key = f"model_counter_{self.MODELS[-1]['name']}"
        st.session_state[counter_key] = st.session_state.get(counter_key, 0) + 1
        return self.MODELS[-1]['name']
    
    def get_current_tier_info(self) -> dict:
        """
        Get information about current tier usage.
        
        Returns:
            Dictionary with tier information
        """
        self._init_counters()
        
        info = []
        for model in self.MODELS:
            counter_key = f"model_counter_{model['name']}"
            count = st.session_state.get(counter_key, 0)
            limit = model['limit'] if model['limit'] != float('inf') else '∞'
            percentage = (count / model['limit'] * 100) if model['limit'] != float('inf') else 0
            
            info.append({
                'tier': model['tier'],
                'model': model['name'],
                'used': count,
                'limit': limit,
                'percentage': percentage,
                'active': count < model['limit'] if model['limit'] != float('inf') else True
            })
        
        return info
    
    def reset_counters(self):
        """Manually reset all counters (for testing)."""
        current_date = datetime.utcnow().strftime("%Y-%m-%d")
        st.session_state.model_router_date = current_date
        for model in self.MODELS:
            st.session_state[f"model_counter_{model['name']}"] = 0


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
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    links: list[str] = Field(default_factory=list)


class Education(BaseModel):
    """Education entry"""
    institution: str = ""
    area: str = ""
    studyType: str = ""
    startDate: str = ""
    endDate: str = ""
    location: str = ""


class Experience(BaseModel):
    """Work experience entry"""
    company: str = ""
    location: str = ""
    role: str = ""
    startDate: str = ""
    endDate: str = ""
    bullets: list[str] = Field(default_factory=list)


class Project(BaseModel):
    """Project entry"""
    name: str = ""
    techStack: str = ""
    description: str = ""


class Skills(BaseModel):
    """Categorized skills"""
    languages_frameworks: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)


class ParsedResume(BaseModel):
    """Complete parsed resume structure"""
    basics: Basics = Field(default_factory=Basics)
    summary: str = ""
    education: list[Education] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    skills: Skills = Field(default_factory=Skills)
    projects: list[Project] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)


# ============================================================================
# Resume Parsing - Using Google AI Studio (gemma-3-27b-it)
# ============================================================================

PARSING_PROMPT = """Extract structured information from this resume and return as JSON.

Required JSON structure:
{
  "basics": {
    "name": "",
    "email": "",
    "phone": "",
    "location": "",
    "links": []
  },
  "summary": "",
  "education": [],
  "experience": [],
  "skills": {
    "languages_frameworks": [],
    "tools": []
  },
  "projects": [],
  "achievements": []
}

Rules:
- Extract name, email, phone, location, links into basics
- Put professional summary text in summary
- List each education entry with institution, area, studyType, startDate, endDate, location
- List each job in experience with company, location, role, startDate, endDate, bullets array
- Split skills: programming languages/frameworks vs tools/platforms
- List each project with name, techStack, description
- List achievements as strings
- Use empty strings "" or empty arrays [] for missing data
- Return ONLY valid JSON, no markdown, no explanations

Resume Text:
{resume_text}

JSON output:"""


def parse_resume_with_gemma(
    resume_text: str,
    api_key: str,
    max_retries: int = 3,
    retry_delay: float = 2.0
) -> ParsedResume:
    """
    Parse resume text into structured JSON using gemma-3-12b-it via Google AI Studio.
    Includes retry logic for handling transient failures and rate limits (429 errors).
    
    Args:
        resume_text: The text extracted from the resume
        api_key: Google AI Studio API key
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delay: Initial delay between retries in seconds (default: 2.0)
        
    Returns:
        ParsedResume object with structured data
        
    Raises:
        ValueError: If all retry attempts fail
    """
    if not GOOGLE_GENAI_AVAILABLE:
        raise ImportError("google-generativeai library not available")
    
    # Configure the API
    genai.configure(api_key=api_key)
    
    # Use gemma-3-12b-it model for parsing (lighter, faster)
    model = genai.GenerativeModel("gemma-3-12b-it")
    
    # Build the prompt
    # Use replace() instead of format() to avoid issues with curly braces in resume text
    prompt = PARSING_PROMPT.replace("{resume_text}", resume_text)
    
    last_error = None
    last_response_text = ""
    
    for attempt in range(max_retries):
        try:
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
            last_response_text = response_text
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            elif response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON into dict first
            parsed_data = json.loads(response_text)
            
            # Fix projects techStack - convert list to string if needed
            if 'projects' in parsed_data and isinstance(parsed_data['projects'], list):
                for project in parsed_data['projects']:
                    if isinstance(project, dict) and 'techStack' in project:
                        if isinstance(project['techStack'], list):
                            project['techStack'] = ', '.join(project['techStack'])
            
            # Now validate with Pydantic
            parsed_resume = ParsedResume(**parsed_data)
            
            # Success! Return the parsed resume
            if attempt > 0:
                print(f"✅ Successfully parsed resume after {attempt + 1} attempts")
            return parsed_resume
            
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            
            # Check for rate limit (429) or quota errors
            is_rate_limit = any(x in error_str for x in ['429', 'rate limit', 'quota', 'resource exhausted'])
            
            if attempt < max_retries - 1:
                # Calculate exponential backoff delay
                current_delay = retry_delay * (2 ** attempt)
                if is_rate_limit:
                    current_delay *= 2  # Extra delay for rate limits
                    print(f"⚠️ Rate limit hit (429). Waiting longer...")
                print(f"⚠️ Attempt {attempt + 1}/{max_retries} failed: {str(e)[:100]}...")
                print(f"   Retrying in {current_delay:.1f} seconds...")
                time.sleep(current_delay)
            else:
                # All retries exhausted
                break
    
    # All retries failed
    error_msg = f"Failed to parse resume after {max_retries} attempts.\n"
    error_msg += f"Last error: {last_error}\n"
    error_msg += f"Last response:\n{last_response_text[:1000]}"
    raise ValueError(error_msg)


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
Return a JSON object with this EXACT structure:

```json
{
  "basics": {
    "name": "Full Name",
    "email": "email@example.com",
    "phone": "+1-xxx-xxx-xxxx",
    "location": "City, Country",
    "links": ["https://linkedin.com/in/...", "https://github.com/..."]
  },
  "summary": "Professional summary paragraph (3 sentences)",
  "education": [
    {
      "institution": "University Name",
      "area": "Field of Study",
      "studyType": "Degree",
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
      "bullets": [
        "Power verb + specific achievement + technology + quantified result",
        "Another achievement bullet with metrics"
      ]
    }
  ],
  "skills": {
    "languages_frameworks": ["Skill1", "Skill2"],
    "tools": ["Tool1", "Tool2"]
  },
  "projects": [
    {
      "name": "Project Name",
      "techStack": "Technologies used (comma separated)",
      "description": "Brief description"
    }
  ],
  "achievements": ["Achievement 1", "Achievement 2", "Achievement 3"]
}
```

**CRITICAL RULES:**
1. Experience MUST be an array of OBJECTS (not strings)
2. Each experience object MUST have: company, location, role, startDate, endDate, bullets
3. Bullets must be an array of strings
4. Preserve dates from input EXACTLY as they appear
5. Return ONLY valid JSON, no markdown code blocks, no explanations."""


def tailor_resume_with_model_router(
    master_resume: dict,
    job_description: str,
    api_key: str,
    model_router: ModelRouter,
    max_retries: int = 3,
    retry_delay: float = 2.0
) -> tuple[str, str]:
    """
    Tailor resume using tiered model selection via ModelRouter.
    Includes retry logic for handling transient failures and rate limits (429 errors).
    
    Args:
        master_resume: The parsed resume as a dictionary
        job_description: The job description text
        api_key: Google AI Studio API key
        model_router: ModelRouter instance for tiered selection
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delay: Initial delay between retries in seconds (default: 2.0)
        
    Returns:
        Tuple of (response_text, model_name_used)
        
    Raises:
        ValueError: If all retry attempts fail
    """
    if not GOOGLE_GENAI_AVAILABLE:
        raise ImportError("google-generativeai library not available")
    
    # Configure the API
    genai.configure(api_key=api_key)
    
    # Build the prompt
    master_resume_json_str = json.dumps(master_resume, indent=2)
    prompt = TAILORING_PROMPT.replace("{master_resume_json}", master_resume_json_str)
    prompt = prompt.replace("{job_description}", job_description)
    
    last_error = None
    model_name = None
    
    for attempt in range(max_retries):
        try:
            # Get model from router (only on first attempt or after certain errors)
            if attempt == 0 or model_name is None:
                model_name = model_router.get_model_for_request()
                print(f"🤖 Using model: {model_name}")
            
            # Create model instance
            model = genai.GenerativeModel(model_name)
            
            # Generate response
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=8192,
                )
            )
            
            if not response.text:
                raise ValueError("Empty response from tailoring API")
            
            # Success! Return the response text and model name
            if attempt > 0:
                print(f"✅ Successfully tailored resume after {attempt + 1} attempts")
            return response.text, model_name
            
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            
            # Check for rate limit (429) or quota errors
            is_rate_limit = any(x in error_str for x in ['429', 'rate limit', 'quota', 'resource exhausted'])
            is_quota_exceeded = 'quota exceeded' in error_str or 'limit: 0' in error_str
            
            if attempt < max_retries - 1:
                # Calculate exponential backoff delay
                current_delay = retry_delay * (2 ** attempt)
                
                if is_quota_exceeded:
                    # All Gemini models share the same quota on free tier
                    # Skip directly to Gemma 3 27B (unlimited)
                    print(f"⚠️ Quota exceeded for {model_name}. Skipping to Gemma 3 27B...")
                    model_name = "gemma-3-27b-it"
                    # Mark all Gemini tiers as exhausted
                    for m in model_router.MODELS[:3]:  # First 3 are Gemini models
                        st.session_state[f"model_counter_{m['name']}"] = m['limit']
                elif is_rate_limit:
                    current_delay *= 2  # Extra delay for rate limits
                    print(f"⚠️ Rate limit hit (429). Waiting longer...")
                    # Try next tier model on rate limit
                    model_name = None  # Force model router to select next tier
                    
                print(f"⚠️ Tailoring attempt {attempt + 1}/{max_retries} failed: {str(e)[:100]}...")
                print(f"   Retrying in {current_delay:.1f} seconds...")
                time.sleep(current_delay)
            else:
                # All retries exhausted
                break
    
    # All retries failed
    raise ValueError(f"Failed to tailor resume after {max_retries} attempts. Last error: {last_error}")


def parse_tailored_response(response_text: str) -> ParsedResume:
    """
    Parse the Groq response into a ParsedResume object.
    
    Args:
        response_text: The full text response from Groq
        
    Returns:
        ParsedResume object
        
    Raises:
        ValueError: If response is empty or invalid JSON
    """
    # Check for empty response
    if not response_text or not response_text.strip():
        raise ValueError("Empty response from Groq API. The model may have failed to generate output.")
    
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
    
    # Check again after cleaning
    if not text:
        raise ValueError("Empty response from Groq API after cleaning markdown.")
    
    # Parse JSON into dict first
    try:
        parsed_data = json.loads(text)
        
        # Fix projects techStack - convert list to string if needed
        if 'projects' in parsed_data and isinstance(parsed_data['projects'], list):
            for project in parsed_data['projects']:
                if isinstance(project, dict) and 'techStack' in project:
                    if isinstance(project['techStack'], list):
                        project['techStack'] = ', '.join(project['techStack'])
        
        return ParsedResume(**parsed_data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse tailored response as JSON: {e}\n\nResponse text:\n{text[:500]}")
    except Exception as e:
        raise ValueError(f"Failed to validate tailored response: {e}\n\nResponse text:\n{text[:500]}")


# ============================================================================
# PDF Generation
# ============================================================================

BLACK = (0, 0, 0)
GRAY = (80, 80, 80)
ASSETS_DIR = Path(__file__).parent / "assets"


class ResumePDF(FPDF):
    """PDF generator for ATS-friendly resumes."""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
    
    def sanitize_text(self, text: str) -> str:
        """
        Sanitize text for PDF output by replacing unsupported Unicode characters.
        
        Args:
            text: Input text that may contain Unicode characters
            
        Returns:
            Sanitized text with ASCII-compatible characters
        """
        if not text:
            return ""
        
        # Replace smart quotes and other common Unicode characters
        replacements = {
            '"': '"',  # Left double quote
            '"': '"',  # Right double quote
            ''': "'",   # Left single quote
            ''': "'",   # Right single quote
            '—': '-',   # Em dash
            '–': '-',   # En dash
            '…': '...', # Ellipsis
            '•': '*',   # Bullet (will use ASCII alternative)
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remove any other non-ASCII characters
        return text.encode('ascii', 'ignore').decode('ascii')
        
    def section_header(self, title: str):
        """Draw a section header with underline."""
        self.set_font("Times", "B", 11)
        self.set_text_color(*BLACK)
        self.multi_cell(0, 6, self.sanitize_text(title.upper()), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*BLACK)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.set_text_color(*BLACK)
        self.ln(1)
    
    def add_header_info(self, basics: Basics):
        """Add name and contact information header with icons."""
        # Name - centered and bold
        self.set_font("Times", "B", 14)
        self.set_text_color(*BLACK)
        self.cell(0, 8, self.sanitize_text(basics.name), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Contact info with icons
        icon_size = 3.5
        gap = 1.5
        separator = " | "
        
        self.set_font("Times", "", 9)
        
        # Build contact items with icons
        items = []
        
        # Email with icon
        if basics.email:
            items.append(("email.png", basics.email))
        
        # Phone with icon
        if basics.phone:
            items.append(("phone.png", basics.phone))
        
        # Location (no icon)
        if basics.location:
            items.append((None, basics.location))
        
        # Links with icons
        for link in basics.links[:2]:
            clean_link = link.replace("https://", "").replace("http://", "")
            if "github" in link.lower() and (ASSETS_DIR / "github.png").exists():
                items.append(("github.png", clean_link))
            elif "linkedin" in link.lower() and (ASSETS_DIR / "linkedin.png").exists():
                items.append(("linkedin.png", clean_link))
            else:
                items.append((None, clean_link))
        
        # Calculate total width
        total_width = 0
        for i, (icon_file, text) in enumerate(items):
            if i > 0:
                total_width += self.get_string_width(separator)
            if icon_file and (ASSETS_DIR / icon_file).exists():
                total_width += icon_size + gap
            total_width += self.get_string_width(self.sanitize_text(text))
        
        # Center the line
        x = (self.w - total_width) / 2
        y = self.get_y()
        
        for i, (icon_file, text) in enumerate(items):
            # Separator
            if i > 0:
                self.set_xy(x, y)
                self.cell(0, icon_size, separator)
                x += self.get_string_width(separator)
            
            # Icon
            if icon_file and (ASSETS_DIR / icon_file).exists():
                try:
                    self.image(str(ASSETS_DIR / icon_file), x=x, y=y + 0.8, h=icon_size - 0.5)
                except Exception:
                    pass
                x += icon_size + gap + 1  # Extra space after icon
            
            # Text
            sanitized = self.sanitize_text(text)
            text_w = self.get_string_width(sanitized)
            self.set_xy(x, y)
            self.cell(text_w, icon_size, sanitized)
            x += text_w
        
        self.ln(icon_size + 2)
    
    def add_summary(self, summary: str):
        """Add professional summary section."""
        self.section_header("Professional Summary")
        self.set_font("Times", "", 10)
        self.set_text_color(*BLACK)
        self.multi_cell(0, 5, self.sanitize_text(summary), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
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
            self.multi_cell(0, 5, self.sanitize_text(", ".join(skills.languages_frameworks)),
                          new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        if skills.tools:
            self.set_font("Times", "B", 10)
            self.cell(0, 5, "Tools & Platforms: ", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_font("Times", "", 10)
            self.multi_cell(0, 5, self.sanitize_text(", ".join(skills.tools)),
                          new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        self.ln(2)
    
    def add_experience(self, experiences: list[Experience]):
        """Add work experience section."""
        self.section_header("Professional Experience")
        
        for exp in experiences:
            # Company and Role
            self.set_font("Times", "B", 10)
            self.set_text_color(*BLACK)
            self.cell(0, 5, self.sanitize_text(exp.role), new_x=XPos.RIGHT, new_y=YPos.LAST)
            
            # Date on the right
            date_str = f"{exp.startDate} - {exp.endDate}"
            self.cell(0, 5, self.sanitize_text(date_str), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            # Company and Location
            self.set_font("Times", "I", 10)
            self.set_text_color(*GRAY)
            self.cell(0, 5, self.sanitize_text(f"{exp.company} | {exp.location}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(1)
            
            # Bullets with bold keywords
            for bullet in exp.bullets:
                self.write_bullet_with_bold(bullet)
            
            self.ln(2)
    
    def add_education(self, education: list[Education]):
        """Add education section."""
        self.section_header("Education")
        
        for edu in education:
            # Degree and Field
            self.set_font("Times", "B", 10)
            self.set_text_color(*BLACK)
            self.cell(0, 5, self.sanitize_text(f"{edu.studyType} in {edu.area}"),
                     new_x=XPos.RIGHT, new_y=YPos.LAST)
            
            # Date on right
            date_str = f"{edu.startDate} - {edu.endDate}"
            self.cell(0, 5, self.sanitize_text(date_str), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            # Institution and Location
            self.set_font("Times", "I", 10)
            self.set_text_color(*GRAY)
            self.cell(0, 5, self.sanitize_text(f"{edu.institution} | {edu.location}"),
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(1)
    
    def add_projects(self, projects: list[Project]):
        """Add projects section."""
        self.section_header("Projects")
        
        for proj in projects:
            # Project name
            self.set_font("Times", "B", 10)
            self.set_text_color(*BLACK)
            self.cell(0, 5, self.sanitize_text(proj.name), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            # Tech stack
            self.set_font("Times", "I", 9)
            self.set_text_color(*GRAY)
            self.cell(0, 4, self.sanitize_text(f"Tech Stack: {proj.techStack}"),
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            # Description
            self.set_font("Times", "", 10)
            self.set_text_color(*BLACK)
            self.multi_cell(0, 5, self.sanitize_text(proj.description),
                          new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(3)  # Extra space after project
    
    def write_bullet_with_bold(self, text: str, line_height: float = 5):
        """Write a bullet point with bold first words, metrics and ATS keywords."""
        import re
        
        text = self.sanitize_text(text)
        if not text:
            return
        
        # Simple approach: just bold the first 3 words
        first_three_match = re.match(r'^(\s*\w+\s+\w+\s+\w+)(.*)$', text)
        
        bullet_indent = 6
        right_margin = self.w - self.r_margin
        
        # Start bullet
        self.set_font("Times", "", 10)
        bullet_x = self.get_x()
        bullet_y = self.get_y()
        self.cell(3, line_height, chr(149), new_x=XPos.RIGHT, new_y=YPos.LAST)
        
        if first_three_match:
            first_three = first_three_match.group(1).strip()
            remainder = first_three_match.group(2)
            
            # Bold first three words
            self.set_font("Times", "B", 10)
            words = first_three.split()
            for i, word in enumerate(words):
                word_to_write = word + (' ' if i < len(words) - 1 or remainder else '')
                word_width = self.get_string_width(word_to_write)
                
                if self.get_x() + word_width > right_margin - 5:
                    self.ln(line_height)
                    self.set_x(self.l_margin + bullet_indent)
                
                self.write(line_height, word_to_write)
            
            # Normal remainder
            if remainder:
                self.set_font("Times", "", 10)
                remainder = remainder.strip()
                words = remainder.split()
                for i, word in enumerate(words):
                    word_to_write = word + (' ' if i < len(words) - 1 else '')
                    word_width = self.get_string_width(word_to_write)
                    
                    if self.get_x() + word_width > right_margin - 5:
                        self.ln(line_height)
                        self.set_x(self.l_margin + bullet_indent)
                    
                    self.write(line_height, word_to_write)
        else:
            # No match, just write normal text
            self.set_font("Times", "", 10)
            words = text.split()
            for i, word in enumerate(words):
                word_to_write = word + (' ' if i < len(words) - 1 else '')
                word_width = self.get_string_width(word_to_write)
                
                if self.get_x() + word_width > right_margin - 5:
                    self.ln(line_height)
                    self.set_x(self.l_margin + bullet_indent)
                
                self.write(line_height, word_to_write)
        
        # End bullet with line break
        self.ln(line_height)
    
    def add_achievements(self, achievements: list[str]):
        """Add achievements section."""
        self.section_header("Achievements")
        
        for achievement in achievements:
            self.write_bullet_with_bold(achievement)
        
        self.ln(2)


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
    
    # Output to bytes (convert bytearray to bytes for Streamlit compatibility)
    output = pdf.output()
    return bytes(output) if isinstance(output, bytearray) else output


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
    
    # Check if keys are available (only Google AI key needed now)
    if not api_keys["google"]:
        st.error("🔐 Google AI API key not configured properly!")
        st.info("""
        Please configure your secrets in Streamlit Cloud:
        1. Go to https://share.streamlit.io/
        2. Find your app and click 'Settings'
        3. Go to 'Secrets' section
        4. Add these secrets:
           - ENCRYPTION_PASSWORD: (your password)
           - GOOGLE_API_KEY_ENCRYPTED: (encrypted Google AI key)
        
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
            # Step 1: Parse Resume with Gemma 12B
            st.subheader("Step 1: Parsing Resume")
            with st.spinner("🤖 Parsing your resume with gemma-3-12b-it..."):
                st.session_state.parsed_resume = parse_resume_with_gemma(
                    resume_text=resume_text,
                    api_key=api_keys["google"]
                )
            
            parsed = st.session_state.parsed_resume
            st.success(f"✅ Parsed resume for: {parsed.basics.name}")
            st.info(f"📊 Found: {len(parsed.experience)} experience entries, "
                   f"{len(parsed.projects)} projects, "
                   f"{len(parsed.education)} education entries")
            
            # Step 2: Tailor Resume with Model Router
            st.subheader("Step 2: Tailoring for Job Description")
            
            # Initialize model router
            router = ModelRouter()
            
            # Show current tier usage
            with st.expander("📊 Model Tier Usage (Resets at Midnight UTC)"):
                tier_info = router.get_current_tier_info()
                for tier in tier_info:
                    limit_str = f"{tier['used']}/{tier['limit']}" if tier['limit'] != '∞' else f"{tier['used']}/∞"
                    progress = tier['percentage'] / 100 if tier['limit'] != '∞' else 0
                    status = "✅ Active" if tier['active'] else "⏭️ Fallback"
                    st.progress(progress, text=f"Tier {tier['tier']}: {limit_str} - {status}")
            
            with st.spinner("🎯 Tailoring resume..."):
                # Convert Pydantic model to dict for JSON serialization
                master_resume_dict = parsed.model_dump()
                
                # Get tailored resume with model router
                response_text, model_used = tailor_resume_with_model_router(
                    master_resume=master_resume_dict,
                    job_description=job_description,
                    api_key=api_keys["google"],
                    model_router=router
                )
                st.session_state.tailored_response_text = response_text
                st.info(f"🤖 Model used: {model_used}")
            
            # Show raw response in expander for debugging
            with st.expander("Debug: Raw Response"):
                st.text(st.session_state.tailored_response_text[:2000])
            
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
                
                # Generate filename using new format: FirstNameLastNameResumeYear.pdf
                name_parts = tailored_resume.basics.name.strip().split()
                if len(name_parts) >= 2:
                    first_name = name_parts[0]
                    last_name = name_parts[-1]
                else:
                    first_name = name_parts[0] if name_parts else "Resume"
                    last_name = ""
                current_year = datetime.now().year
                filename = f"{first_name}{last_name}Resume{current_year}.pdf"
                
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
