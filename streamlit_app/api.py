"""
ResumeMaker AI - FastAPI Wrapper for Streamlit Backend
This module provides REST API endpoints that the React frontend can call.
It wraps the Streamlit backend processing logic.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import tempfile
import logging
from io import BytesIO
from pathlib import Path
import sys

# Add parent directory to path for imports
BASE_DIR = Path(__file__).resolve().parent.parent

# Verify required directories exist
BACKEND_DIR = BASE_DIR / "backend"
if not BACKEND_DIR.exists():
    raise RuntimeError(f"Backend directory not found at: {BACKEND_DIR}")

sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv()

# Validate required environment variables
required_env_vars = [
    "NVIDIA_API_KEY",
    "AUTH0_DOMAIN",
    "AUTH0_CLIENT_ID",
    "AUTH0_CLIENT_SECRET"
]

for var in required_env_vars:
    if not os.getenv(var):
        raise RuntimeError(f"Required environment variable '{var}' is not set")

# Import application modules
from backend.app.resume import ResumeProcessor
from backend.app.ai_client import AIClient, convert_app_to_core, validate_tailored_resume
from backend.app.models import (
    ParsedResume, Basics, Experience, Education, Skills, Project, TailoredResume
)
from intelligence.ats_scorer import ATSScorer
from intelligence.content_generator import ContentGenerator
from intelligence.role_detector import RoleDetector
from vision.pdf_validator import PDFValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Pydantic Models
# ============================================================================

class HealthResponse(BaseModel):
    status: str
    version: str
    service: str


class ResumeUploadResponse(BaseModel):
    success: bool
    message: str
    resume_data: Optional[Dict[str, Any]] = None
    filename: Optional[str] = None


class JobDescriptionRequest(BaseModel):
    job_description: str


class GenerationConfig(BaseModel):
    target_ats_score: int = 92
    max_pages: int = 1
    include_summary: bool = True
    highlight_skills: bool = True


class GenerationRequest(BaseModel):
    resume_data: Dict[str, Any]
    job_description: str
    config: Optional[GenerationConfig] = GenerationConfig()


class GenerationResponse(BaseModel):
    success: bool
    message: str
    tailored_resume: Optional[Dict[str, Any]] = None
    ats_score: Optional[int] = None
    page_status: Optional[str] = None


class ATSScoreRequest(BaseModel):
    resume_text: str
    job_description: str


class ATSScoreResponse(BaseModel):
    score: int
    keyword_match: int
    format_score: int
    suggestions: List[str]
    matched_keywords: List[str]
    missing_keywords: List[str]


class RegenerateRequest(BaseModel):
    resume_data: Dict[str, Any]
    job_description: str
    attempt: int = 2
    force_variation: bool = False


class ConsolidateRequest(BaseModel):
    resume_data: Dict[str, Any]
    job_description: str = ""


class ImproveTextRequest(BaseModel):
    original_text: str
    user_prompt: str
    context: str = "resume content"


class CheckATSScoreRequest(BaseModel):
    resume_data: Dict[str, Any]


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="ResumeMaker AI - Streamlit Backend API",
    description="REST API wrapper for Streamlit backend processing",
    version="2.0.0"
)

# CORS Configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Allow all origins if FRONTEND_URL is set to "*"
if FRONTEND_URL == "*":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            FRONTEND_URL,
            "http://localhost:5173",
            "http://localhost:3000",
            "https://resume-maker2-one.vercel.app",
            "https://resume-maker1-rust.vercel.app"
        ],
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# ============================================================================
# Service Initialization
# ============================================================================

def get_api_key() -> Optional[str]:
    """Get NVIDIA API key from environment."""
    return os.getenv('NVIDIA_API_KEY')


# Initialize global services
resume_processor = ResumeProcessor()


def get_ai_client() -> AIClient:
    """Get AI client instance."""
    api_key = get_api_key()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured - NVIDIA_API_KEY not set"
        )
    return AIClient(api_key=api_key)


def get_services():
    """Initialize and return AI services."""
    api_key = get_api_key()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured - NVIDIA_API_KEY not set"
        )
    
    try:
        ats_scorer = ATSScorer(api_key=api_key)
        content_generator = ContentGenerator(api_key=api_key)
        role_detector = RoleDetector(api_key=api_key)
        return ats_scorer, content_generator, role_detector
    except Exception as e:
        logger.error(f"Error initializing services: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initializing AI services: {str(e)}"
        )


# ============================================================================
# Health Check
# ============================================================================

@app.get("/", response_model=HealthResponse)
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        service="resumemaker-streamlit-backend"
    )


# ============================================================================
# Resume Upload & Parsing
# ============================================================================

@app.post("/api/resume/upload", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    """Upload and parse a resume PDF"""
    try:
        # Validate file type
        if not file.content_type or "pdf" not in file.content_type.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported"
            )
        
        # Read file content
        content = await file.read()
        
        if len(content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds 10MB limit"
            )
        
        # Validate PDF
        validator = PDFValidator()
        
        # Save to temp file for validation
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            is_valid, validation_msg = validator.validate(tmp_path)
            
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid PDF: {validation_msg}"
                )
            
            # Parse resume using the actual ResumeProcessor
            api_key = get_api_key()
            parsed_resume = await resume_processor.parse_pdf(content, api_key=api_key)
            
            # Convert ParsedResume to dict for JSON serialization
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
            
            return ResumeUploadResponse(
                success=True,
                message="Resume parsed successfully",
                resume_data=resume_dict,
                filename=file.filename
            )
            
        finally:
            # Cleanup temp file
            os.unlink(tmp_path)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing resume: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error parsing resume: {str(e)}"
        )


# ============================================================================
# Resume Generation
# ============================================================================

@app.post("/api/resume/generate")
async def generate_resume(request: GenerationRequest):
    """Generate a tailored resume using AI"""
    try:
        # Initialize AI client
        ai_client = get_ai_client()
        
        logger.info(f"Generating resume for job description: {request.job_description[:100]}...")
        
        # Use the actual AI client for generation
        result = await ai_client.generate_sync(
            resume_data=request.resume_data,
            job_description=request.job_description,
            config=request.config.model_dump() if request.config else None,
            user_id="streamlit-user"
        )
        
        # Convert TailoredResume to dict if needed
        tailored_resume = result.get("tailored_resume")
        if hasattr(tailored_resume, 'model_dump'):
            tailored_dict = tailored_resume.model_dump()
        elif hasattr(tailored_resume, 'dict'):
            tailored_dict = tailored_resume.dict()
        else:
            tailored_dict = tailored_resume
        
        return {
            "success": result.get("success", True),
            "job_id": "sync",
            "status": "completed",
            "tailored_resume": tailored_dict,
            "ats_score": result.get("ats_score"),
            "page_status": result.get("page_status"),
            "continue_reason": result.get("continue_reason"),
            "validation_issues": result.get("validation_issues", []),
            "message": f"ATS Score: {result.get('ats_score', 0):.0f}" + (
                f", Page: {result.get('page_status', {}).get('fill_percentage', 100)}%" 
                if result.get('page_status') else ""
            ),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating resume: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating resume: {str(e)}"
        )


@app.post("/api/resume/regenerate")
async def regenerate_resume(request: RegenerateRequest):
    """Single improvement pass using ATS feedback from a previous result."""
    try:
        ai_client = get_ai_client()
        
        result = await ai_client.regenerate_single_pass(
            previous_resume=request.resume_data,
            job_description=request.job_description,
            attempt=request.attempt,
            user_id="streamlit-user"
        )
        
        # Convert TailoredResume to dict if needed
        tailored_resume = result.get("tailored_resume")
        if hasattr(tailored_resume, 'model_dump'):
            tailored_dict = tailored_resume.model_dump()
        elif hasattr(tailored_resume, 'dict'):
            tailored_dict = tailored_resume.dict()
        else:
            tailored_dict = tailored_resume
        
        return {
            "success": result.get("success", True),
            "tailored_resume": tailored_dict,
            "ats_score": result.get("ats_score"),
            "page_status": result.get("page_status"),
            "continue_reason": result.get("continue_reason"),
            "validation_issues": result.get("validation_issues", []),
            "message": f"ATS Score: {result.get('ats_score', 0):.0f}" + (
                f", Page: {result.get('page_status', {}).get('fill_percentage', 100)}%" 
                if result.get('page_status') else ""
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating resume: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error regenerating: {str(e)}"
        )


@app.post("/api/resume/consolidate")
async def consolidate_resume(request: ConsolidateRequest):
    """Consolidate resume for sparse trailing pages."""
    try:
        ai_client = get_ai_client()
        
        result = await ai_client.consolidate_resume(
            resume_data=request.resume_data,
            job_description=request.job_description,
            user_id="streamlit-user"
        )
        
        # Convert TailoredResume to dict if needed
        tailored_resume = result.get("tailored_resume")
        if hasattr(tailored_resume, 'model_dump'):
            tailored_dict = tailored_resume.model_dump()
        elif hasattr(tailored_resume, 'dict'):
            tailored_dict = tailored_resume.dict()
        else:
            tailored_dict = tailored_resume
        
        return {
            "success": True,
            "tailored_resume": tailored_dict,
            "ats_score": result.get("ats_score"),
            "message": result.get("message", "Resume consolidated")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error consolidating resume: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error consolidating: {str(e)}"
        )


@app.post("/api/resume/optimize-ats")
async def optimize_resume_ats(request: CheckATSScoreRequest):
    """Optimize resume for ATS without job description (ATS-only mode)"""
    try:
        ai_client = get_ai_client()
        
        result = await ai_client.optimize_for_ats(
            resume_data=request.resume_data,
            user_id="streamlit-user"
        )
        
        # Convert to dict if needed
        if hasattr(result, 'model_dump'):
            result = result.model_dump()
        elif hasattr(result, 'dict'):
            result = result.dict()
        
        return {
            "success": True,
            "tailored_resume": result,
            "message": "Resume optimized for ATS"
        }
        
    except Exception as e:
        logger.error(f"Error optimizing resume: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error optimizing resume: {str(e)}"
        )


# ============================================================================
# ATS Scoring
# ============================================================================

@app.post("/api/resume/score", response_model=ATSScoreResponse)
async def calculate_ats_score(request: ATSScoreRequest):
    """Calculate ATS score for a resume against a job description"""
    try:
        # Initialize ATS scorer
        ats_scorer, _, _ = get_services()
        
        logger.info(f"Calculating ATS score for resume length: {len(request.resume_text)}")
        
        # Use the actual ATS scorer
        result = ats_scorer.score_resume(
            resume_text=request.resume_text,
            job_description=request.job_description
        )
        
        return ATSScoreResponse(
            score=result.get("score", 0),
            keyword_match=result.get("keyword_match", 0),
            format_score=result.get("format_score", 0),
            suggestions=result.get("suggestions", []),
            matched_keywords=result.get("matched_keywords", []),
            missing_keywords=result.get("missing_keywords", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating ATS score: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating ATS score: {str(e)}"
        )


@app.post("/api/resume/check-ats")
async def check_ats_score(request: CheckATSScoreRequest):
    """Check ATS score for a resume"""
    try:
        api_key = get_api_key()
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service not configured"
            )
        
        from core.models import JobAnalysis, SeniorityLevel, Industry, CompanyType
        
        scorer = ATSScorer(api_key)
        
        job_analysis = JobAnalysis(
            role_title="Software Engineer",
            seniority_level=SeniorityLevel.MID,
            years_experience_required=3,
            key_skills=[],
            nice_to_have_skills=[],
            industry=Industry.TECH,
            company_type=CompanyType.ENTERPRISE,
            role_focus_areas=[],
            missing_from_resume=[],
        )
        
        # Convert dict to core model if needed
        core_resume = convert_app_to_core(request.resume_data)
        
        result = scorer.score_resume(
            resume=core_resume,
            job_analysis=job_analysis
        )
        
        return {
            "success": True,
            "score": result.get("overall_score", 0),
            "details": result
        }
        
    except Exception as e:
        logger.error(f"Error checking ATS score: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking ATS score: {str(e)}"
        )


# ============================================================================
# PDF Rendering
# ============================================================================

@app.post("/api/resume/download")
async def render_resume_pdf(resume_data: Dict[str, Any]):
    """Render a resume as PDF"""
    try:
        logger.info(f"Rendering resume PDF")
        
        # Convert dict to TailoredResume model
        from backend.app.models import TailoredResume as AppTailoredResume
        
        # Parse the resume data into the model
        tailored_resume = AppTailoredResume(**resume_data)
        
        # Generate PDF using the actual ResumeProcessor
        pdf_bytes = await resume_processor.generate_pdf(tailored_resume)
        
        return StreamingResponse(
            pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=tailored_resume.pdf"
            }
        )
        
    except Exception as e:
        logger.error(f"Error rendering PDF: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rendering PDF: {str(e)}"
        )


# ============================================================================
# AI Improve Text
# ============================================================================

@app.get("/api/resume/status/{job_id}")
async def get_generation_status(job_id: str):
    """Get the status of a resume generation job"""
    try:
        # Since we're using synchronous generation, we always return completed
        return {
            "job_id": job_id,
            "status": "completed",
            "message": "Job completed successfully"
        }
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}"
        )


@app.post("/api/resume/improve")
async def improve_text(request: ImproveTextRequest):
    """Improve text using AI (for edit feature)"""
    try:
        ai_client = get_ai_client()
        
        improved = await ai_client.improve_text(
            original_text=request.original_text,
            user_prompt=request.user_prompt,
            context=request.context
        )
        
        return {
            "success": True,
            "improved_text": improved
        }
        
    except Exception as e:
        logger.error(f"Error improving text: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error improving text: {str(e)}"
        )


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
