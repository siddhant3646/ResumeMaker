"""
AI Client - Kimi K2.5 Integration with Job Queue and Retry Logic
"""

import os
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from copy import deepcopy

logger = logging.getLogger(__name__)


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
    
    MAX_ATTEMPTS = 10
    
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
                        resume_data, job_description, core_config
                    )
                else:
                    job["progress"] = 10.0 + (attempt - 1) * 8
                    job["message"] = f"Retry {attempt}/{self.MAX_ATTEMPTS} - Optimizing content..."
                    job["stream_text"] = "Kimi improving based on feedback..."
                    
                    if best_tailored and previous_ats_feedback and job_analysis:
                        tailored = content_gen.regenerate_with_feedback(
                            previous_resume=best_tailored,
                            original_resume=resume_data,
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
            
            config = CoreGenConfig(
                generation_mode=GenerationMode.ATS_OPTIMIZE_ONLY,
                fabrication_enabled=False,
                target_ats_score=90,
                page_match_mode="optimize"
            )
            
            content_gen = ContentGenerator(self.api_key, self.api_key)
            
            tailored, job_analysis = content_gen.optimize_for_ats_only(resume_data, config)
            
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
    
    async def get_job_status(self, job_id: str) -> Dict:
        """Get job status and result"""
        if job_id not in self.jobs:
            raise ValueError(f"Job not found: {job_id}")
        
        job = self.jobs[job_id]
        result = job.get("result")
        
        result_dict = None
        if result:
            if hasattr(result, 'model_dump'):
                result_dict = result.model_dump()
            elif isinstance(result, dict):
                result_dict = result
        
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
