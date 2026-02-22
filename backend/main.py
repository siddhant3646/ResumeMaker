"""
ResumeMaker AI - FastAPI Backend
2026 Edition with React Frontend
"""

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends, WebSocket, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, StreamingResponse
from contextlib import asynccontextmanager
import os
from typing import Optional
import logging

# Import app modules
from app.models import (
    HealthResponse, ResumeUploadResponse, JobDescriptionRequest,
    GenerationRequest, GenerationResponse, GenerationStatus,
    TailoredResume, UserInfo
)
from pydantic import BaseModel
from app.auth import verify_token, get_current_user
from app.resume import ResumeProcessor
from app.ai_client import AIClient
from app.websocket_manager import WebSocketManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting ResumeMaker AI Backend")
    logger.info(f"Frontend URL: {FRONTEND_URL}")
    
    if not NVIDIA_API_KEY:
        logger.warning("⚠️ NVIDIA_API_KEY not set - AI generation will fail")
    else:
        logger.info("✅ NVIDIA API key configured")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down ResumeMaker AI Backend")

# Create FastAPI app
app = FastAPI(
    title="ResumeMaker AI API",
    description="AI-powered resume optimization backend",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Configuration
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

# Security
security = HTTPBearer()

# Initialize services
resume_processor = ResumeProcessor()
ai_client = AIClient(api_key=NVIDIA_API_KEY)
ws_manager = WebSocketManager()

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
        service="resumemaker-ai-api"
    )

# ============================================================================
# Authentication
# ============================================================================

@app.get("/api/auth/me", response_model=UserInfo)
async def get_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user info"""
    return UserInfo(
        user_id=current_user.get("sub"),
        email=current_user.get("email"),
        name=current_user.get("name", current_user.get("nickname", "")),
        picture=current_user.get("picture")
    )

# ============================================================================
# Resume Upload & Parsing
# ============================================================================

@app.post("/api/resume/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
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
        
        # Parse resume
        parsed_resume = await resume_processor.parse_pdf(content)
        
        return ResumeUploadResponse(
            success=True,
            message="Resume parsed successfully",
            resume_data=parsed_resume,
            filename=file.filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing resume: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error parsing resume: {str(e)}"
        )

# ============================================================================
# Resume Generation
# ============================================================================

@app.post("/api/resume/generate")
async def generate_resume(
    request: GenerationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Single-pass synchronous resume generation.
    
    Returns the tailored resume immediately. Frontend drives additional
    improvement passes via /api/resume/regenerate.
    """
    try:
        if not NVIDIA_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service not configured"
            )

        result = await ai_client.generate_sync(
            resume_data=request.resume_data,
            job_description=request.job_description,
            config=request.config,
            user_id=current_user.get("sub")
        )

        return {
            "success": True,
            "job_id": "sync",
            "message": f"Resume generated! ATS Score: {result.get('ats_score', 0):.0f}",
            "status": "completed",
            "tailored_resume": result.get("tailored_resume"),
            "ats_score": result.get("ats_score"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating resume: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating resume: {str(e)}"
        )




@app.post("/api/resume/optimize-ats")
async def optimize_resume_ats(
    request: JobDescriptionRequest,  # resume_data only, no JD needed
    current_user: dict = Depends(get_current_user)
):
    """Optimize resume for ATS without job description (ATS-only mode)"""
    try:
        if not NVIDIA_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service not configured"
            )
        
        # Single-pass ATS optimization
        result = await ai_client.optimize_for_ats(
            resume_data=request.resume_data,
            user_id=current_user.get("sub")
        )
        
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

@app.get("/api/resume/status/{job_id}")
async def get_generation_status(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get the status of a resume generation job"""
    try:
        status_info = await ai_client.get_job_status(job_id)
        return status_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}"
        )

# ============================================================================
# WebSocket for Real-time Updates
# ============================================================================

@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time generation progress"""
    await ws_manager.connect(websocket, job_id)
    try:
        while True:
            # Keep connection alive and send updates
            import asyncio
            data = await ai_client.get_progress_update(job_id)
            await ws_manager.send_update(job_id, data)
            
            # Check if generation is complete
            if data.get("status") in ["completed", "failed"]:
                break
                
            await asyncio.sleep(1)
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(job_id)

# ============================================================================
# PDF Download
# ============================================================================

@app.post("/api/resume/download")
async def download_resume_pdf(
    resume_data: TailoredResume,
    current_user: dict = Depends(get_current_user)
):
    """Generate and download resume as PDF"""
    try:
        logger.info(f"Generating PDF for user {current_user.get('sub')}")
        logger.info(f"Resume sections - experience: {len(resume_data.experience)}, education: {len(resume_data.education)}, skills: {bool(resume_data.skills)}")
        
        pdf_bytes = await resume_processor.generate_pdf(resume_data)
        
        return StreamingResponse(
            pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=tailored_resume.pdf"
            }
        )
    except Exception as e:
        logger.error(f"Error generating PDF: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating PDF: {str(e)}"
        )

# ============================================================================
# AI Improve Text
# ============================================================================

class ImproveTextRequest(BaseModel):
    original_text: str
    user_prompt: str
    context: str = "resume content"

@app.post("/api/resume/improve")
async def improve_text(
    request: ImproveTextRequest,
    current_user: dict = Depends(get_current_user)
):
    """Improve text using AI (for edit feature)"""
    try:
        if not NVIDIA_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service not configured"
            )
        
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
# Check ATS Score
# ============================================================================

class CheckATSScoreRequest(BaseModel):
    resume_data: TailoredResume

@app.post("/api/resume/check-ats")
async def check_ats_score(
    request: CheckATSScoreRequest,
    current_user: dict = Depends(get_current_user)
):
    """Check ATS score for a resume"""
    try:
        if not NVIDIA_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service not configured"
            )
        
        from intelligence.ats_scorer import ATSScorer
        from core.models import JobAnalysis, SeniorityLevel, Industry, CompanyType
        
        scorer = ATSScorer(NVIDIA_API_KEY)
        
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
            match_score=85.0
        )
        
        ats_score = scorer.calculate_score(request.resume_data, job_analysis)
        
        return {
            "success": True,
            "ats_score": {
                "overall": ats_score.overall,
                "keyword_match": ats_score.keyword_match,
                "star_compliance": ats_score.star_compliance,
                "quantification": ats_score.quantification,
                "action_verb_strength": ats_score.action_verb_strength,
                "missing_keywords": ats_score.missing_keywords,
                "weak_bullets": ats_score.weak_bullets,
                "suggestions": ats_score.suggestions
            }
        }
        
    except Exception as e:
        logger.error(f"Error checking ATS score: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking ATS score: {str(e)}"
        )

# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "error": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True
    )
