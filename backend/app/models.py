"""
Pydantic Models for ResumeMaker API
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime

# ============================================================================
# Enums
# ============================================================================

class GenerationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class PageStrategy(str, Enum):
    OPTIMIZE = "optimize"
    FORCE_1_PAGE = "force_1_page"
    FORCE_2_PAGES = "force_2_pages"

class FabricationLevel(str, Enum):
    SUBTLE = "subtle"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

class GenerationMode(str, Enum):
    TAILOR_WITH_JD = "tailor_with_jd"
    ATS_OPTIMIZE_ONLY = "ats_optimize_only"

# ============================================================================
# Health & System
# ============================================================================

class HealthResponse(BaseModel):
    status: str
    version: str
    service: str

# ============================================================================
# User & Auth
# ============================================================================

class UserInfo(BaseModel):
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None

# ============================================================================
# Resume Data Models
# ============================================================================

class Basics(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    website: Optional[str] = None

class Experience(BaseModel):
    company: str
    role: str
    location: Optional[str] = None
    startDate: str
    endDate: Optional[str] = None
    bullets: List[str]
    is_fabricated: bool = False

class Education(BaseModel):
    institution: str
    degree: str
    field: Optional[str] = None
    location: Optional[str] = None
    graduationDate: Optional[str] = None
    gpa: Optional[str] = None

class Skills(BaseModel):
    languages_frameworks: List[str] = []
    tools: List[str] = []
    methodologies: List[str] = []

class Project(BaseModel):
    name: str
    description: Optional[str] = None
    technologies: List[str] = []
    link: Optional[str] = None

class ParsedResume(BaseModel):
    basics: Basics
    summary: Optional[str] = None
    experience: List[Experience] = []
    education: List[Education] = []
    skills: Skills
    projects: List[Project] = []
    achievements: List[str] = []

class TailoredResume(BaseModel):
    basics: Basics
    summary: Optional[str] = None
    experience: List[Experience] = []
    education: List[Education] = []
    skills: Skills
    projects: List[Project] = []
    achievements: List[str] = []
    ats_score: Optional[Dict[str, Any]] = None
    fabrication_notes: List[str] = []

# ============================================================================
# Generation Config
# ============================================================================

class GenerationConfig(BaseModel):
    generation_mode: GenerationMode = GenerationMode.TAILOR_WITH_JD
    page_strategy: PageStrategy = PageStrategy.OPTIMIZE
    target_pages: Optional[int] = None
    fabrication_enabled: bool = True
    fabrication_level: FabricationLevel = FabricationLevel.SUBTLE
    target_ats_score: int = Field(default=92, ge=90, le=100)
    include_summary: bool = False
    include_projects: bool = True
    use_star_format: bool = True
    require_quantification: bool = True

# ============================================================================
# API Request/Response Models
# ============================================================================

class ResumeUploadResponse(BaseModel):
    success: bool
    message: str
    resume_data: ParsedResume
    filename: str

class JobDescriptionRequest(BaseModel):
    resume_data: ParsedResume
    job_description: Optional[str] = None

class GenerationRequest(BaseModel):
    resume_data: ParsedResume
    job_description: str
    config: GenerationConfig = Field(default_factory=GenerationConfig)

class GenerationResponse(BaseModel):
    success: bool
    job_id: str
    message: str
    status: GenerationStatus
    tailored_resume: Optional[Dict[str, Any]] = None
    ats_score: Optional[float] = None


class GenerationStatusResponse(BaseModel):
    job_id: str
    status: GenerationStatus
    progress: float = Field(ge=0, le=100)
    message: str
    result: Optional[TailoredResume] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
