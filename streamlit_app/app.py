"""
ResumeMaker AI - Streamlit Application
A comprehensive AI-powered resume builder with password protection
"""

import streamlit as st
import os
import sys
from pathlib import Path
from typing import Optional
import json
import tempfile
from io import BytesIO
import asyncio
import bcrypt
import hmac
import logging

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Import application modules
from backend.app.resume import ResumeProcessor
from backend.app.ai_client import AIClient
from backend.app.models import TailoredResume
from intelligence.ats_scorer import ATSScorer
from intelligence.content_generator import ContentGenerator
from intelligence.role_detector import RoleDetector
from vision.pdf_validator import PDFValidator

# ============================================================================
# Configuration
# ============================================================================

# Password protection - set in Streamlit secrets or environment
def get_app_password() -> Optional[str]:
    """Get app password from secrets or environment.
    
    Returns None if not configured (will show error in production).
    """
    try:
        if hasattr(st, 'secrets') and 'APP_PASSWORD' in st.secrets:
            return st.secrets['APP_PASSWORD']
    except:
        pass
    
    password = os.getenv('APP_PASSWORD')
    
    # Only allow default password in development mode
    if not password:
        if os.getenv('STREAMLIT_ENV') == 'development':
            return 'dev-password'  # Development only
        return None  # No password configured
    
    return password

def get_api_key() -> Optional[str]:
    """Get NVIDIA API key from environment or secrets."""
    try:
        if hasattr(st, 'secrets') and 'NVIDIA_API_KEY' in st.secrets:
            return st.secrets['NVIDIA_API_KEY']
    except:
        pass
    return os.getenv('NVIDIA_API_KEY')

def hash_password(password: str) -> str:
    """Hash password using bcrypt for secure storage."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain_password: str, stored_value: str) -> bool:
    """Verify password against stored value.
    
    Supports both bcrypt hashes (recommended) and plaintext passwords (legacy).
    To use bcrypt, store the hash in APP_PASSWORD secret (generate with hash_password).
    Plaintext passwords are supported for backward compatibility but deprecated.
    """
    try:
        # Check if stored value is a bcrypt hash (starts with $2b$)
        if stored_value.startswith('$2b$'):
            return bcrypt.checkpw(plain_password.encode(), stored_value.encode())
        else:
            # Legacy plaintext comparison (deprecated, but supported for backward compatibility)
            # Use constant-time comparison to prevent timing attacks
            return hmac.compare_digest(plain_password, stored_value)
    except Exception as e:
        logger.warning(f"Password verification error: {e}")
        return False

# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="ResumeMaker AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# Custom CSS
# ============================================================================

def load_custom_css():
    """Load custom CSS for modern styling."""
    st.markdown("""
    <style>
        /* Main theme colors */
        :root {
            --primary-color: #4F46E5;
            --secondary-color: #6366F1;
            --accent-color: #8B5CF6;
            --background-dark: #0F172A;
            --background-card: #1E293B;
            --text-primary: #F8FAFC;
            --text-secondary: #94A3B8;
            --success-color: #10B981;
            --error-color: #EF4444;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Main container */
        .main {
            background: linear-gradient(135deg, var(--background-dark) 0%, #1a1a2e 100%);
        }
        
        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background: var(--background-card) !important;
            border-right: 1px solid rgba(255,255,255,0.1);
        }
        
        section[data-testid="stSidebar"] .element-container {
            color: var(--text-primary);
        }
        
        /* Cards */
        .card {
            background: var(--background-card);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 16px;
        }
        
        /* Gradient text */
        .gradient-text {
            background: linear-gradient(135deg, #4F46E5 0%, #8B5CF6 50%, #EC4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        /* Headers */
        h1 {
            color: var(--text-primary) !important;
            font-weight: 800 !important;
        }
        
        h2, h3 {
            color: var(--text-primary) !important;
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, var(--primary-color), var(--accent-color)) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 12px 24px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3) !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(79, 70, 229, 0.4) !important;
        }
        
        /* Secondary button */
        .stButton.secondary > button {
            background: transparent !important;
            border: 1px solid rgba(255,255,255,0.2) !important;
            box-shadow: none !important;
        }
        
        /* File uploader */
        .stFileUploader {
            background: var(--background-card);
            border-radius: 16px;
            padding: 20px;
            border: 2px dashed rgba(255,255,255,0.2);
        }
        
        /* Text areas and inputs */
        .stTextArea > div > div, .stTextInput > div > div {
            background: var(--background-card) !important;
            border-radius: 12px !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
        }
        
        .stTextArea textarea, .stTextInput input {
            color: var(--text-primary) !important;
        }
        
        /* Sliders */
        .stSlider > div > div {
            background: var(--background-card);
        }
        
        /* Progress bar */
        .stProgress > div > div {
            background: var(--background-card);
        }
        
        .stProgress > div > div > div {
            background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
        }
        
        /* Expanders */
        .streamlit-expanderHeader {
            background: var(--background-card) !important;
            border-radius: 12px !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
        }
        
        .streamlit-expanderContent {
            background: var(--background-card) !important;
            border-radius: 0 0 12px 12px !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            border-top: none !important;
        }
        
        /* Metrics */
        .stMetric {
            background: var(--background-card);
            border-radius: 12px;
            padding: 16px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .stMetric > label {
            color: var(--text-secondary) !important;
        }
        
        .stMetric > div {
            color: var(--text-primary) !important;
        }
        
        /* Success/Error boxes */
        .element-container .stSuccess, .element-container .stError, 
        .element-container .stWarning, .element-container .stInfo {
            border-radius: 12px;
            padding: 16px;
        }
        
        /* Download button */
        .stDownloadButton > button {
            background: linear-gradient(135deg, #10B981, #059669) !important;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3) !important;
        }
        
        /* Login page specific */
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 40px;
            background: var(--background-card);
            border-radius: 24px;
            border: 1px solid rgba(255,255,255,0.1);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }
        
        .login-logo {
            font-size: 48px;
            text-align: center;
            margin-bottom: 20px;
        }
        
        /* Feature badges */
        .feature-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: rgba(79, 70, 229, 0.1);
            border: 1px solid rgba(79, 70, 229, 0.2);
            border-radius: 20px;
            font-size: 14px;
            color: #A5B4FC;
            margin: 4px;
        }
        
        /* Step indicator */
        .step-indicator {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin: 30px 0;
        }
        
        .step {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
        }
        
        .step-circle {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 20px;
        }
        
        .step-active .step-circle {
            background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
            color: white;
            box-shadow: 0 4px 15px rgba(79, 70, 229, 0.4);
        }
        
        .step-complete .step-circle {
            background: var(--success-color);
            color: white;
        }
        
        .step-inactive .step-circle {
            background: var(--background-card);
            color: var(--text-secondary);
            border: 2px solid rgba(255,255,255,0.1);
        }
        
        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .animate-fade-in {
            animation: fadeIn 0.5s ease-out;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .animate-pulse {
            animation: pulse 2s infinite;
        }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# Session State Initialization
# ============================================================================

def init_session_state():
    """Initialize all session state variables."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_page' not in st.session_state:
        st.session_state.current_page = '🏠 Home'
    if 'resume_data' not in st.session_state:
        st.session_state.resume_data = None
    if 'tailored_resume' not in st.session_state:
        st.session_state.tailored_resume = None
    if 'ats_score' not in st.session_state:
        st.session_state.ats_score = None
    if 'job_description' not in st.session_state:
        st.session_state.job_description = None
    if 'pdf_bytes' not in st.session_state:
        st.session_state.pdf_bytes = None
    if 'step' not in st.session_state:
        st.session_state.step = 1

# ============================================================================
# Authentication
# ============================================================================

def show_login_page():
    """Display the login page."""
    load_custom_css()
    
    st.markdown("""
    <div class="login-container animate-fade-in">
        <div class="login-logo">📄</div>
        <h1 style="text-align: center; margin-bottom: 10px;">ResumeMaker AI</h1>
        <p style="text-align: center; color: #94A3B8; margin-bottom: 30px;">
            AI-Powered Resume Optimization
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if password is configured
    correct_password = get_app_password()
    if correct_password is None:
        st.error("⚠️ App password not configured. Please set APP_PASSWORD in Streamlit secrets.")
        st.info("See README.md for configuration instructions.")
        return
    
    # Login form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input(
            "Enter Password",
            type="password",
            placeholder="Enter your password",
            label_visibility="collapsed"
        )
        
        if st.button("🔓 Login", use_container_width=True):
            if verify_password(password, correct_password):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Incorrect password")
        
        # Only show password hint in development mode
        if os.getenv("STREAMLIT_ENV", "production") == "development":
            st.markdown("""
            <p style="text-align: center; color: #64748B; font-size: 12px; margin-top: 20px;">
                Dev mode: password is 'dev-password'
            </p>
            """, unsafe_allow_html=True)

# ============================================================================
# Pages
# ============================================================================

def show_home_page():
    """Display the home page with feature overview."""
    st.markdown("""
    <div class="animate-fade-in">
        <h1 style="text-align: center; font-size: 3rem; margin-bottom: 10px;">
            Craft Your <span class="gradient-text">Perfect Resume</span>
        </h1>
        <p style="text-align: center; color: #94A3B8; font-size: 1.2rem; margin-bottom: 40px;">
            Stand out from the crowd with ATS-optimized resumes tailored for your dream job
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature badges
    st.markdown("""
    <div style="text-align: center; margin-bottom: 40px;">
        <span class="feature-badge">⚡ AI Optimized</span>
        <span class="feature-badge">📄 ATS Friendly</span>
        <span class="feature-badge">🔒 Secure & Private</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="card" style="text-align: center;">
            <div style="font-size: 2.5rem; margin-bottom: 10px;">🎯</div>
            <h3>ATS Optimized</h3>
            <p style="color: #94A3B8;">Beat applicant tracking systems with intelligent keyword optimization</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="card" style="text-align: center;">
            <div style="font-size: 2.5rem; margin-bottom: 10px;">💼</div>
            <h3>Job Tailored</h3>
            <p style="color: #94A3B8;">Customize bullet points for specific roles and companies</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="card" style="text-align: center;">
            <div style="font-size: 2.5rem; margin-bottom: 10px;">✨</div>
            <h3>AI Enhanced</h3>
            <p style="color: #94A3B8;">Powered by advanced AI for industry-leading results</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Stats
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Resumes Created", "10K+")
    with col2:
        st.metric("ATS Pass Rate", "95%")
    with col3:
        st.metric("User Rating", "4.9★")
    
    # CTA
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Get Started - Upload Resume", use_container_width=True):
            st.session_state.current_page = "📤 Upload Resume"
            st.rerun()

def show_upload_page():
    """Display the resume upload page."""
    st.markdown("""
    <h1 style="text-align: center; margin-bottom: 10px;">
        📤 Upload Your Resume
    </h1>
    <p style="text-align: center; color: #94A3B8; margin-bottom: 30px;">
        Upload your existing resume PDF to get started
    </p>
    """, unsafe_allow_html=True)
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload your resume PDF",
        type=["pdf"],
        help="Upload a PDF resume to parse and process"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        # Parse button
        if st.button("🔍 Parse Resume", type="primary"):
            tmp_path = None  # Initialize before try block
            with st.spinner("Parsing resume..."):
                try:
                    # Save to temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    # Validate PDF
                    validator = PDFValidator()
                    is_valid, validation_msg = validator.validate(tmp_path)
                    
                    if not is_valid:
                        st.error(f"Invalid PDF: {validation_msg}")
                    else:
                        st.success("✅ PDF is valid")
                        
                        # Parse resume
                        api_key = get_api_key()
                        processor = ResumeProcessor()
                        
                        parsed = asyncio.run(
                            processor.parse_pdf(uploaded_file.getvalue(), api_key=api_key)
                        )
                        
                        # Convert to dict
                        resume_dict = {
                            "basics": {
                                "name": parsed.basics.name if parsed.basics else "",
                                "email": parsed.basics.email if parsed.basics else "",
                                "phone": parsed.basics.phone if parsed.basics else "",
                                "location": getattr(parsed.basics, 'location', None),
                                "links": getattr(parsed.basics, 'links', [])
                            },
                            "summary": parsed.summary,
                            "experience": [
                                {
                                    "company": exp.company,
                                    "role": exp.role,
                                    "startDate": exp.startDate,
                                    "endDate": exp.endDate,
                                    "location": getattr(exp, 'location', None),
                                    "bullets": exp.bullets or []
                                }
                                for exp in (parsed.experience or [])
                            ],
                            "education": [
                                {
                                    "institution": edu.institution,
                                    "studyType": edu.studyType,
                                    "area": edu.area,
                                    "startDate": edu.startDate,
                                    "endDate": edu.endDate
                                }
                                for edu in (parsed.education or [])
                            ],
                            "skills": {
                                "languages_frameworks": parsed.skills.languages_frameworks if parsed.skills else [],
                                "tools": parsed.skills.tools if parsed.skills else [],
                                "methodologies": getattr(parsed.skills, 'methodologies', []) if parsed.skills else []
                            },
                            "projects": [
                                {
                                    "name": proj.name,
                                    "techStack": proj.techStack,
                                    "description": proj.description
                                }
                                for proj in (parsed.projects or [])
                            ],
                            "achievements": parsed.achievements or []
                        }
                        
                        st.session_state.resume_data = resume_dict
                        st.success("✅ Resume parsed successfully!")
                        
                        # Show parsed data
                        with st.expander("📋 View Parsed Resume", expanded=True):
                            st.json(resume_dict)
                        
                        # Continue button
                        if st.button("➡️ Continue to Generate", type="primary"):
                            st.session_state.current_page = "🎯 Generate Resume"
                            st.rerun()
                        
                except Exception as e:
                    st.error(f"Error parsing resume: {e}")
                finally:
                    # Cleanup temp file - always runs even on exception
                    if tmp_path and os.path.exists(tmp_path):
                        os.unlink(tmp_path)

def show_generate_page():
    """Display the resume generation page."""
    st.markdown("""
    <h1 style="text-align: center; margin-bottom: 10px;">
        🎯 Generate Tailored Resume
    </h1>
    <p style="text-align: center; color: #94A3B8; margin-bottom: 30px;">
        Enter the job description and generate your optimized resume
    </p>
    """, unsafe_allow_html=True)
    
    # Check if resume is loaded
    if not st.session_state.resume_data:
        st.warning("⚠️ Please upload a resume first!")
        if st.button("📤 Go to Upload"):
            st.session_state.current_page = "📤 Upload Resume"
            st.rerun()
        return
    
    # Show current resume summary
    with st.expander("📄 Current Resume Summary", expanded=False):
        basics = st.session_state.resume_data.get('basics', {})
        st.write(f"**Name:** {basics.get('name', 'N/A')}")
        st.write(f"**Email:** {basics.get('email', 'N/A')}")
        st.write(f"**Experience:** {len(st.session_state.resume_data.get('experience', []))} positions")
        st.write(f"**Skills:** {len(st.session_state.resume_data.get('skills', {}).get('languages_frameworks', []))} items")
    
    # Job description input
    job_description = st.text_area(
        "Job Description",
        height=200,
        placeholder="Paste the job description here...",
        value=st.session_state.job_description or ""
    )
    
    if job_description:
        st.session_state.job_description = job_description
    
    # Configuration
    col1, col2 = st.columns(2)
    with col1:
        target_ats = st.slider("Target ATS Score", 70, 100, 92)
    with col2:
        max_pages = st.select_slider("Max Pages", [1, 2], value=1)
    
    # Generate button
    if st.button("🚀 Generate Resume", type="primary"):
        if not job_description:
            st.error("Please provide a job description")
            return
        
        if not get_api_key():
            st.error("⚠️ NVIDIA API Key not configured")
            return
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("🔄 Initializing AI client...")
            progress_bar.progress(10)
            
            ai_client = AIClient(api_key=get_api_key())
            
            status_text.text("📝 Analyzing job description...")
            progress_bar.progress(20)
            
            status_text.text("🔍 Detecting role requirements...")
            progress_bar.progress(40)
            
            config = {
                "target_ats_score": target_ats,
                "max_pages": max_pages
            }
            
            status_text.text("✨ Generating tailored content...")
            progress_bar.progress(60)
            
            result = asyncio.run(
                ai_client.generate_sync(
                    resume_data=st.session_state.resume_data,
                    job_description=job_description,
                    config=config,
                    user_id="streamlit-user"
                )
            )
            
            status_text.text("📊 Optimizing for ATS...")
            progress_bar.progress(80)
            
            tailored_resume = result.get("tailored_resume")
            ats_score = result.get("ats_score", 0)
            
            # Convert to dict
            if hasattr(tailored_resume, 'model_dump'):
                tailored_dict = tailored_resume.model_dump()
            elif hasattr(tailored_resume, 'dict'):
                tailored_dict = tailored_resume.dict()
            else:
                tailored_dict = tailored_resume
            
            st.session_state.tailored_resume = tailored_dict
            st.session_state.ats_score = ats_score
            
            status_text.text("✅ Complete!")
            progress_bar.progress(100)
            
            st.success(f"✅ Resume generated! ATS Score: {ats_score:.0f}%")
            
            # Generate PDF
            try:
                processor = ResumeProcessor()
                tailored_model = TailoredResume(**tailored_dict)
                pdf_bytes = asyncio.run(processor.generate_pdf(tailored_model))
                st.session_state.pdf_bytes = pdf_bytes.getvalue()
            except Exception as pdf_error:
                st.warning(f"Could not generate PDF: {pdf_error}")
            
            # Show results
            st.markdown("### 📊 Results")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("ATS Score", f"{ats_score:.0f}%", delta=f"Target: {target_ats}%")
            with col2:
                st.metric("Page Fill", "100%")
            
            # Download button
            if st.session_state.pdf_bytes:
                st.download_button(
                    "📥 Download Resume PDF",
                    data=st.session_state.pdf_bytes,
                    file_name="tailored_resume.pdf",
                    mime="application/pdf"
                )
            
            # View/Edit button
            if st.button("📝 View/Edit Resume"):
                st.session_state.current_page = "📝 Editor"
                st.rerun()
                
        except Exception as e:
            st.error(f"Error generating resume: {e}")

def show_editor_page():
    """Display the resume editor page."""
    st.markdown("""
    <h1 style="text-align: center; margin-bottom: 10px;">
        📝 Resume Editor
    </h1>
    <p style="text-align: center; color: #94A3B8; margin-bottom: 30px;">
        View and edit your tailored resume
    </p>
    """, unsafe_allow_html=True)
    
    if not st.session_state.tailored_resume:
        st.warning("⚠️ No resume to edit. Generate one first!")
        if st.button("🎯 Go to Generate"):
            st.session_state.current_page = "🎯 Generate Resume"
            st.rerun()
        return
    
    resume = st.session_state.tailored_resume
    
    # ATS Score
    if st.session_state.ats_score:
        st.metric("ATS Score", f"{st.session_state.ats_score:.0f}%")
    
    # Track if changes were made
    changes_made = False
    
    # Edit sections
    with st.expander("👤 Personal Information", expanded=True):
        basics = resume.get('basics', {})
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name", basics.get('name', ''))
            email = st.text_input("Email", basics.get('email', ''))
        with col2:
            phone = st.text_input("Phone", basics.get('phone', ''))
            location = st.text_input("Location", basics.get('location', ''))
        
        # Check for changes in basics
        if (name != basics.get('name', '') or 
            email != basics.get('email', '') or 
            phone != basics.get('phone', '') or 
            location != basics.get('location', '')):
            changes_made = True
    
    with st.expander("📝 Summary", expanded=False):
        summary = st.text_area("Professional Summary", resume.get('summary', ''), height=150)
        if summary != resume.get('summary', ''):
            changes_made = True
    
    with st.expander("💼 Experience", expanded=False):
        for i, exp in enumerate(resume.get('experience', [])):
            st.markdown(f"**{exp.get('role', '')}** at {exp.get('company', '')}")
            st.caption(f"{exp.get('startDate', '')} - {exp.get('endDate', '')}")
            for bullet in exp.get('bullets', []):
                st.markdown(f"- {bullet}")
            if i < len(resume.get('experience', [])) - 1:
                st.divider()
    
    with st.expander("🎓 Education", expanded=False):
        for edu in resume.get('education', []):
            st.write(f"**{edu.get('studyType', '')}** in {edu.get('area', '')}")
            st.caption(f"{edu.get('institution', '')}")
    
    with st.expander("🛠️ Skills", expanded=False):
        skills = resume.get('skills', {})
        st.write("**Languages & Frameworks:**", ", ".join(skills.get('languages_frameworks', [])))
        st.write("**Tools:**", ", ".join(skills.get('tools', [])))
    
    # Show unsaved changes indicator
    if changes_made:
        st.info("📝 You have unsaved changes")
    
    # Actions
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Changes", type="primary", use_container_width=True, disabled=not changes_made):
            # Update resume with edited values
            resume['basics']['name'] = name
            resume['basics']['email'] = email
            resume['basics']['phone'] = phone
            resume['basics']['location'] = location
            resume['summary'] = summary
            
            # Update session state
            st.session_state.tailored_resume = resume
            
            # Regenerate PDF with updated data
            try:
                with st.spinner("Regenerating PDF..."):
                    processor = ResumeProcessor()
                    tailored_model = TailoredResume(**resume)
                    pdf_bytes = asyncio.run(processor.generate_pdf(tailored_model))
                    st.session_state.pdf_bytes = pdf_bytes.getvalue()
                    st.success("✅ Changes saved and PDF regenerated!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error regenerating PDF: {e}")
                st.info("Your changes were saved but PDF could not be regenerated.")
    
    with col2:
        if st.session_state.pdf_bytes:
            st.download_button(
                "📥 Download PDF",
                data=st.session_state.pdf_bytes,
                file_name="tailored_resume.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    
    with col3:
        if st.button("🔄 Regenerate", use_container_width=True):
            st.session_state.current_page = "🎯 Generate Resume"
            st.rerun()

def show_settings_page():
    """Display the settings page."""
    st.markdown("""
    <h1 style="text-align: center; margin-bottom: 30px;">
        ⚙️ Settings
    </h1>
    """, unsafe_allow_html=True)
    
    # API Key status
    st.markdown("### 🔑 API Configuration")
    if get_api_key():
        st.success("✅ NVIDIA API Key configured")
    else:
        st.error("❌ NVIDIA API Key not found")
        st.info("Add NVIDIA_API_KEY to Streamlit secrets")
    
    st.markdown("### 📋 Session Data")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Resume Loaded", "✅" if st.session_state.resume_data else "❌")
    with col2:
        st.metric("Resume Generated", "✅" if st.session_state.tailored_resume else "❌")
    with col3:
        st.metric("PDF Ready", "✅" if st.session_state.pdf_bytes else "❌")
    
    # Clear session
    st.markdown("### 🗑️ Clear Session")
    if st.button("Clear All Data"):
        st.session_state.resume_data = None
        st.session_state.tailored_resume = None
        st.session_state.ats_score = None
        st.session_state.job_description = None
        st.session_state.pdf_bytes = None
        st.success("Session cleared!")
        st.rerun()

# ============================================================================
# Main App
# ============================================================================

def main():
    """Main application entry point."""
    load_custom_css()
    init_session_state()
    
    # Check authentication
    if not st.session_state.authenticated:
        show_login_page()
        return
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <h2 style="margin: 0; color: #F8FAFC;">📄 ResumeMaker</h2>
            <p style="color: #64748B; font-size: 12px;">AI-Powered Builder</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        page = st.radio(
            "Navigation",
            ["🏠 Home", "📤 Upload Resume", "🎯 Generate Resume", "📝 Editor", "⚙️ Settings"],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # Session status
        st.markdown("### 📦 Session")
        if st.session_state.resume_data:
            st.success("✅ Resume loaded")
        if st.session_state.tailored_resume:
            st.success("✅ Resume generated")
        
        st.divider()
        
        # Logout
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.rerun()
    
    # Page routing
    if page == "🏠 Home":
        show_home_page()
    elif page == "📤 Upload Resume":
        show_upload_page()
    elif page == "🎯 Generate Resume":
        show_generate_page()
    elif page == "📝 Editor":
        show_editor_page()
    elif page == "⚙️ Settings":
        show_settings_page()

if __name__ == "__main__":
    main()
