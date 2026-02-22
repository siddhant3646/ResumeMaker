"""
ResumeMaker AI - Streamlit Backend Service
Hybrid Architecture: Vercel Frontend + Streamlit Backend
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

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

# Import application modules
from backend.app.resume import ResumeProcessor
from backend.app.ai_client import AIClient, convert_app_to_core
from backend.app.models import TailoredResume
from intelligence.ats_scorer import ATSScorer
from intelligence.content_generator import ContentGenerator
from intelligence.role_detector import RoleDetector
from vision.pdf_validator import PDFValidator

# Page configuration
st.set_page_config(
    page_title="ResumeMaker AI - Backend Service",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4F46E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #6366F1;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #D1FAE5;
        border: 1px solid #10B981;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #FEE2E2;
        border: 1px solid #EF4444;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #DBEAFE;
        border: 1px solid #3B82F6;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'resume_data' not in st.session_state:
    st.session_state.resume_data = None
if 'ats_score' not in st.session_state:
    st.session_state.ats_score = None
if 'tailored_resume' not in st.session_state:
    st.session_state.tailored_resume = None
if 'job_description' not in st.session_state:
    st.session_state.job_description = None
if 'pdf_bytes' not in st.session_state:
    st.session_state.pdf_bytes = None


def get_api_key() -> Optional[str]:
    """Get NVIDIA API key from environment or secrets."""
    # Try Streamlit secrets first
    try:
        if hasattr(st, 'secrets') and 'NVIDIA_API_KEY' in st.secrets:
            return st.secrets['NVIDIA_API_KEY']
    except:
        pass
    
    # Fall back to environment variable
    return os.getenv('NVIDIA_API_KEY')


def init_services():
    """Initialize AI services."""
    api_key = get_api_key()
    if not api_key:
        st.error("⚠️ NVIDIA API Key not configured. Please set NVIDIA_API_KEY in environment or Streamlit secrets.")
        return None, None, None
    
    try:
        ats_scorer = ATSScorer(api_key=api_key)
        content_generator = ContentGenerator(api_key=api_key)
        role_detector = RoleDetector(api_key=api_key)
        return ats_scorer, content_generator, role_detector
    except Exception as e:
        st.error(f"Error initializing services: {e}")
        return None, None, None


def get_ai_client() -> Optional[AIClient]:
    """Get AI client instance."""
    api_key = get_api_key()
    if not api_key:
        return None
    return AIClient(api_key=api_key)


# Global resume processor
resume_processor = ResumeProcessor()


def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<h1 class="main-header">📄 ResumeMaker AI Backend</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #64748B;">Hybrid Architecture - Processing Service</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key status
        api_key = get_api_key()
        if api_key:
            st.success("✅ NVIDIA API Key configured")
        else:
            st.error("❌ NVIDIA API Key not found")
            st.info("Set NVIDIA_API_KEY in environment or Streamlit secrets")
        
        st.divider()
        
        # Navigation
        st.header("📋 Navigation")
        page = st.radio(
            "Select Function",
            ["🏠 Home", "📤 Upload Resume", "🎯 Generate Resume", "📊 ATS Score", "ℹ️ API Info"],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # Session state info
        st.header("📦 Session Data")
        if st.session_state.resume_data:
            st.success("✅ Resume loaded")
        if st.session_state.job_description:
            st.success("✅ Job description set")
        if st.session_state.tailored_resume:
            st.success("✅ Tailored resume ready")
    
    # Main content based on selected page
    if page == "🏠 Home":
        show_home_page()
    elif page == "📤 Upload Resume":
        show_upload_page()
    elif page == "🎯 Generate Resume":
        show_generate_page()
    elif page == "📊 ATS Score":
        show_ats_page()
    elif page == "ℹ️ API Info":
        show_api_info_page()


def show_home_page():
    """Display home page with overview."""
    st.markdown('<h2 class="sub-header">Welcome to ResumeMaker AI Backend</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    This is the <strong>backend processing service</strong> for ResumeMaker AI. 
    It works in conjunction with the Vercel-hosted React frontend.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Resume Upload", "✅", help="Upload and parse PDF resumes")
    
    with col2:
        st.metric("AI Generation", "✅", help="Generate tailored resumes using NVIDIA AI")
    
    with col3:
        st.metric("ATS Scoring", "✅", help="Score resumes against job descriptions")
    
    st.divider()
    
    st.markdown("### 🚀 Quick Start")
    st.markdown("""
    1. **Upload Resume**: Go to 'Upload Resume' to parse your existing resume
    2. **Generate Resume**: Use AI to tailor your resume for a specific job
    3. **ATS Score**: Check how well your resume matches a job description
    """)
    
    st.divider()
    
    st.markdown("### 🔗 API Endpoints")
    st.code("""
# Health Check
GET /api/health

# Upload Resume
POST /api/resume/upload

# Generate Resume
POST /api/resume/generate

# Get ATS Score
POST /api/resume/score
    """, language="bash")


def show_upload_page():
    """Display resume upload page."""
    st.markdown('<h2 class="sub-header">📤 Upload Resume</h2>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Upload your resume PDF",
        type=["pdf"],
        help="Upload a PDF resume to parse and process"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        # Parse resume
        if st.button("🔍 Parse Resume", type="primary"):
            with st.spinner("Parsing resume..."):
                tmp_path = None
                try:
                    # Save to temporary file for validation
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    # Initialize PDF validator
                    validator = PDFValidator()
                    
                    # Validate PDF
                    is_valid, validation_msg = validator.validate(tmp_path)
                    
                    if not is_valid:
                        st.error(f"Invalid PDF: {validation_msg}")
                    else:
                        st.success("✅ PDF is valid")
                        
                        # Parse resume using actual ResumeProcessor
                        api_key = get_api_key()
                        content = uploaded_file.getvalue()
                        
                        parsed_resume = asyncio.run(
                            resume_processor.parse_pdf(content, api_key=api_key)
                        )
                        
                        # Convert to dict for storage
                        resume_dict = {
                            "basics": {
                                "name": parsed_resume.basics.name if parsed_resume.basics else "",
                                "email": parsed_resume.basics.email if parsed_resume.basics else "",
                                "phone": parsed_resume.basics.phone if parsed_resume.basics else "",
                                "location": getattr(parsed_resume.basics, 'location', None),
                                "links": getattr(parsed_resume.basics, 'links', [])
                            },
                            "summary": parsed_resume.summary,
                            "experience": [
                                {
                                    "company": exp.company,
                                    "role": exp.role,
                                    "startDate": exp.startDate,
                                    "endDate": exp.endDate,
                                    "location": getattr(exp, 'location', None),
                                    "bullets": exp.bullets or []
                                }
                                for exp in (parsed_resume.experience or [])
                            ],
                            "education": [
                                {
                                    "institution": edu.institution,
                                    "studyType": edu.studyType,
                                    "area": edu.area,
                                    "startDate": edu.startDate,
                                    "endDate": edu.endDate,
                                    "location": getattr(edu, 'location', None)
                                }
                                for edu in (parsed_resume.education or [])
                            ],
                            "skills": {
                                "languages_frameworks": parsed_resume.skills.languages_frameworks if parsed_resume.skills else [],
                                "tools": parsed_resume.skills.tools if parsed_resume.skills else [],
                                "methodologies": getattr(parsed_resume.skills, 'methodologies', []) if parsed_resume.skills else []
                            },
                            "projects": [
                                {
                                    "name": proj.name,
                                    "techStack": proj.techStack,
                                    "description": proj.description
                                }
                                for proj in (parsed_resume.projects or [])
                            ],
                            "achievements": parsed_resume.achievements or []
                        }
                        
                        # Store in session state
                        st.session_state.resume_data = resume_dict
                        
                        st.success("✅ Resume parsed successfully!")
                        
                        # Display parsed data
                        st.markdown("### 📋 Parsed Resume Data")
                        
                        with st.expander("👤 Personal Information", expanded=True):
                            st.write(f"**Name:** {resume_dict['basics']['name']}")
                            st.write(f"**Email:** {resume_dict['basics']['email']}")
                            st.write(f"**Phone:** {resume_dict['basics']['phone']}")
                            if resume_dict['basics'].get('location'):
                                st.write(f"**Location:** {resume_dict['basics']['location']}")
                        
                        with st.expander("💼 Experience", expanded=False):
                            for i, exp in enumerate(resume_dict['experience']):
                                st.markdown(f"**{exp['role']}** at {exp['company']}")
                                st.caption(f"{exp['startDate']} - {exp['endDate']}")
                                for bullet in exp['bullets']:
                                    st.markdown(f"- {bullet}")
                                if i < len(resume_dict['experience']) - 1:
                                    st.divider()
                        
                        with st.expander("🎓 Education", expanded=False):
                            for edu in resume_dict['education']:
                                st.write(f"**{edu['studyType']}** in {edu['area']}")
                                st.caption(f"{edu['institution']} ({edu['startDate']} - {edu['endDate']})")
                        
                        with st.expander("🛠️ Skills", expanded=False):
                            skills = resume_dict['skills']
                            st.write("**Languages & Frameworks:**", ", ".join(skills['languages_frameworks']) if skills['languages_frameworks'] else "None")
                            st.write("**Tools:**", ", ".join(skills['tools']) if skills['tools'] else "None")
                        
                except Exception as e:
                    st.error(f"Error parsing resume: {e}")
                finally:
                    # Cleanup temp file
                    if tmp_path and os.path.exists(tmp_path):
                        os.unlink(tmp_path)


def show_generate_page():
    """Display resume generation page."""
    st.markdown('<h2 class="sub-header">🎯 Generate Tailored Resume</h2>', unsafe_allow_html=True)
    
    # Check if resume is loaded
    if not st.session_state.resume_data:
        st.warning("⚠️ Please upload a resume first!")
        st.info("Go to 'Upload Resume' to parse your resume.")
        return
    
    # Show current resume info
    with st.expander("📄 Current Resume", expanded=False):
        st.json(st.session_state.resume_data['basics'])
    
    # Job description input
    job_description = st.text_area(
        "Job Description",
        height=200,
        placeholder="Paste the job description here...",
        value=st.session_state.job_description or ""
    )
    
    if job_description:
        st.session_state.job_description = job_description
    
    # Generation options
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
        
        # Check API key
        if not get_api_key():
            st.error("⚠️ NVIDIA API Key not configured. Cannot generate resume.")
            return
        
        with st.spinner("Generating tailored resume..."):
            try:
                # Initialize AI client
                ai_client = get_ai_client()
                
                if not ai_client:
                    st.error("Failed to initialize AI client")
                    return
                
                # Progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("Analyzing job description...")
                progress_bar.progress(20)
                
                status_text.text("Detecting role requirements...")
                progress_bar.progress(40)
                
                # Call actual generation
                config = {
                    "target_ats_score": target_ats,
                    "max_pages": max_pages
                }
                
                status_text.text("Generating tailored content...")
                progress_bar.progress(60)
                
                result = asyncio.run(
                    ai_client.generate_sync(
                        resume_data=st.session_state.resume_data,
                        job_description=job_description,
                        config=config,
                        user_id="streamlit-user"
                    )
                )
                
                status_text.text("Optimizing for ATS...")
                progress_bar.progress(80)
                
                tailored_resume = result.get("tailored_resume")
                ats_score = result.get("ats_score", 0)
                
                # Convert to dict if needed
                if hasattr(tailored_resume, 'model_dump'):
                    tailored_dict = tailored_resume.model_dump()
                elif hasattr(tailored_resume, 'dict'):
                    tailored_dict = tailored_resume.dict()
                else:
                    tailored_dict = tailored_resume
                
                st.session_state.tailored_resume = tailored_dict
                st.session_state.ats_score = ats_score
                
                status_text.text("Finalizing resume...")
                progress_bar.progress(100)
                
                st.success("✅ Resume generated successfully!")
                
                # Show results
                st.markdown("### 📊 Generation Results")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("ATS Score", f"{ats_score:.0f}%", delta=f"Target: {target_ats}%")
                with col2:
                    page_status = result.get("page_status", {})
                    if isinstance(page_status, dict):
                        fill_pct = page_status.get('fill_percentage', 100)
                        st.metric("Page Fill", f"{fill_pct}%")
                
                # Generate PDF for download
                if tailored_dict:
                    try:
                        tailored_model = TailoredResume(**tailored_dict)
                        pdf_bytes = asyncio.run(resume_processor.generate_pdf(tailored_model))
                        st.session_state.pdf_bytes = pdf_bytes.getvalue()
                    except Exception as pdf_error:
                        st.warning(f"Could not generate PDF: {pdf_error}")
                
                # Download button
                if st.session_state.pdf_bytes:
                    st.download_button(
                        "📥 Download Resume PDF",
                        data=st.session_state.pdf_bytes,
                        file_name="tailored_resume.pdf",
                        mime="application/pdf"
                    )
                
                # Show tailored resume details
                with st.expander("📝 View Tailored Resume", expanded=False):
                    st.json(tailored_dict)
                
            except Exception as e:
                st.error(f"Error generating resume: {e}")
                import traceback
                st.code(traceback.format_exc())


def show_ats_page():
    """Display ATS scoring page."""
    st.markdown('<h2 class="sub-header">📊 ATS Score Analysis</h2>', unsafe_allow_html=True)
    
    # Option to use session resume or paste text
    use_session_resume = st.checkbox(
        "Use uploaded resume", 
        value=st.session_state.resume_data is not None,
        disabled=st.session_state.resume_data is None
    )
    
    if use_session_resume and st.session_state.resume_data:
        # Convert resume data to text for scoring
        resume_text = json.dumps(st.session_state.resume_data, indent=2)
        st.text_area("Resume Content", value=resume_text, height=150, disabled=True)
    else:
        # Resume input
        resume_text = st.text_area(
            "Resume Content",
            height=150,
            placeholder="Paste your resume content here..."
        )
    
    # Job description input
    job_description = st.text_area(
        "Job Description",
        height=150,
        placeholder="Paste the job description here..."
    )
    
    if st.button("📊 Calculate ATS Score", type="primary"):
        if not resume_text or not job_description:
            st.error("Please provide both resume and job description")
            return
        
        if not get_api_key():
            st.error("⚠️ NVIDIA API Key not configured. Cannot calculate ATS score.")
            return
        
        with st.spinner("Calculating ATS score..."):
            try:
                # Initialize ATS scorer
                ats_scorer, _, _ = init_services()
                
                if not ats_scorer:
                    st.error("Failed to initialize ATS scorer")
                    return
                
                # Use actual ATS scoring
                result = ats_scorer.score_resume(
                    resume_text=resume_text,
                    job_description=job_description
                )
                
                score = result.get("score", result.get("overall_score", 0))
                
                # Display results
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Overall Score", f"{score}%")
                
                with col2:
                    keyword_match = result.get("keyword_match", 0)
                    st.metric("Keyword Match", f"{keyword_match}%")
                
                with col3:
                    format_score = result.get("format_score", 95)
                    st.metric("Format Score", f"{format_score}%")
                
                # Detailed analysis
                st.markdown("### 📋 Detailed Analysis")
                
                matched = result.get("matched_keywords", [])
                missing = result.get("missing_keywords", [])
                suggestions = result.get("suggestions", [])
                
                if matched:
                    st.markdown("""
                    <div class="success-box">
                    <strong>Matched Keywords:</strong><br>
                    """ + ", ".join(matched) + """
                    </div>
                    """, unsafe_allow_html=True)
                
                if missing:
                    st.markdown("""
                    <div class="error-box">
                    <strong>Missing Keywords:</strong><br>
                    """ + ", ".join(missing) + """
                    </div>
                    """, unsafe_allow_html=True)
                
                if suggestions:
                    st.markdown("### 💡 Suggestions for Improvement")
                    for suggestion in suggestions:
                        st.markdown(f"- {suggestion}")
                
            except Exception as e:
                st.error(f"Error calculating ATS score: {e}")
                import traceback
                st.code(traceback.format_exc())


def show_api_info_page():
    """Display API information for frontend integration."""
    st.markdown('<h2 class="sub-header">ℹ️ API Information</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    This page provides information for integrating the React frontend with this Streamlit backend.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🔗 API Endpoints")
    
    # Health endpoint
    with st.expander("GET /api/health", expanded=False):
        st.markdown("**Description:** Check backend health status")
        st.code("""
Response:
{
    "status": "healthy",
    "version": "2.0.0",
    "service": "resumemaker-streamlit-backend"
}
        """, language="json")
    
    # Upload endpoint
    with st.expander("POST /api/resume/upload", expanded=False):
        st.markdown("**Description:** Upload and parse a resume PDF")
        st.code("""
Request:
Content-Type: multipart/form-data
Body: file (PDF)

Response:
{
    "success": true,
    "message": "Resume parsed successfully",
    "resume_data": { ... }
}
        """, language="json")
    
    # Generate endpoint
    with st.expander("POST /api/resume/generate", expanded=False):
        st.markdown("**Description:** Generate a tailored resume")
        st.code("""
Request:
Content-Type: application/json
Body:
{
    "resume_data": { ... },
    "job_description": "...",
    "config": {
        "target_ats_score": 92,
        "max_pages": 1
    }
}

Response:
{
    "success": true,
    "tailored_resume": { ... },
    "ats_score": 94
}
        """, language="json")
    
    # Score endpoint
    with st.expander("POST /api/resume/score", expanded=False):
        st.markdown("**Description:** Calculate ATS score")
        st.code("""
Request:
Content-Type: application/json
Body:
{
    "resume_text": "...",
    "job_description": "..."
}

Response:
{
    "score": 85,
    "keyword_match": 78,
    "format_score": 95,
    "suggestions": [...],
    "matched_keywords": [...],
    "missing_keywords": [...]
}
        """, language="json")
    
    # Download endpoint
    with st.expander("POST /api/resume/download", expanded=False):
        st.markdown("**Description:** Download resume as PDF")
        st.code("""
Request:
Content-Type: application/json
Body: { ... tailored resume data ... }

Response:
Content-Type: application/pdf
Body: PDF binary data
        """, language="json")
    
    st.markdown("### 🔧 Frontend Configuration")
    st.markdown("""
To use this backend with the React frontend, set these environment variables:
    
```bash
# In frontend/.env.local
VITE_STREAMLIT_BACKEND=true
VITE_API_URL=http://localhost:8001  # or your deployed URL
```
    """)


if __name__ == "__main__":
    main()
