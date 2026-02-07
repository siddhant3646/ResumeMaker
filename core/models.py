"""
Core Pydantic Models for ResumeMaker Intelligence System
Defines data structures for resume processing, job analysis, and ATS scoring
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from datetime import datetime
from enum import Enum


class SeniorityLevel(str, Enum):
    """Job seniority levels"""
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    STAFF = "staff"
    PRINCIPAL = "principal"
    DIRECTOR = "director"


class CompanyType(str, Enum):
    """Types of companies"""
    STARTUP = "startup"
    MID_SIZE = "mid_size"
    ENTERPRISE = "enterprise"
    FANG = "fang"
    CONSULTING = "consulting"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"


class Industry(str, Enum):
    """Industry sectors"""
    TECH = "technology"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    CONSULTING = "consulting"
    E_COMMERCE = "e_commerce"
    EDUCATION = "education"
    GAMING = "gaming"
    OTHER = "other"


class Basics(BaseModel):
    """Basic contact information"""
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    links: List[str] = []


class Education(BaseModel):
    """Education entry"""
    institution: str
    studyType: str
    area: str
    startDate: str
    endDate: str
    location: Optional[str] = None


class Experience(BaseModel):
    """Work experience entry"""
    company: str
    role: str
    startDate: str
    endDate: str
    location: Optional[str] = None
    bullets: List[str] = []
    is_fabricated: bool = False  # Track if this experience was AI-generated


class Skills(BaseModel):
    """Skills section"""
    languages_frameworks: List[str] = []
    tools: List[str] = []


class Project(BaseModel):
    """Project entry"""
    name: str
    techStack: str
    description: str
    is_fabricated: bool = False


class ParsedResume(BaseModel):
    """Parsed resume structure"""
    basics: Basics
    summary: Optional[str] = None
    education: List[Education] = []
    experience: List[Experience] = []
    skills: Optional[Skills] = None
    projects: List[Project] = []
    achievements: List[str] = []


class JobAnalysis(BaseModel):
    """Deep analysis of job description"""
    role_title: str
    seniority_level: SeniorityLevel
    years_experience_required: int
    key_skills: List[str] = []
    nice_to_have_skills: List[str] = []
    industry: Industry
    company_type: CompanyType
    role_focus_areas: List[str] = []  # e.g., ["backend", "distributed_systems"]
    company_culture_keywords: List[str] = []  # e.g., ["ownership", "customer_obsession"]
    missing_from_resume: List[str] = []  # Skills user lacks
    match_score: float = Field(ge=0, le=100)


class SkillsGapReport(BaseModel):
    """Analysis of skills gaps between resume and JD"""
    exact_matches: List[str] = []
    partial_matches: List[str] = []  # Similar skills
    missing_critical: List[str] = []
    missing_nice_to_have: List[str] = []
    fabrication_candidates: List[str] = []  # Skills to fabricate if enabled
    transferrable_skills: List[str] = []  # Can reframe existing skills
    reframing_suggestions: Dict[str, str] = {}  # "Django" -> "Web Development"


class ContentPlan(BaseModel):
    """Plan for generating optimal resume content"""
    target_pages: int
    total_bullets: int
    bullets_per_experience: Dict[str, int]  # company -> bullet count
    include_summary: bool
    include_projects: bool
    include_achievements: bool
    sections_priority: List[str]  # Order to fill sections


class ATSScore(BaseModel):
    """ATS compatibility scoring"""
    overall: int = Field(ge=0, le=100)
    keyword_match: int = Field(ge=0, le=100)
    star_compliance: int = Field(ge=0, le=100)
    quantification: int = Field(ge=0, le=100)
    action_verb_strength: int = Field(ge=0, le=100)
    format_compliance: int = Field(ge=0, le=100)
    section_completeness: int = Field(ge=0, le=100)
    suggestions: List[str] = []
    
    def is_faang_ready(self) -> bool:
        """Check if resume meets FAANG standards (>90)"""
        return self.overall >= 90


class ValidationReport(BaseModel):
    """PDF validation report from vision model"""
    page_count: int
    fill_percentage: float
    whitespace_percentage: float
    text_density: float
    issues: List[str] = []  # "too_much_whitespace", "text_cut_off", etc.
    suggestions: List[str] = []
    needs_regeneration: bool
    ats_score: Optional[int] = None
    
    def has_critical_issues(self) -> bool:
        """Check if there are issues preventing good resume"""
        critical = ['text_cut_off', 'poor_formatting', 'unreadable']
        return any(issue in self.issues for issue in critical)


class GenerationConfig(BaseModel):
    """Configuration for resume generation"""
    # Core Settings
    page_match_mode: Literal["optimize", "force_1_page", "force_2_pages"] = "optimize"
    target_pages: Optional[int] = None  # None = optimize mode, 1 or 2 = force specific
    
    # Content Generation
    fabrication_enabled: bool = True  # Default ON as requested
    fabrication_level: Literal["subtle", "moderate", "aggressive"] = "subtle"
    
    # Quality Settings
    target_ats_score: int = Field(default=92, ge=90, le=100)  # FAANG standard
    enable_vision_validation: bool = True
    max_regeneration_attempts: Optional[int] = None  # None = infinite
    
    # Content Strategy
    prioritize_recent_experience: bool = True
    include_summary: bool = False  # Only if 2+ pages
    include_projects: bool = True
    include_achievements: bool = True
    
    # FAANG/MAANG Specific
    use_star_format: bool = True
    use_xyz_formula: bool = True
    require_quantification: bool = True
    min_metrics_per_bullet: int = 1


class GenerationAttempt(BaseModel):
    """Track a single generation attempt"""
    attempt_number: int
    timestamp: datetime
    ats_score: ATSScore
    validation_report: Optional[ValidationReport]
    issues_found: List[str] = []
    adjustments_made: List[str] = []


class GenerationResult(BaseModel):
    """Final result of resume generation"""
    pdf_bytes: bytes
    resume_data: ParsedResume
    ats_score: ATSScore
    validation_report: ValidationReport
    attempts: List[GenerationAttempt]
    total_attempts: int
    fabrication_audit: List[str] = []  # Track what was fabricated
    generation_time_seconds: float
    success: bool


class TailoredResume(BaseModel):
    """Final tailored resume structure"""
    basics: Basics
    summary: Optional[str] = None
    education: List[Education] = []
    experience: List[Experience] = []
    skills: Optional[Skills] = None
    projects: List[Project] = []
    achievements: List[str] = []
    ats_score: Optional[ATSScore] = None
    fabrication_notes: List[str] = []


class UIState(BaseModel):
    """Track UI state for animations"""
    current_stage: str = "initializing"
    progress_percentage: float = 0.0
    current_tip_index: int = 0
    regeneration_attempt: int = 0
    is_processing: bool = False
    ats_score: Optional[int] = None
    status_message: str = ""
