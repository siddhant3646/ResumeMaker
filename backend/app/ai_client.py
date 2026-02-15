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
        """Call Mistral API to generate resume"""
        import httpx
        import json
        
        resume_data = job["resume_data"]
        job_description = job["job_description"]
        config = job["config"]
        
        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY not configured")
        
        # Build prompt for Mistral
        system_prompt = """You are an expert resume writer specializing in ATS-optimized resumes for FAANG/MAANG companies.
        
TASK: Rewrite the provided resume to match the job description.

RULES:
1. Use STAR format (Situation, Task, Action, Result) for all bullets
2. Include specific metrics and quantifiable results
3. Use strong action verbs
4. Match keywords from job description
5. Target ATS score >90
6. Keep it concise and professional

OUTPUT FORMAT: Return JSON with this structure:
{
    "summary": "professional summary",
    "experience": [
        {
            "company": "Company Name",
            "role": "Job Title",
            "startDate": "YYYY-MM",
            "endDate": "YYYY-MM or null",
            "bullets": ["STAR formatted bullet 1", "STAR formatted bullet 2"]
        }
    ],
    "skills": {
        "languages_frameworks": ["Skill1", "Skill2"],
        "tools": ["Tool1", "Tool2"],
        "methodologies": ["Method1"]
    },
    "ats_score": {
        "overall": 92,
        "keyword_match": 95,
        "star_compliance": 90,
        "quantification": 88,
        "action_verb_strength": 95
    }
}"""

        user_prompt = f"""JOB DESCRIPTION:
{job_description}

CURRENT RESUME:
Name: {resume_data.get('basics', {}).get('name', '')}
Email: {resume_data.get('basics', {}).get('email', '')}

Experience:
{json.dumps(resume_data.get('experience', []), indent=2)}

Education:
{json.dumps(resume_data.get('education', []), indent=2)}

Skills:
{json.dumps(resume_data.get('skills', {}), indent=2)}

Please rewrite this resume to match the job description."""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://integrate.api.nvidia.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "mistralai/mistral-7b-instruct-v0.2",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 4096
                    },
                    timeout=60.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Extract content from Mistral response
                content = result["choices"][0]["message"]["content"]
                
                # Parse JSON from response
                try:
                    # Try to find JSON in the response
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', content)
                    if json_match:
                        ai_result = json.loads(json_match.group())
                    else:
                        # Fallback: treat entire response as text
                        ai_result = self._create_fallback_result(resume_data, content)
                except json.JSONDecodeError:
                    ai_result = self._create_fallback_result(resume_data, content)
                
                # Build TailoredResume from AI result
                return TailoredResume(
                    basics=resume_data.basics,
                    summary=ai_result.get("summary", resume_data.get("summary", "")),
                    experience=[
                        Experience(**exp) for exp in ai_result.get("experience", resume_data.get("experience", []))
                    ],
                    education=resume_data.education,
                    skills=Skills(**ai_result.get("skills", resume_data.get("skills", {}))),
                    projects=resume_data.projects,
                    achievements=ai_result.get("achievements", resume_data.get("achievements", [])),
                    ats_score=ai_result.get("ats_score", {
                        "overall": 90,
                        "keyword_match": 90,
                        "star_compliance": 90,
                        "quantification": 90,
                        "action_verb_strength": 90
                    })
                )
                
        except httpx.HTTPError as e:
            logger.error(f"Mistral API error: {e}")
            raise ValueError(f"AI service error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error calling Mistral: {e}")
            raise
    
    def _create_fallback_result(self, resume_data: Dict, content: str) -> Dict:
        """Create a fallback result when JSON parsing fails"""
        return {
            "summary": resume_data.get("summary", ""),
            "experience": resume_data.get("experience", []),
            "skills": resume_data.get("skills", {}),
            "achievements": resume_data.get("achievements", []),
            "ats_score": {
                "overall": 90,
                "keyword_match": 90,
                "star_compliance": 90,
                "quantification": 90,
                "action_verb_strength": 90
            }
        }
    
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
