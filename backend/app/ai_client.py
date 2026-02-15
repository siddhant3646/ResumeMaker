"""
AI Client - Mistral API Integration with Job Queue
"""

import os
import uuid
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from app.models import (
    ParsedResume, TailoredResume, GenerationConfig, GenerationStatus,
    Experience, Skills
)

logger = logging.getLogger(__name__)

class AIClient:
    """Mistral AI client with job queue management"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.jobs: Dict[str, Dict] = {}  # In-memory job store
        self.active_jobs: Dict[str, asyncio.Task] = {}
    
    async def start_generation(
        self,
        resume_data: ParsedResume,
        job_description: str,
        config: GenerationConfig,
        user_id: str
    ) -> str:
        """Start resume generation job"""
        job_id = str(uuid.uuid4())
        
        self.jobs[job_id] = {
            "job_id": job_id,
            "user_id": user_id,
            "status": GenerationStatus.PENDING,
            "progress": 0.0,
            "message": "Starting generation...",
            "result": None,
            "error": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "resume_data": resume_data,
            "job_description": job_description,
            "config": config
        }
        
        # Start async job
        task = asyncio.create_task(
            self._process_generation(job_id)
        )
        self.active_jobs[job_id] = task
        
        return job_id
    
    async def _process_generation(self, job_id: str):
        """Process resume generation asynchronously"""
        job = self.jobs[job_id]
        
        try:
            # Update status
            job["status"] = GenerationStatus.PROCESSING
            job["progress"] = 10.0
            job["message"] = "Analyzing job description..."
            job["updated_at"] = datetime.now()
            
            # Simulate AI processing (replace with actual Mistral calls)
            await asyncio.sleep(2)  # Simulate API call
            
            job["progress"] = 30.0
            job["message"] = "Matching skills with requirements..."
            await asyncio.sleep(2)
            
            job["progress"] = 50.0
            job["message"] = "Generating optimized content..."
            
            # Call Mistral API (placeholder)
            tailored_resume = await self._call_mistral_api(job)
            
            job["progress"] = 90.0
            job["message"] = "Finalizing resume..."
            await asyncio.sleep(1)
            
            # Complete
            job["status"] = GenerationStatus.COMPLETED
            job["progress"] = 100.0
            job["message"] = "Resume generated successfully!"
            job["result"] = tailored_resume
            job["updated_at"] = datetime.now()
            
        except Exception as e:
            logger.error(f"Generation failed for job {job_id}: {e}")
            job["status"] = GenerationStatus.FAILED
            job["error"] = str(e)
            job["updated_at"] = datetime.now()
        
        finally:
            # Cleanup
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
    
    async def _call_mistral_api(self, job: Dict) -> TailoredResume:
        """Call Mistral API to generate resume (placeholder)"""
        # In production, integrate with Mistral API here
        # For now, return mock data
        
        resume_data = job["resume_data"]
        
        return TailoredResume(
            basics=resume_data.basics,
            summary="Experienced software engineer with expertise in...",
            experience=[
                Experience(
                    company="Tech Corp",
                    role="Senior Engineer",
                    startDate="2020-01",
                    bullets=[
                        "Led team of 5 engineers delivering 3 major products",
                        "Improved system performance by 40% through optimization"
                    ]
                )
            ],
            education=resume_data.education,
            skills=Skills(
                languages_frameworks=["Python", "React", "FastAPI"],
                tools=["Docker", "Kubernetes"],
                methodologies=["Agile", "TDD"]
            ),
            projects=[],
            achievements=["Awarded Employee of the Year 2023"],
            ats_score={
                "overall": 92,
                "keyword_match": 95,
                "star_compliance": 90,
                "quantification": 88,
                "action_verb_strength": 95
            }
        )
    
    async def get_job_status(self, job_id: str) -> Dict:
        """Get job status and result"""
        if job_id not in self.jobs:
            raise ValueError(f"Job not found: {job_id}")
        
        job = self.jobs[job_id]
        return {
            "job_id": job_id,
            "status": job["status"],
            "progress": job["progress"],
            "message": job["message"],
            "result": job.get("result"),
            "error": job.get("error"),
            "created_at": job["created_at"].isoformat(),
            "updated_at": job["updated_at"].isoformat()
        }
    
    async def get_progress_update(self, job_id: str) -> Dict:
        """Get progress update for WebSocket"""
        return await self.get_job_status(job_id)
    
    async def optimize_for_ats(
        self,
        resume_data: ParsedResume,
        user_id: str
    ) -> TailoredResume:
        """ATS-only optimization (single pass)"""
        # Placeholder - integrate with Mistral
        return TailoredResume(
            basics=resume_data.basics,
            summary=resume_data.summary,
            experience=resume_data.experience,
            education=resume_data.education,
            skills=resume_data.skills,
            projects=resume_data.projects,
            achievements=resume_data.achievements,
            ats_score={
                "overall": 90,
                "keyword_match": 92,
                "star_compliance": 88,
                "quantification": 90,
                "action_verb_strength": 90
            }
        )
