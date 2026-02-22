"""
AI Client - Kimi K2.5 Integration with Job Queue and Retry Logic
"""

import os
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from copy import deepcopy

logger = logging.getLogger(__name__)


def validate_tailored_resume(tailored: Any) -> Tuple[bool, List[str]]:
    """Validate that tailored resume has all required sections"""
    issues = []
    
    if not tailored:
        return False, ["Tailored resume is None"]
    
    if not hasattr(tailored, 'basics') or not tailored.basics:
        issues.append("Missing basics section")
    elif not getattr(tailored.basics, 'name', None):
        issues.append("Missing name in basics")
    
    if not hasattr(tailored, 'experience') or not tailored.experience:
        issues.append("Missing experience section")
    elif len(tailored.experience) == 0:
        issues.append("Experience array is empty")
    else:
        for i, exp in enumerate(tailored.experience):
            if not getattr(exp, 'bullets', None) or len(exp.bullets) == 0:
                issues.append(f"Experience {i} ({getattr(exp, 'company', 'unknown')}) has no bullets")
    
    if not hasattr(tailored, 'education') or not tailored.education:
        issues.append("Missing education section")
    
    if not hasattr(tailored, 'skills') or not tailored.skills:
        issues.append("Missing skills section")
    
    return len(issues) == 0, issues


def convert_app_to_core(resume_data: Any) -> Any:
    """Convert app.models ParsedResume to core.models format"""
    from core.models import ParsedResume as CoreParsedResume
    from core.models import Basics as CoreBasics
    from core.models import Experience as CoreExperience
    from core.models import Education as CoreEducation
    from core.models import Skills as CoreSkills
    from core.models import Project as CoreProject
    
    # Handle dict input
    if isinstance(resume_data, dict):
        basics_data = resume_data.get("basics", {})
        basics = CoreBasics(
            name=basics_data.get("name", ""),
            email=basics_data.get("email", ""),
            phone=basics_data.get("phone"),
            location=basics_data.get("location"),
            links=[]
        )
        
        experience = []
        for exp in resume_data.get("experience", []):
            if isinstance(exp, dict):
                end_date = exp.get("endDate") or ""
                experience.append(CoreExperience(
                    company=str(exp.get("company", "")),
                    role=str(exp.get("role", "")),
                    startDate=str(exp.get("startDate", "")),
                    endDate=str(end_date),
                    location=exp.get("location"),
                    bullets=exp.get("bullets", []),
                    is_fabricated=exp.get("is_fabricated", False)
                ))
            else:
                end_date = getattr(exp, 'endDate', '') or ""
                experience.append(CoreExperience(
                    company=str(exp.company),
                    role=str(exp.role),
                    startDate=str(getattr(exp, 'startDate', '')),
                    endDate=str(end_date),
                    location=getattr(exp, 'location', None),
                    bullets=exp.bullets or [],
                    is_fabricated=getattr(exp, 'is_fabricated', False)
                ))
        
        education = []
        for edu in resume_data.get("education", []):
            if isinstance(edu, dict):
                education.append(CoreEducation(
                    institution=edu.get("institution", ""),
                    studyType=edu.get("degree", "") or edu.get("studyType", ""),
                    area=edu.get("field", "") or edu.get("area", ""),
                    startDate=edu.get("startDate", ""),
                    endDate=edu.get("graduationDate", "") or edu.get("endDate", ""),
                    location=edu.get("location")
                ))
            else:
                education.append(CoreEducation(
                    institution=edu.institution,
                    studyType=getattr(edu, 'degree', '') or getattr(edu, 'studyType', ''),
                    area=getattr(edu, 'field', '') or getattr(edu, 'area', ''),
                    startDate=getattr(edu, 'startDate', ''),
                    endDate=getattr(edu, 'graduationDate', '') or getattr(edu, 'endDate', ''),
                    location=getattr(edu, 'location', None)
                ))
        
        skills_data = resume_data.get("skills", {})
        if isinstance(skills_data, dict):
            skills = CoreSkills(
                languages_frameworks=skills_data.get("languages_frameworks", []),
                tools=skills_data.get("tools", [])
            )
        else:
            skills = CoreSkills(
                languages_frameworks=getattr(skills_data, 'languages_frameworks', []) or [],
                tools=getattr(skills_data, 'tools', []) or []
            )
        
        projects = []
        for proj in resume_data.get("projects", []):
            if isinstance(proj, dict):
                tech = proj.get("technologies", [])
                tech_str = ", ".join(tech) if isinstance(tech, list) else str(tech)
                projects.append(CoreProject(
                    name=proj.get("name", ""),
                    techStack=tech_str,
                    description=proj.get("description", ""),
                    is_fabricated=proj.get("is_fabricated", False)
                ))
            else:
                tech = getattr(proj, 'technologies', [])
                tech_str = ", ".join(tech) if isinstance(tech, list) else str(getattr(proj, 'techStack', ''))
                projects.append(CoreProject(
                    name=proj.name,
                    techStack=tech_str,
                    description=getattr(proj, 'description', ''),
                    is_fabricated=getattr(proj, 'is_fabricated', False)
                ))
        
        return CoreParsedResume(
            basics=basics,
            summary=resume_data.get("summary"),
            experience=experience,
            education=education,
            skills=skills,
            projects=projects,
            achievements=resume_data.get("achievements", [])
        )
    
    # Handle Pydantic model input
    basics_obj = resume_data.basics
    basics = CoreBasics(
        name=basics_obj.name,
        email=basics_obj.email,
        phone=getattr(basics_obj, 'phone', None),
        location=getattr(basics_obj, 'location', None),
        links=[]
    )
    
    experience = []
    for exp in resume_data.experience:
        end_date = getattr(exp, 'endDate', '') or ""
        experience.append(CoreExperience(
            company=str(exp.company),
            role=str(exp.role),
            startDate=str(getattr(exp, 'startDate', '')),
            endDate=str(end_date),
            location=getattr(exp, 'location', None),
            bullets=exp.bullets or [],
            is_fabricated=getattr(exp, 'is_fabricated', False)
        ))
    
    education = []
    for edu in resume_data.education:
        education.append(CoreEducation(
            institution=edu.institution,
            studyType=getattr(edu, 'degree', '') or getattr(edu, 'studyType', ''),
            area=getattr(edu, 'field', '') or getattr(edu, 'area', ''),
            startDate=getattr(edu, 'startDate', ''),
            endDate=getattr(edu, 'graduationDate', '') or getattr(edu, 'endDate', ''),
            location=getattr(edu, 'location', None)
        ))
    
    skills_obj = resume_data.skills
    skills = CoreSkills(
        languages_frameworks=getattr(skills_obj, 'languages_frameworks', []) or [],
        tools=getattr(skills_obj, 'tools', []) or []
    )
    
    projects = []
    for proj in resume_data.projects:
        tech = getattr(proj, 'technologies', [])
        tech_str = ", ".join(tech) if isinstance(tech, list) else str(getattr(proj, 'techStack', ''))
        projects.append(CoreProject(
            name=proj.name,
            techStack=tech_str,
            description=getattr(proj, 'description', ''),
            is_fabricated=getattr(proj, 'is_fabricated', False)
        ))
    
    return CoreParsedResume(
        basics=basics,
        summary=getattr(resume_data, 'summary', None),
        experience=experience,
        education=education,
        skills=skills,
        projects=projects,
        achievements=getattr(resume_data, 'achievements', []) or []
    )


def convert_core_to_app(core_resume: Any) -> Dict:
    """Convert core.models TailoredResume to plain dict for app.models"""
    
    def convert_basics(basics_obj) -> Dict:
        return {
            "name": basics_obj.name,
            "email": basics_obj.email,
            "phone": getattr(basics_obj, 'phone', None),
            "location": getattr(basics_obj, 'location', None),
            "linkedin": None,
            "github": None,
            "website": None
        }
    
    def convert_experience(exp_list) -> list:
        result = []
        for exp in exp_list:
            result.append({
                "company": exp.company,
                "role": exp.role,
                "startDate": exp.startDate if hasattr(exp, 'startDate') else '',
                "endDate": getattr(exp, 'endDate', None),
                "location": getattr(exp, 'location', None),
                "bullets": exp.bullets if exp.bullets else [],
                "is_fabricated": getattr(exp, 'is_fabricated', False)
            })
        return result
    
    def convert_education(edu_list) -> list:
        result = []
        for edu in edu_list:
            result.append({
                "institution": edu.institution,
                "degree": getattr(edu, 'studyType', '') or getattr(edu, 'degree', ''),
                "field": getattr(edu, 'area', None),
                "location": getattr(edu, 'location', None),
                "graduationDate": getattr(edu, 'endDate', None),
                "gpa": None
            })
        return result
    
    def convert_skills(skills_obj) -> Dict:
        return {
            "languages_frameworks": skills_obj.languages_frameworks if skills_obj and skills_obj.languages_frameworks else [],
            "tools": skills_obj.tools if skills_obj and skills_obj.tools else [],
            "methodologies": []
        }
    
    def convert_projects(proj_list) -> list:
        result = []
        for proj in proj_list:
            tech = getattr(proj, 'techStack', '') or ''
            result.append({
                "name": proj.name,
                "description": getattr(proj, 'description', ''),
                "technologies": tech.split(', ') if tech else [],
                "link": None
            })
        return result
    
    ats_score_dict = None
    if hasattr(core_resume, 'ats_score') and core_resume.ats_score:
        ats = core_resume.ats_score
        ats_score_dict = {
            "overall": getattr(ats, 'overall', 90),
            "keyword_match": getattr(ats, 'keyword_match', 90),
            "star_compliance": getattr(ats, 'star_compliance', 90),
            "quantification": getattr(ats, 'quantification', 90),
            "action_verb_strength": getattr(ats, 'action_verb_strength', 90)
        }
    
    fabrication_notes = getattr(core_resume, 'fabrication_notes', []) or []
    
    return {
        "basics": convert_basics(core_resume.basics),
        "summary": getattr(core_resume, 'summary', None),
        "experience": convert_experience(core_resume.experience),
        "education": convert_education(getattr(core_resume, 'education', [])),
        "skills": convert_skills(getattr(core_resume, 'skills', None)),
        "projects": convert_projects(getattr(core_resume, 'projects', [])),
        "achievements": getattr(core_resume, 'achievements', []) or [],
        "ats_score": ats_score_dict,
        "fabrication_notes": fabrication_notes
    }

class AIClient:
    """Kimi K2.5 AI client with job queue management and retry logic"""
    
    MAX_ATTEMPTS = 5
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.jobs: Dict[str, Dict] = {}
        self.active_jobs: Dict[str, asyncio.Task] = {}
        
        if not api_key:
            logger.warning("NVIDIA_API_KEY not set - AI generation may fail")
    
    async def start_generation(
        self,
        resume_data: Any,
        job_description: str,
        config: Any,
        user_id: str
    ) -> str:
        """Start resume generation job with Kimi K2.5"""
        job_id = str(uuid.uuid4())
        
        self.jobs[job_id] = {
            "job_id": job_id,
            "user_id": user_id,
            "status": "pending",
            "progress": 0.0,
            "message": "Initializing Kimi K2.5...",
            "result": None,
            "error": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "resume_data": resume_data,
            "job_description": job_description,
            "config": config,
            "attempt": 1,
            "ats_score": None,
            "stream_text": ""
        }
        
        task = asyncio.create_task(self._process_generation(job_id))
        self.active_jobs[job_id] = task
        
        return job_id
    
    async def _process_generation(self, job_id: str):
        """Process resume generation with retry loop using Kimi K2.5"""
        from app.models import GenerationStatus
        
        job = self.jobs[job_id]
        
        try:
            if not self.api_key:
                raise ValueError("NVIDIA_API_KEY not configured")
            
            resume_data = job["resume_data"]
            job_description = job["job_description"]
            config = job["config"]
            
            from intelligence.content_generator import ContentGenerator
            from core.models import GenerationConfig as CoreGenConfig
            from core.models import GenerationMode
            
            # Convert app.models to core.models
            core_resume = convert_app_to_core(resume_data)
            
            content_gen = ContentGenerator(self.api_key, self.api_key)
            
            core_config = CoreGenConfig(
                generation_mode=GenerationMode.TAILOR_WITH_JD if job_description else GenerationMode.ATS_OPTIMIZE_ONLY,
                fabrication_enabled=getattr(config, 'fabrication_enabled', True),
                target_ats_score=getattr(config, 'target_ats_score', 92),
                page_match_mode="optimize"
            )
            
            best_tailored = None
            best_score = 0
            previous_ats_feedback = None
            job_analysis = None
            
            for attempt in range(1, self.MAX_ATTEMPTS + 1):
                job["attempt"] = attempt
                job["updated_at"] = datetime.now()
                
                target_score = getattr(config, 'target_ats_score', 92)
                
                if attempt == 1:
                    job["status"] = GenerationStatus.PROCESSING
                    job["progress"] = 10.0
                    job["message"] = "Analyzing job description..."
                    job["stream_text"] = "Kimi K2.5 analyzing requirements..."
                    
                    tailored, job_analysis = content_gen.generate_tailored_resume(
                        core_resume, job_description, core_config
                    )
                else:
                    job["progress"] = 10.0 + (attempt - 1) * 8
                    job["message"] = f"Retry {attempt}/{self.MAX_ATTEMPTS} - Optimizing content..."
                    job["stream_text"] = "Kimi improving based on feedback..."
                    
                    if best_tailored and previous_ats_feedback and job_analysis:
                        tailored = content_gen.regenerate_with_feedback(
                            previous_resume=best_tailored,
                            original_resume=core_resume,
                            job_analysis=job_analysis,
                            ats_feedback=previous_ats_feedback,
                            config=core_config,
                            retry_count=attempt
                        )
                    else:
                        tailored = best_tailored
                
                ats_score = tailored.ats_score.overall if tailored and tailored.ats_score else 0
                job["ats_score"] = ats_score
                
                logger.info(f"Attempt {attempt}: ATS Score = {ats_score}")
                
                if ats_score > best_score:
                    best_score = ats_score
                    best_tailored = tailored
                
                if ats_score >= target_score:
                    job["status"] = GenerationStatus.COMPLETED
                    job["progress"] = 100.0
                    job["message"] = f"Completed! ATS Score: {ats_score}"
                    job["stream_text"] = f"Resume optimized with {ats_score}% ATS score"
                    job["result"] = convert_core_to_app(best_tailored) if best_tailored else None
                    job["updated_at"] = datetime.now()
                    return
                
                previous_ats_feedback = tailored.ats_score if tailored else None
                
                job["message"] = f"Attempt {attempt}/{self.MAX_ATTEMPTS} - Score: {ats_score}/{target_score}"
            
            job["status"] = GenerationStatus.COMPLETED
            job["progress"] = 100.0
            job["message"] = f"Completed with best score: {best_score}"
            job["stream_text"] = f"Resume generated - Best ATS: {best_score}%"
            job["result"] = convert_core_to_app(best_tailored) if best_tailored else None
            job["ats_score"] = best_score
            job["updated_at"] = datetime.now()
            
        except Exception as e:
            logger.error(f"Generation failed for job {job_id}: {e}", exc_info=True)
            job["status"] = GenerationStatus.FAILED
            job["error"] = str(e)
            job["message"] = f"Error: {str(e)}"
            job["updated_at"] = datetime.now()
        
        finally:
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
    
    async def optimize_for_ats(
        self,
        resume_data: Any,
        user_id: str
    ):
        """ATS-only optimization using Kimi K2.5 (single pass)"""
        try:
            from intelligence.content_generator import ContentGenerator
            from core.models import GenerationConfig as CoreGenConfig
            from core.models import GenerationMode
            
            # Convert app.models to core.models
            core_resume = convert_app_to_core(resume_data)
            
            config = CoreGenConfig(
                generation_mode=GenerationMode.ATS_OPTIMIZE_ONLY,
                fabrication_enabled=False,
                target_ats_score=90,
                page_match_mode="optimize"
            )
            
            content_gen = ContentGenerator(self.api_key, self.api_key)
            
            tailored, job_analysis = content_gen.optimize_for_ats_only(core_resume, config)
            
            return convert_core_to_app(tailored) if tailored else None
            
        except Exception as e:
            logger.error(f"ATS optimization failed: {e}", exc_info=True)
            raise
    
    async def improve_text(
        self,
        original_text: str,
        user_prompt: str,
        context: str
    ) -> str:
        """AI improvement of specific text (for edit feature)"""
        try:
            import httpx
            
            system_prompt = f"""You are a professional resume writer helping improve a resume.

CONTEXT: {context}

ORIGINAL TEXT:
{original_text}

USER'S REQUEST: {user_prompt}

INSTRUCTIONS:
- Rewrite the text following the user's request
- Use STAR format where applicable
- Include specific metrics and quantifiable results
- Use strong action verbs
- Keep it concise (1-2 lines maximum)
- Maintain professional tone
- Only return the improved text, nothing else

IMPROVED TEXT:"""
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://integrate.api.nvidia.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "moonshotai/kimi-k2.5",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 200,
                        "stream": False
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                
                improved = content.strip()
                if improved.startswith('"') and improved.endswith('"'):
                    improved = improved[1:-1]
                
                return improved if improved else original_text
                
        except Exception as e:
            logger.error(f"AI improvement failed: {e}")
            raise ValueError(f"AI improvement failed: {str(e)}")
    
    async def generate_sync(
        self,
        resume_data: Any,
        job_description: str,
        config: Any,
        user_id: str,
    ) -> Dict:
        """Server-side generation for the first pass.
        The frontend will drive subsequent passes via regenerate_single_pass 
        to ensure no single request hits the 60s proxy timeout.
        
        Returns:
            Dict with tailored_resume, ats_score, page_status, success, continue_reason
        """
        import gc
        from core.models import GenerationConfig as CoreGenConfig
        from core.models import GenerationMode
        from intelligence.content_generator import ContentGenerator

        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY not configured")

        core_resume = convert_app_to_core(resume_data)

        core_config = CoreGenConfig(
            generation_mode=GenerationMode.TAILOR_WITH_JD if job_description else GenerationMode.ATS_OPTIMIZE_ONLY,
            fabrication_enabled=getattr(config, "fabrication_enabled", True),
            target_ats_score=getattr(config, "target_ats_score", 92),
            page_match_mode="optimize",
        )

        content_gen = ContentGenerator(self.api_key, self.api_key)
        
        try:
            logger.info("[sync] Starting initial generation pass")
            
            tailored, job_analysis = content_gen.generate_tailored_resume(
                core_resume, job_description, core_config
            )
            
            ats_score = tailored.ats_score.overall if tailored and tailored.ats_score else 0.0
            logger.info(f"[sync] Initial pass complete: ATS = {ats_score}")
            
            # Validate the result
            is_valid, validation_issues = validate_tailored_resume(tailored)
            if not is_valid:
                logger.warning(f"[sync] Validation issues: {validation_issues}")
            
            # Log detailed info
            if tailored:
                logger.info(f"[sync] Tailored has {len(tailored.experience)} experiences, "
                           f"{len(tailored.education)} education entries, "
                           f"skills: {bool(tailored.skills)}")
            
            # Check page fill
            page_status = None
            try:
                from app.renderer import generate_pdf_to_bytes
                from intelligence.page_manager import PageManager
                
                pdf_bytes = generate_pdf_to_bytes(tailored)
                page_manager = PageManager()
                page_status = page_manager.check_page_fill(pdf_bytes, target_fill=95)
                logger.info(f"[sync] Page fill: {page_status.fill_percentage}%")
            except Exception as e:
                logger.warning(f"[sync] Page check failed: {e}")

        finally:
            del content_gen
            gc.collect()

        result_dict = convert_core_to_app(tailored) if tailored else None
        
        # Calculate dual success conditions
        target_score = 92
        ats_passed = ats_score >= target_score
        page_passed = page_status and not page_status.needs_content and \
                      "CONSOLIDATE" not in (page_status.suggestion or "")
        
        # Determine continue reason
        continue_reason = None
        if not (ats_passed and page_passed):
            if ats_passed and not page_passed:
                continue_reason = "page_needs_content"
            elif not ats_passed and page_passed:
                continue_reason = "ats_needs_improvement"
            else:
                continue_reason = "both_need_improvement"
        
        return {
            "tailored_resume": result_dict,
            "ats_score": ats_score,
            "page_status": {
                "fill_percentage": page_status.fill_percentage if page_status else 100,
                "needs_content": page_status.needs_content if page_status else False,
                "suggestion": page_status.suggestion if page_status else None,
                "current_page": page_status.current_page if page_status else 1,
            } if page_status else None,
            "success": ats_passed and page_passed,
            "continue_reason": continue_reason,
            "validation_issues": validation_issues if not is_valid else [],
        }


    async def regenerate_single_pass(
        self,
        previous_resume: Any,
        job_description: str,
        attempt: int,
        user_id: str,
        force_variation: bool = False,
    ) -> Dict:
        """One improvement pass using ATS feedback from previous result.
        
        Called by the frontend in a loop until ATS >= target.
        Each call is ~30-60s, well within Render timeout.
        
        Returns:
            Dict with tailored_resume, ats_score, page_status, success, continue_reason
        """
        import gc
        from intelligence.content_generator import ContentGenerator
        from core.models import GenerationConfig as CoreGenConfig
        from core.models import GenerationMode, TailoredResume as CoreTailored, ATSScore as CoreATSScore

        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY not configured")

        core_previous = convert_app_to_core(previous_resume)
        
        ats_data = CoreATSScore(
            overall=0,
            keyword_match=0,
            star_compliance=0,
            quantification=0,
            action_verb_strength=0,
            format_compliance=80,
            section_completeness=80,
            missing_keywords=[],
            weak_bullets=[],
            shortcomings=[],
            suggestions=[],
        )
        
        if hasattr(previous_resume, 'ats_score') and previous_resume.ats_score:
            ats_dict = previous_resume.ats_score if isinstance(previous_resume.ats_score, dict) else previous_resume.ats_score.model_dump()
            ats_data = CoreATSScore(
                overall=ats_dict.get('overall', 0),
                keyword_match=ats_dict.get('keyword_match', 0),
                star_compliance=ats_dict.get('star_compliance', 0),
                quantification=ats_dict.get('quantification', 0),
                action_verb_strength=ats_dict.get('action_verb_strength', 0),
                format_compliance=ats_dict.get('format_compliance', 80),
                section_completeness=ats_dict.get('section_completeness', 80),
                missing_keywords=ats_dict.get('missing_keywords', []),
                weak_bullets=ats_dict.get('weak_bullets', []),
                shortcomings=ats_dict.get('shortcomings', []),
                suggestions=ats_dict.get('suggestions', []),
            )
        
        core_tailored = CoreTailored(
            basics=core_previous.basics,
            summary=getattr(previous_resume, 'summary', None) or core_previous.summary,
            experience=core_previous.experience,
            education=core_previous.education,
            skills=core_previous.skills,
            projects=core_previous.projects,
            achievements=getattr(core_previous, 'achievements', []),
            ats_score=ats_data,
            fabrication_notes=getattr(previous_resume, 'fabrication_notes', []) or [],
        )

        core_config = CoreGenConfig(
            generation_mode=GenerationMode.TAILOR_WITH_JD,
            fabrication_enabled=True,
            target_ats_score=92,
            page_match_mode="optimize",
        )

        content_gen = ContentGenerator(self.api_key, self.api_key)
        try:
            job_analysis = content_gen.role_detector.analyze_job_description(job_description)
            
            tailored = content_gen.regenerate_with_feedback(
                previous_resume=core_tailored,
                original_resume=core_previous,
                job_analysis=job_analysis,
                ats_feedback=ats_data,
                config=core_config,
                retry_count=attempt,
                force_variation=force_variation,
            )
            
            ats_score = tailored.ats_score.overall if tailored and tailored.ats_score else 0.0
            logger.info(f"[regenerate] Attempt {attempt}: ATS = {ats_score}")
            
            # Validate the result
            is_valid, validation_issues = validate_tailored_resume(tailored)
            if not is_valid:
                logger.warning(f"[regenerate] Validation issues: {validation_issues}")
            
            # Check page fill
            page_status = None
            try:
                from app.renderer import generate_pdf_to_bytes
                from intelligence.page_manager import PageManager
                
                pdf_bytes = generate_pdf_to_bytes(tailored)
                page_manager = PageManager()
                page_status = page_manager.check_page_fill(pdf_bytes, target_fill=95)
                logger.info(f"[regenerate] Page fill: {page_status.fill_percentage}%")
            except Exception as e:
                logger.warning(f"[regenerate] Page check failed: {e}")
            
            result_dict = convert_core_to_app(tailored) if tailored else None
            
            # Calculate dual success conditions
            target_score = 92
            ats_passed = ats_score >= target_score
            page_passed = page_status and not page_status.needs_content and \
                          "CONSOLIDATE" not in (page_status.suggestion or "")
            
            # Determine continue reason
            continue_reason = None
            if not (ats_passed and page_passed):
                if ats_passed and not page_passed:
                    continue_reason = "page_needs_content"
                elif not ats_passed and page_passed:
                    continue_reason = "ats_needs_improvement"
                else:
                    continue_reason = "both_need_improvement"
            
            return {
                "tailored_resume": result_dict,
                "ats_score": ats_score,
                "page_status": {
                    "fill_percentage": page_status.fill_percentage if page_status else 100,
                    "needs_content": page_status.needs_content if page_status else False,
                    "suggestion": page_status.suggestion if page_status else None,
                    "current_page": page_status.current_page if page_status else 1,
                } if page_status else None,
                "success": ats_passed and page_passed,
                "continue_reason": continue_reason,
                "validation_issues": validation_issues if not is_valid else [],
            }
        finally:
            del content_gen
            gc.collect()

    async def consolidate_resume(
        self,
        resume_data: Any,
        job_description: str,
        user_id: str,
    ) -> Dict:
        """Consolidate resume by removing weak bullets for sparse trailing pages.
        
        Called when page fill check indicates a sparse trailing page.
        Uses the _consolidate_resume method from ContentGenerator.
        """
        import gc
        from core.models import TailoredResume as CoreTailored, ATSScore as CoreATSScore
        from intelligence.content_generator import ContentGenerator
        
        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY not configured")
        
        core_resume = convert_app_to_core(resume_data)
        
        # Build ATS feedback from existing score
        ats_data = CoreATSScore(
            overall=0,
            keyword_match=0,
            star_compliance=0,
            quantification=0,
            action_verb_strength=0,
            format_compliance=80,
            section_completeness=80,
            missing_keywords=[],
            weak_bullets=[],
            shortcomings=[],
            suggestions=[],
        )
        
        if hasattr(resume_data, 'ats_score') and resume_data.ats_score:
            ats_dict = resume_data.ats_score if isinstance(resume_data.ats_score, dict) else resume_data.ats_score.model_dump()
            ats_data = CoreATSScore(
                overall=ats_dict.get('overall', 0),
                keyword_match=ats_dict.get('keyword_match', 0),
                star_compliance=ats_dict.get('star_compliance', 0),
                quantification=ats_dict.get('quantification', 0),
                action_verb_strength=ats_dict.get('action_verb_strength', 0),
                format_compliance=ats_dict.get('format_compliance', 80),
                section_completeness=ats_dict.get('section_completeness', 80),
                missing_keywords=ats_dict.get('missing_keywords', []),
                weak_bullets=ats_dict.get('weak_bullets', []),
                shortcomings=ats_dict.get('shortcomings', []),
                suggestions=ats_dict.get('suggestions', []),
            )
        
        # Build TailoredResume for consolidation
        core_tailored = CoreTailored(
            basics=core_resume.basics,
            summary=core_resume.summary,
            experience=core_resume.experience,
            education=core_resume.education,
            skills=core_resume.skills,
            projects=core_resume.projects,
            achievements=core_resume.achievements,
            ats_score=ats_data,
            fabrication_notes=getattr(resume_data, 'fabrication_notes', []) or [],
        )
        
        content_gen = ContentGenerator(self.api_key, self.api_key)
        try:
            logger.info("[consolidate] Starting consolidation")
            
            # Trigger consolidation
            consolidated = content_gen._consolidate_resume(core_tailored, ats_data)
            
            # Calculate new ATS score
            ats_score = consolidated.ats_score.overall if consolidated and consolidated.ats_score else 0.0
            logger.info(f"[consolidate] Consolidation complete: ATS = {ats_score}")
            
            result_dict = convert_core_to_app(consolidated) if consolidated else None
            
            return {
                "tailored_resume": result_dict,
                "ats_score": ats_score,
                "message": "Resume consolidated for better page fit"
            }
        finally:
            del content_gen
            gc.collect()

    async def get_job_status(self, job_id: str) -> Dict:
        """Get job status and result"""
        if job_id not in self.jobs:
            raise ValueError(f"Job not found: {job_id}")
        
        job = self.jobs[job_id]
        result = job.get("result")
        
        result_dict = None
        if result:
            logger.info(f"Result type: {type(result)}, isinstance dict: {isinstance(result, dict)}")
            if hasattr(result, 'model_dump'):
                result_dict = result.model_dump()
            elif isinstance(result, dict):
                # Deep convert any nested Pydantic models to dicts
                import json
                result_dict = json.loads(json.dumps(result, default=lambda o: o.dict() if hasattr(o, 'dict') else str(o)))
            else:
                # Unexpected type - try to convert
                logger.warning(f"Unexpected result type: {type(result)}")
                if hasattr(result, 'dict'):
                    result_dict = result.dict()
        
        return {
            "job_id": job_id,
            "status": job["status"],
            "progress": job["progress"],
            "message": job["message"],
            "stream_text": job.get("stream_text", ""),
            "result": result_dict,
            "error": job.get("error"),
            "attempt": job.get("attempt", 1),
            "ats_score": job.get("ats_score"),
            "created_at": job["created_at"].isoformat(),
            "updated_at": job["updated_at"].isoformat()
        }
    
    async def get_progress_update(self, job_id: str) -> Dict:
        """Get progress update for WebSocket"""
        return await self.get_job_status(job_id)
