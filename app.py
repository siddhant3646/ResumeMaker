#!/usr/bin/env python3
"""
Resume Tailor - Streamlit Web Application

A secure web application that takes a Resume (PDF or Text) and a Job Description,
parses the resume into structured JSON, then generates a tailored ATS-friendly resume.

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
import requests
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
        Dictionary with 'google' and 'nvidia' keys containing decrypted API keys
    """
    keys = {
        "google": None,
        "nvidia": None
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
        
        # Decrypt NVIDIA API key
        encrypted_nvidia = st.secrets.get("NVIDIA_API_KEY_ENCRYPTED")
        if encrypted_nvidia:
            keys["nvidia"] = decrypt_api_key(encrypted_nvidia, password)
            
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
# Resume Parsing
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
    Parse resume text into structured JSON using gemma-3-27b-it via Google AI Studio.
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
    add_log("Initializing AI parser...", "processing")
    
    if not GOOGLE_GENAI_AVAILABLE:
        add_log("ERROR: AI library not available", "error")
        raise ImportError("google-generativeai library not available")
    
    # Configure the API
    add_log("Configuring AI API...", "info")
    genai.configure(api_key=api_key)
    
    # Load AI model for parsing
    add_log("Loading AI model...", "info")
    model = genai.GenerativeModel("gemma-3-27b-it")
    
    # Build the prompt
    # Use replace() instead of format() to avoid issues with curly braces in resume text
    prompt = PARSING_PROMPT.replace("{resume_text}", resume_text)
    add_log(f"Resume text length: {len(resume_text)} characters", "info")
    
    last_error = None
    last_response_text = ""
    
    for attempt in range(max_retries):
        try:
            add_log(f"Attempt {attempt + 1}/{max_retries}: Sending request to Google AI...", "processing")
            
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
            
            add_log(f"Received response: {len(response.text)} characters", "success")
            
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
            
            add_log("Parsing JSON response...", "processing")
            # Parse JSON into dict first
            parsed_data = json.loads(response_text)
            
            # Fix projects techStack - convert list to string if needed
            if 'projects' in parsed_data and isinstance(parsed_data['projects'], list):
                for project in parsed_data['projects']:
                    if isinstance(project, dict) and 'techStack' in project:
                        if isinstance(project['techStack'], list):
                            project['techStack'] = ', '.join(project['techStack'])
            
            add_log("Validating with Pydantic schema...", "processing")
            # Now validate with Pydantic
            parsed_resume = ParsedResume(**parsed_data)
            
            # Success! Return the parsed resume
            if attempt > 0:
                add_log(f"Successfully parsed resume after {attempt + 1} attempts", "success")
            else:
                add_log("Resume parsed successfully!", "success")
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
                    add_log(f"Rate limit hit (429). Waiting {current_delay:.1f}s...", "warning")
                else:
                    add_log(f"Attempt {attempt + 1} failed: {str(e)[:80]}...", "warning")
                time.sleep(current_delay)
            else:
                # All retries exhausted
                add_log(f"All {max_retries} attempts failed", "error")
                break
    
    # All retries failed
    error_msg = f"Failed to parse resume after {max_retries} attempts.\n"
    error_msg += f"Last error: {last_error}\n"
    error_msg += f"Last response:\n{last_response_text[:1000]}"
    raise ValueError(error_msg)


# ============================================================================
# Resume Tailoring
# ============================================================================

TAILORING_PROMPT = """You are an expert technical resume writer. Rewrite the resume to match the job description for maximum ATS compatibility.

## KEY RULES:
1. **Metrics**: Use diverse metrics (time, scale, counts, reliability) - avoid only percentages
2. **Power Verbs**: Architected, Engineered, Optimized, Spearheaded, Secured
3. **Bullet Format**: [Power Verb] + [Achievement] + [Technology] + [Metric]
4. **EXPERIENCE BULLETS** (CRITICAL):
   - MOST RECENT role (latest startDate): 10-12 detailed bullets
   - ALL OTHER roles: 1-2 bullets only
5. **NO SUMMARY SECTION** - Skip entirely
6. **Preserve**: Keep ALL dates exactly as provided
7. **One Page**: Skills (1 line), Education (compact), Projects/Achievements only if space permits

## OUTPUT STRUCTURE (JSON ONLY):
```json
{
  "basics": {"name": "", "email": "", "phone": "", "location": "", "links": []},
  "education": [{"institution": "", "area": "", "studyType": "", "startDate": "", "endDate": "", "location": ""}],
  "experience": [{"company": "", "location": "", "role": "", "startDate": "", "endDate": "", "bullets": []}],
  "skills": {"languages_frameworks": [], "tools": []},
  "projects": [{"name": "", "techStack": "", "description": ""}],
  "achievements": []
}
```

## INPUT:
**Resume:**
```json
{master_resume_json}
```

**Job Description:**
{job_description}

Return ONLY valid JSON. No markdown."""


def tailor_resume_with_nvidia(
    master_resume: dict,
    job_description: str,
    nvidia_api_key: str,
    max_retries: int = 3,
    retry_delay: float = 2.0,
    progress_callback: Optional[callable] = None
) -> tuple[str, str]:
    """
    Tailor resume using Kimi k2.5 model via NVIDIA API with streaming support.
    Includes detailed timeout logging and retry logic.
    
    Args:
        master_resume: The parsed resume as a dictionary
        job_description: The job description text
        nvidia_api_key: NVIDIA API key for integrate.api.nvidia.com
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delay: Initial delay between retries in seconds (default: 2.0)
        progress_callback: Optional callback function(progress: float, chars: int, status: str) for UI updates
        
    Returns:
        Tuple of (response_text, model_name_used)
        
    Raises:
        ValueError: If all retry attempts fail
    """
    import time
    start_time = time.time()
    
    add_log("Initializing AI tailor...", "processing")
    
    # API endpoint
    invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
    stream = True  # Enable streaming for faster perceived response
    
    # Build the prompt
    add_log("Building tailoring prompt...", "info")
    master_resume_json_str = json.dumps(master_resume, separators=(',', ':'))  # Compact JSON
    prompt = TAILORING_PROMPT.replace("{master_resume_json}", master_resume_json_str)
    prompt = prompt.replace("{job_description}", job_description)
    prompt_size = len(prompt)
    add_log(f"Prompt size: {prompt_size} characters (~{prompt_size // 4} tokens)", "info")
    
    headers = {
        "Authorization": f"Bearer {nvidia_api_key}",
        "Accept": "text/event-stream" if stream else "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "moonshotai/kimi-k2.5",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 32768,
        "temperature": 0.3,
        "top_p": 0.9,
        "stream": stream
    }
    
    last_error = None
    
    for attempt in range(max_retries):
        attempt_start = time.time()
        try:
            add_log(f"Attempt {attempt + 1}/{max_retries}: Connecting to AI service...", "processing")
            add_log("Streaming mode enabled for faster response...", "info")
            
            # Track connection time
            conn_start = time.time()
            response = requests.post(invoke_url, headers=headers, json=payload, timeout=180, stream=stream)
            conn_time = time.time() - conn_start
            add_log(f"Connected in {conn_time:.1f}s", "success")
            
            response.raise_for_status()
            
            if stream:
                # Process streaming response
                add_log("Receiving streamed response...", "processing")
                response_text = ""
                chunk_count = 0
                last_log_time = time.time()
                
                for line in response.iter_lines():
                    if line:
                        chunk_count += 1
                        line_str = line.decode('utf-8')
                        
                        # Log progress every 5 seconds
                        current_time = time.time()
                        if current_time - last_log_time > 5:
                            elapsed = current_time - attempt_start
                            add_log(f"Receiving... {chunk_count} chunks, {elapsed:.0f}s elapsed", "info")
                            last_log_time = current_time
                        
                        # Parse SSE format
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]
                            if data_str == '[DONE]':
                                break
                            try:
                                data = json.loads(data_str)
                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        response_text += delta['content']
                                        # Update progress every 10 chunks or when content is received
                                        if chunk_count % 10 == 0 and progress_callback:
                                            progress_callback(chunk_count, len(response_text), "generating")
                            except json.JSONDecodeError:
                                continue
                
                total_time = time.time() - attempt_start
                add_log(f"Stream complete: {chunk_count} chunks in {total_time:.1f}s", "success")
                if progress_callback:
                    progress_callback(chunk_count, len(response_text), "complete")
            else:
                # Non-streaming fallback
                data = response.json()
                
                if 'choices' not in data or len(data['choices']) == 0:
                    raise ValueError("Empty response from AI API")
                
                response_text = data['choices'][0]['message']['content']
                total_time = time.time() - attempt_start
                add_log(f"Response received in {total_time:.1f}s", "success")
            
            if not response_text:
                raise ValueError("Empty response from tailoring API")
            
            # Validate JSON is complete (not truncated)
            response_text = response_text.strip()
            if not (response_text.startswith('{') and response_text.endswith('}')):
                add_log(f"Warning: Response appears truncated ({len(response_text)} chars)", "warning")
                # Try to find complete JSON object
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    response_text = response_text[start_idx:end_idx+1]
                    add_log("Extracted valid JSON object from response", "info")
                else:
                    raise ValueError("Response appears to be truncated. Try with a shorter job description or resume.")
            
            final_time = time.time() - start_time
            add_log(f"Tailored resume: {len(response_text)} chars (Total: {final_time:.1f}s)", "success")
            
            # Success! Return the response text
            if attempt > 0:
                add_log(f"Success after {attempt + 1} attempts", "success")
            return response_text, "AI"
            
        except requests.exceptions.Timeout as e:
            elapsed = time.time() - attempt_start
            last_error = e
            add_log(f"TIMEOUT after {elapsed:.1f}s", "error")
            
            if attempt < max_retries - 1:
                current_delay = retry_delay * (2 ** attempt)
                add_log(f"Retrying in {current_delay:.0f}s...", "warning")
                time.sleep(current_delay)
            else:
                add_log(f"All {max_retries} attempts timed out", "error")
                break
                
        except requests.exceptions.RequestException as e:
            elapsed = time.time() - attempt_start
            last_error = e
            error_str = str(e).lower()
            
            # Check for rate limit errors
            is_rate_limit = any(x in error_str for x in ['429', 'rate limit', 'too many requests'])
            
            if attempt < max_retries - 1:
                current_delay = retry_delay * (2 ** attempt)
                if is_rate_limit:
                    current_delay *= 2
                    add_log(f"Rate limit hit after {elapsed:.1f}s. Wait {current_delay:.0f}s...", "warning")
                else:
                    add_log(f"Error after {elapsed:.1f}s: {str(e)[:60]}...", "warning")
                time.sleep(current_delay)
            else:
                add_log(f"All {max_retries} attempts failed", "error")
                break
        except Exception as e:
            elapsed = time.time() - attempt_start
            last_error = e
            if attempt < max_retries - 1:
                current_delay = retry_delay * (2 ** attempt)
                add_log(f"Error after {elapsed:.1f}s: {str(e)[:60]}...", "warning")
                time.sleep(current_delay)
            else:
                add_log(f"All {max_retries} attempts failed", "error")
                break
    
    # All retries failed
    total_elapsed = time.time() - start_time
    raise ValueError(f"Failed after {max_retries} attempts ({total_elapsed:.1f}s). Last error: {last_error}")


def parse_tailored_response(response_text: str) -> ParsedResume:
    """
    Parse the tailored response into a ParsedResume object.
    
    Args:
        response_text: The full text response from the AI model
        
    Returns:
        ParsedResume object
        
    Raises:
        ValueError: If response is empty or invalid JSON
    """
    # Check for empty response
    if not response_text or not response_text.strip():
        raise ValueError("Empty response from API. The model may have failed to generate output.")
    
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
        raise ValueError("Empty response from API after cleaning markdown.")
    
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
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    if 'is_processing' not in st.session_state:
        st.session_state.is_processing = False
    if 'model_used' not in st.session_state:
        st.session_state.model_used = None


def add_log(message: str, log_type: str = "info"):
    """Add a log entry to the session state logs."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    icon = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌", "processing": "🔄"}.get(log_type, "ℹ️")
    st.session_state.logs.append({"time": timestamp, "message": message, "type": log_type, "icon": icon})
    # Keep only last 50 logs to prevent memory issues
    if len(st.session_state.logs) > 50:
        st.session_state.logs = st.session_state.logs[-50:]


def clear_logs():
    """Clear all logs."""
    st.session_state.logs = []


def render_logs_sidebar():
    """Render the logs in the sidebar."""
    with st.sidebar:
        st.markdown("### 📋 Activity Logs")
        
        # Clear logs button
        if st.button("🗑️ Clear Logs", use_container_width=True):
            clear_logs()
            st.rerun()
        
        st.divider()
        
        # Display logs in reverse order (newest first)
        if st.session_state.logs:
            for log in reversed(st.session_state.logs):
                st.markdown(f"**{log['time']}** {log['icon']} {log['message']}")
        else:
            st.info("No activity yet. Start processing to see logs.")


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
        initial_sidebar_state="expanded"
    )
    
    # Render logs in sidebar
    render_logs_sidebar()
    
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
    
    # Check for required API keys
    if not api_keys["google"]:
        st.error("🔐 Google API key not configured. Please set up Streamlit secrets.")
        st.stop()
    
    if not api_keys["nvidia"]:
        st.error("🔐 NVIDIA API key not configured. Please set up Streamlit secrets.")
        st.stop()
    
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
                # Clear logs when starting new processing
                clear_logs()
                add_log("Starting Step 1: Resume Upload & Parsing", "info")
                
                with st.spinner("🔍 Extracting text from PDF..."):
                    try:
                        # Extract text from PDF
                        add_log(f"Processing file: {uploaded_file.name}", "info")
                        file_bytes = uploaded_file.getvalue()
                        add_log(f"File size: {len(file_bytes)} bytes", "info")
                        
                        extracted_text = extract_text_from_pdf(file_bytes)
                        add_log(f"Extracted {len(extracted_text)} characters from PDF", "success")
                        
                        if not extracted_text.strip():
                            add_log("ERROR: No text found in PDF", "error")
                            st.error("❌ Could not extract text from PDF. Please ensure it's a text-based PDF.")
                        else:
                            # Parse resume with AI
                            with st.spinner("🤖 Parsing resume with AI..."):
                                add_log("Starting AI parsing...", "processing")
                                parsed_resume = parse_resume_with_gemma(
                                    extracted_text,
                                    api_keys["google"]
                                )
                                add_log(f"Parsed resume for: {parsed_resume.basics.name}", "success")
                                add_log(f"Found {len(parsed_resume.experience)} experience entries", "info")
                                add_log(f"Found {len(parsed_resume.education)} education entries", "info")
                                st.session_state.parsed_resume = parsed_resume
                                st.session_state.step = 2
                                add_log("Moving to Step 2", "info")
                                st.rerun()
                                
                    except Exception as e:
                        add_log(f"ERROR: {str(e)[:100]}", "error")
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
                        # Clear previous logs and start fresh
                        clear_logs()
                        add_log("Starting Step 2: Resume Tailoring", "info")
                        add_log(f"Job description length: {len(job_description)} characters", "info")
                        
                        # Create enhanced UI elements for progress tracking
                        progress_container = st.container()
                        with progress_container:
                            # Animated status with stages
                            status_animation = st.empty()
                            progress_bar = st.progress(0.0)
                            details_placeholder = st.empty()
                            
                            # Show initial stage with continuous animation
                            status_animation.markdown("""
                            <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 50%, #1e3a5f 100%); border-radius: 15px; margin: 10px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                                <div style="font-size: 50px; margin-bottom: 15px;">
                                    <span style="display: inline-block; animation: rocketLaunch 2s ease-in-out infinite;">🚀</span>
                                </div>
                                <div style="color: white; font-size: 20px; font-weight: bold; margin-bottom: 8px;">
                                    Initializing AI Engine
                                </div>
                                <div style="color: #a0c4e8; font-size: 14px; margin-bottom: 15px;">
                                    Preparing to craft your perfect resume...
                                </div>
                                <div style="display: flex; justify-content: center; gap: 8px; margin-top: 15px;">
                                    <span class="loading-dot" style="width: 10px; height: 10px; background: #4fc3f7; border-radius: 50%; display: inline-block; animation: bounceDots 1.4s ease-in-out infinite;"></span>
                                    <span class="loading-dot" style="width: 10px; height: 10px; background: #4fc3f7; border-radius: 50%; display: inline-block; animation: bounceDots 1.4s ease-in-out 0.2s infinite;"></span>
                                    <span class="loading-dot" style="width: 10px; height: 10px; background: #4fc3f7; border-radius: 50%; display: inline-block; animation: bounceDots 1.4s ease-in-out 0.4s infinite;"></span>
                                </div>
                            </div>
                            <style>
                                @keyframes rocketLaunch {
                                    0%, 100% { transform: translateY(0) rotate(-5deg); }
                                    25% { transform: translateY(-8px) rotate(5deg); }
                                    50% { transform: translateY(-15px) rotate(-5deg); }
                                    75% { transform: translateY(-8px) rotate(5deg); }
                                }
                                @keyframes bounceDots {
                                    0%, 80%, 100% { transform: scale(0); opacity: 0.5; }
                                    40% { transform: scale(1); opacity: 1; }
                                }
                            </style>
                            """, unsafe_allow_html=True)
                            progress_bar.progress(0.05)
                        
                        try:
                            # Convert ParsedResume to dict for tailoring
                            add_log("Converting resume to dictionary format...", "info")
                            resume_dict = st.session_state.parsed_resume.model_dump()
                            
                            # Update to reading resume stage with fun fact
                            status_animation.markdown("""
                            <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 50%, #1e3a5f 100%); border-radius: 15px; margin: 10px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                                <div style="font-size: 45px; margin-bottom: 15px;">
                                    <span style="display: inline-block; animation: flipPage 1.5s ease-in-out infinite;">📄</span>
                                </div>
                                <div style="color: white; font-size: 20px; font-weight: bold; margin-bottom: 8px;">
                                    Reading Your Resume
                                </div>
                                <div style="color: #a0c4e8; font-size: 14px; margin-bottom: 15px;">
                                    Extracting your experience and achievements...
                                </div>
                                <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 8px; margin-top: 15px; border-left: 3px solid #4fc3f7;">
                                    <div style="color: #81d4fa; font-size: 12px; font-style: italic;">
                                        💡 Did you know? 75% of resumes are rejected by ATS before human review
                                    </div>
                                </div>
                            </div>
                            <style>
                                @keyframes flipPage {
                                    0%, 100% { transform: rotateY(0deg); }
                                    50% { transform: rotateY(180deg); }
                                }
                            </style>
                            """, unsafe_allow_html=True)
                            progress_bar.progress(0.15)
                            
                            # Update to analyzing stage with another tip
                            status_animation.markdown("""
                            <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 50%, #1e3a5f 100%); border-radius: 15px; margin: 10px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                                <div style="font-size: 45px; margin-bottom: 15px;">
                                    <span style="display: inline-block; animation: searchZoom 2s ease-in-out infinite;">🔍</span>
                                </div>
                                <div style="color: white; font-size: 20px; font-weight: bold; margin-bottom: 8px;">
                                    Analyzing Job Description
                                </div>
                                <div style="color: #a0c4e8; font-size: 14px; margin-bottom: 15px;">
                                    Identifying key requirements and keywords...
                                </div>
                                <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 8px; margin-top: 15px; border-left: 3px solid #4fc3f7;">
                                    <div style="color: #81d4fa; font-size: 12px; font-style: italic;">
                                        💡 Pro tip: Tailored resumes get 3x more interviews than generic ones
                                    </div>
                                </div>
                            </div>
                            <style>
                                @keyframes searchZoom {
                                    0%, 100% { transform: scale(1) rotate(0deg); }
                                    25% { transform: scale(1.1) rotate(-10deg); }
                                    75% { transform: scale(1.1) rotate(10deg); }
                                }
                            </style>
                            """, unsafe_allow_html=True)
                            progress_bar.progress(0.25)
                            
                            # Tailor resume using AI with progress tracking
                            add_log("Sending request to AI service...", "processing")
                            
                            def update_progress(chunks: int, chars: int, status: str):
                                """Update progress bar based on character generation with animation."""
                                # Estimate progress (typical response is ~2000-4000 chars)
                                estimated_total = 3000
                                base_progress = 0.3  # First 30% is setup
                                generation_progress = min(0.65, (chars / estimated_total) * 0.65)
                                progress = base_progress + generation_progress
                                
                                progress_bar.progress(progress)
                                
                                if status == "generating":
                                    # Animated writing status with rotating tips
                                    animation_icons = ["✍️", "📝", "✨", "💼", "🎯", "🚀"]
                                    tips = [
                                        "💡 Action verbs like 'Architected' and 'Engineered' make stronger impact",
                                        "💡 Quantified achievements get 40% more attention from recruiters",
                                        "💡 ATS systems scan for keywords in the first 1/3 of your resume",
                                        "💡 Skills matching job description increase interview chances by 3x",
                                        "💡 Bullet points starting with numbers catch the eye immediately",
                                        "💡 Keeping resume to 1 page increases readability by 70%"
                                    ]
                                    icon = animation_icons[(chunks // 15) % len(animation_icons)]
                                    tip = tips[(chunks // 30) % len(tips)]
                                    
                                    status_animation.markdown(f"""
                                    <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #2d5a87 0%, #4a90c2 50%, #2d5a87 100%); border-radius: 15px; margin: 10px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                                        <div style="font-size: 50px; margin-bottom: 15px;">
                                            <span style="display: inline-block; animation: magicWrite 1.5s ease-in-out infinite;">{icon}</span>
                                        </div>
                                        <div style="color: white; font-size: 20px; font-weight: bold; margin-bottom: 8px;">
                                            ✨ Rewriting Your Resume ✨
                                        </div>
                                        <div style="color: #a0c4e8; font-size: 14px; margin-bottom: 15px;">
                                            Crafting tailored content... <span style="color: #4fc3f7; font-weight: bold;">{chars}</span> characters generated
                                        </div>
                                        <div style="display: flex; justify-content: center; gap: 8px; margin: 15px 0;">
                                            <span style="width: 8px; height: 8px; background: #4fc3f7; border-radius: 50%; display: inline-block; animation: pulseDot 1s ease-in-out infinite;"></span>
                                            <span style="width: 8px; height: 8px; background: #4fc3f7; border-radius: 50%; display: inline-block; animation: pulseDot 1s ease-in-out 0.2s infinite;"></span>
                                            <span style="width: 8px; height: 8px; background: #4fc3f7; border-radius: 50%; display: inline-block; animation: pulseDot 1s ease-in-out 0.4s infinite;"></span>
                                        </div>
                                        <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 8px; margin-top: 15px; border-left: 3px solid #4fc3f7;">
                                            <div style="color: #81d4fa; font-size: 12px; font-style: italic; animation: fadeTip 3s ease-in-out;">
                                                {tip}
                                            </div>
                                        </div>
                                        <div style="margin-top: 15px; display: flex; justify-content: center; gap: 15px; flex-wrap: wrap;">
                                            <span style="background: rgba(79, 195, 247, 0.2); padding: 5px 10px; border-radius: 15px; color: #81d4fa; font-size: 11px;">🎯 Matching skills</span>
                                            <span style="background: rgba(79, 195, 247, 0.2); padding: 5px 10px; border-radius: 15px; color: #81d4fa; font-size: 11px;">💡 ATS Optimization</span>
                                            <span style="background: rgba(79, 195, 247, 0.2); padding: 5px 10px; border-radius: 15px; color: #81d4fa; font-size: 11px;">📊 Highlighting wins</span>
                                        </div>
                                    </div>
                                    <style>
                                        @keyframes magicWrite {{
                                            0%, 100% {{ transform: translateY(0) rotate(-5deg) scale(1); }}
                                            25% {{ transform: translateY(-5px) rotate(5deg) scale(1.1); }}
                                            50% {{ transform: translateY(0) rotate(-5deg) scale(1); }}
                                            75% {{ transform: translateY(-3px) rotate(5deg) scale(1.05); }}
                                        }}
                                        @keyframes pulseDot {{
                                            0%, 100% {{ transform: scale(1); opacity: 1; }}
                                            50% {{ transform: scale(0.5); opacity: 0.5; }}
                                        }}
                                        @keyframes fadeTip {{
                                            0%, 100% {{ opacity: 1; }}
                                            50% {{ opacity: 0.7; }}
                                        }}
                                    </style>
                                    """, unsafe_allow_html=True)
                                    
                                    # Show dynamic details
                                    details_placeholder.info(f"📊 Generated {chars} characters of tailored content")
                                    
                                elif status == "complete":
                                    progress_bar.progress(1.0)
                                    status_animation.markdown("""
                                    <div style="text-align: center; padding: 20px; background: linear-gradient(90deg, #2d7d46 0%, #4caf50 100%); border-radius: 10px; margin: 10px 0;">
                                        <div style="font-size: 40px; animation: success 0.6s ease-out;">✅</div>
                                        <div style="color: white; font-size: 18px; font-weight: bold; margin-top: 10px;">
                                            Resume Tailored Successfully!
                                        </div>
                                        <div style="color: #c8e6c9; font-size: 14px; margin-top: 5px;">
                                            Your optimized resume is ready for download
                                        </div>
                                    </div>
                                    <style>
                                        @keyframes success {
                                            0% { transform: scale(0) rotate(0deg); }
                                            50% { transform: scale(1.2) rotate(180deg); }
                                            100% { transform: scale(1) rotate(360deg); }
                                        }
                                    </style>
                                    """, unsafe_allow_html=True)
                                    details_placeholder.empty()
                            
                            response_text, model_used = tailor_resume_with_nvidia(
                                resume_dict,
                                job_description,
                                api_keys["nvidia"],
                                progress_callback=update_progress
                            )
                            
                            # Store response
                            add_log("Response received, parsing results...", "processing")
                            st.session_state.tailored_response_text = response_text
                            
                            # Parse the tailored response
                            tailored_resume = parse_tailored_response(response_text)
                            add_log(f"Tailored resume for: {tailored_resume.basics.name}", "success")
                            
                            # Clear UI elements on success
                            status_animation.empty()
                            progress_bar.empty()
                            details_placeholder.empty()
                            progress_container.empty()
                            
                            st.session_state.tailored_resume = tailored_resume
                            st.session_state.step = 3
                            add_log("Moving to Step 3 (Download)", "info")
                            st.rerun()
                            
                        except Exception as e:
                            add_log(f"ERROR: {str(e)[:100]}", "error")
                            status_animation.markdown(f"""
                            <div style="text-align: center; padding: 20px; background: linear-gradient(90deg, #8b2635 0%, #c0392b 100%); border-radius: 10px; margin: 10px 0;">
                                <div style="font-size: 40px;">❌</div>
                                <div style="color: white; font-size: 18px; font-weight: bold; margin-top: 10px;">
                                    Error Tailoring Resume
                                </div>
                                <div style="color: #f5b7b1; font-size: 14px; margin-top: 5px;">
                                    {str(e)[:100]}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            progress_bar.empty()
                            details_placeholder.empty()
            
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
                
                # No summary section - removed to save space
                
                if tailored_resume.skills:
                    st.write("**Skills**")
                    # Combine all skills into single line
                    all_skills = []
                    if tailored_resume.skills.languages_frameworks:
                        all_skills.extend(tailored_resume.skills.languages_frameworks)
                    if tailored_resume.skills.tools:
                        all_skills.extend(tailored_resume.skills.tools)
                    if all_skills:
                        st.write(f"{', '.join(all_skills)}")
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
                pdf_bytes = generate_pdf_to_bytes(tailored_resume, include_summary=False)
                
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
                    st.session_state.model_used = None
                    st.session_state.step = 1
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Error generating PDF: {str(e)}")
                st.code(st.session_state.tailored_response_text, language="json")


if __name__ == "__main__":
    main()
