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
from pydantic import BaseModel, Field

# Import consolidated PDF renderer
from renderer import generate_pdf_to_bytes

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
    sanitized = re.sub(r'[<>"/\\|?*]', '', name)
    sanitized = sanitized.replace(' ', '_')
    return sanitized[:50]


def main():
    """Main Streamlit application."""
    init_session_state()
    
    # Page configuration
    st.set_page_config(
        page_title="Resume Tailor",
        page_icon="📝",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #6b7280;
        text-align: center;
        margin-bottom: 2rem;
    }
    .step-container {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d1fae5;
        border: 1px solid #10b981;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #dbeafe;
        border: 1px solid #3b82f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fef3c7;
        border: 1px solid #f59e0b;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">📝 Resume Tailor</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Resume Customization for Job Applications</p>', unsafe_allow_html=True)
    
    # Get decrypted API keys
    api_keys = get_decrypted_api_keys()
    
    if not api_keys["google"]:
        st.error("🔐 Google API key not configured. Please set up Streamlit secrets.")
        st.stop()
    
    # Initialize model router
    model_router = ModelRouter()
    
    # Step indicator
    st.markdown(f"### Step {st.session_state.step} of 3")
    
    # STEP 1: Upload Resume
    if st.session_state.step == 1:
        with st.container():
            st.markdown("<div class='step-container'>", unsafe_allow_html=True)
            st.subheader("📄 Upload Your Resume")
            st.write("Upload your resume in PDF format. We'll extract the text and parse it into a structured format.")
            
            uploaded_file = st.file_uploader(
                "Choose a PDF file",
                type="pdf",
                help="Upload your resume as a PDF file"
            )
            
            if uploaded_file is not None:
                with st.spinner("🔍 Extracting text from PDF..."):
                    try:
                        # Extract text from PDF
                        file_bytes = uploaded_file.getvalue()
                        extracted_text = extract_text_from_pdf(file_bytes)
                        
                        if not extracted_text.strip():
                            st.error("❌ Could not extract text from PDF. Please ensure it's a text-based PDF.")
                        else:
                            # Parse resume with Gemma
                            with st.spinner("🤖 Parsing resume with AI..."):
                                parsed_resume = parse_resume_with_gemma(
                                    extracted_text,
                                    api_keys["google"]
                                )
                                st.session_state.parsed_resume = parsed_resume
                                st.session_state.step = 2
                                st.rerun()
                                
                    except Exception as e:
                        st.error(f"❌ Error processing resume: {str(e)}")
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # STEP 2: Paste Job Description
    elif st.session_state.step == 2:
        # Show parsed resume summary
        if st.session_state.parsed_resume:
            with st.expander("✅ Parsed Resume Summary", expanded=False):
                resume = st.session_state.parsed_resume
                st.write(f"**Name:** {resume.basics.name}")
                st.write(f"**Email:** {resume.basics.email}")
                st.write(f"**Experience:** {len(resume.experience)} roles")
                st.write(f"**Education:** {len(resume.education)} entries")
                st.write(f"**Projects:** {len(resume.projects)} projects")
        
        with st.container():
            st.markdown("<div class='step-container'>", unsafe_allow_html=True)
            st.subheader("💼 Job Description")
            st.write("Paste the job description you're applying for. Our AI will tailor your resume to match.")
            
            job_description = st.text_area(
                "Job Description",
                height=200,
                placeholder="Paste the job description here...",
                help="Copy and paste the full job description from the job posting"
            )
            
            col1, col2 = st.columns([1, 4])
            
            with col1:
                if st.button("⬅️ Back", use_container_width=True):
                    st.session_state.step = 1
                    st.rerun()
            
            with col2:
                if st.button("🚀 Tailor Resume", type="primary", use_container_width=True):
                    if not job_description.strip():
                        st.warning("⚠️ Please enter a job description.")
                    else:
                        with st.spinner("✨ Tailoring your resume with AI..."):
                            try:
                                # Convert ParsedResume to dict for tailoring
                                resume_dict = st.session_state.parsed_resume.model_dump()
                                
                                # Tailor resume
                                response_text, model_used = tailor_resume_with_model_router(
                                    resume_dict,
                                    job_description,
                                    api_keys["google"],
                                    model_router
                                )
                                
                                # Store response
                                st.session_state.tailored_response_text = response_text
                                st.session_state.model_used = model_used
                                
                                # Parse the tailored response
                                tailored_resume = parse_tailored_response(response_text)
                                st.session_state.tailored_resume = tailored_resume
                                st.session_state.step = 3
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"❌ Error tailoring resume: {str(e)}")
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # STEP 3: Download Resume
    elif st.session_state.step == 3:
        tailored_resume = st.session_state.tailored_resume
        
        if tailored_resume:
            # Success message
            st.markdown("<div class='success-box'>", unsafe_allow_html=True)
            st.success("✅ Resume tailored successfully!")
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Preview tailored resume
            with st.expander("👁️ Preview Tailored Resume", expanded=True):
                st.subheader(tailored_resume.basics.name)
                st.caption(f"{tailored_resume.basics.email} | {tailored_resume.basics.phone} | {tailored_resume.basics.location}")
                
                if tailored_resume.basics.links:
                    st.caption(" | ".join(tailored_resume.basics.links))
                
                st.divider()
                
                if tailored_resume.summary:
                    st.write("**Professional Summary**")
                    st.write(tailored_resume.summary)
                    st.divider()
                
                if tailored_resume.skills:
                    st.write("**Skills**")
                    if tailored_resume.skills.languages_frameworks:
                        st.write(f"Languages & Frameworks: {', '.join(tailored_resume.skills.languages_frameworks)}")
                    if tailored_resume.skills.tools:
                        st.write(f"Tools: {', '.join(tailored_resume.skills.tools)}")
                    st.divider()
                
                if tailored_resume.experience:
                    st.write("**Experience**")
                    for exp in tailored_resume.experience:
                        st.write(f"**{exp.role}** at {exp.company}")
                        st.caption(f"{exp.startDate} — {exp.endDate} | {exp.location}")
                        for bullet in exp.bullets[:3]:  # Show first 3 bullets
                            st.write(f"• {bullet[:100]}...")
                        st.write("")
            
            # Generate PDF
            try:
                pdf_bytes = generate_pdf_to_bytes(tailored_resume)
                
                # Download button
                filename = sanitize_filename(f"{tailored_resume.basics.name}_Resume.pdf")
                
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col2:
                    st.download_button(
                        label="📥 Download Tailored Resume (PDF)",
                        data=pdf_bytes,
                        file_name=filename,
                        mime="application/pdf",
                        use_container_width=True
                    )
                
                # Start over button
                st.divider()
                if st.button("🔄 Start Over", use_container_width=True):
                    st.session_state.parsed_resume = None
                    st.session_state.tailored_resume = None
                    st.session_state.tailored_response_text = ""
                    st.session_state.step = 1
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Error generating PDF: {str(e)}")
                st.code(st.session_state.tailored_response_text, language="json")


if __name__ == "__main__":
    main()
