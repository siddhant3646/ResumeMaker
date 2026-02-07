"""
Main Content Generator
Coordinates all intelligence modules to generate optimized resume
"""

from typing import Tuple, List
from core.models import (
    ParsedResume, TailoredResume, JobAnalysis, GenerationConfig,
    Experience, Project, ATSScore, Skills, SkillsGapReport, ContentPlan
)
from intelligence.role_detector import RoleDetector
from intelligence.fabricator import FAANGBulletGenerator, ExperienceFabricator
from intelligence.ats_scorer import ATSScorer
from intelligence.skills_gap_analyzer import SkillsGapAnalyzer
from intelligence.page_manager import PageManager


class ContentGenerator:
    """
    Main coordinator for resume content generation
    Orchestrates all intelligence modules
    """
    
    def __init__(self, gemma_api_key: str, nvidia_api_key: str):
        self.gemma_api_key = gemma_api_key
        self.nvidia_api_key = nvidia_api_key
        
        # Initialize all modules
        self.role_detector = RoleDetector(gemma_api_key)
        self.bullet_generator = FAANGBulletGenerator(gemma_api_key)
        self.fabricator = ExperienceFabricator(gemma_api_key, enabled=True)
        self.ats_scorer = ATSScorer(gemma_api_key)
        self.skills_analyzer = SkillsGapAnalyzer()
        self.page_manager = PageManager()
    
    def generate_tailored_resume(
        self,
        resume: ParsedResume,
        job_description: str,
        config: GenerationConfig
    ) -> Tuple[TailoredResume, JobAnalysis]:
        """
        Main generation pipeline
        Returns tailored resume and job analysis
        """
        # Step 1: Analyze job description
        job_analysis = self.role_detector.analyze_job_description(job_description)
        
        # Step 2: Calculate match score
        match_score = self.role_detector.calculate_match_score(job_analysis, resume)
        job_analysis.match_score = match_score
        
        # Step 3: Analyze skills gaps
        skills_gap = self.skills_analyzer.analyze_gaps(resume, job_analysis)
        job_analysis.missing_from_resume = skills_gap.missing_critical
        
        # Step 4: Calculate content plan
        page_plan = self.page_manager.calculate_optimal_content(
            resume, job_analysis, config.fabrication_enabled
        )
        
        # Step 5: Generate tailored content
        tailored = self._generate_content(
            resume, job_analysis, skills_gap, page_plan, config
        )
        
        return tailored, job_analysis
    
    def _generate_content(
        self,
        resume: ParsedResume,
        job_analysis: JobAnalysis,
        skills_gap: SkillsGapReport,
        page_plan: ContentPlan,
        config: GenerationConfig
    ) -> TailoredResume:
        """Generate optimized content"""
        
        # Create tailored resume from original
        tailored = TailoredResume(
            basics=resume.basics,
            summary=resume.summary if page_plan.include_summary else None,
            education=resume.education.copy(),
            experience=[],
            skills=resume.skills,
            projects=[],
            achievements=resume.achievements.copy() if page_plan.include_achievements else [],
            fabrication_notes=[]
        )
        
        # Process each experience entry
        for idx, exp in enumerate(resume.experience):
            is_most_recent = (idx == 0)
            target_bullets = page_plan.bullets_per_experience.get(exp.company, 4 if is_most_recent else 2)
            
            # Enhance existing bullets
            enhanced_bullets = self._enhance_bullets(
                exp.bullets,
                job_analysis,
                target_bullets,
                config
            )
            
            # Add fabricated bullets if needed and enabled
            if config.fabrication_enabled and len(enhanced_bullets) < target_bullets:
                fabricated = self._add_fabricated_bullets(
                    exp, job_analysis, target_bullets - len(enhanced_bullets), config
                )
                enhanced_bullets.extend(fabricated)
                tailored.fabrication_notes.append(
                    f"Added {len(fabricated)} bullets to {exp.company} experience"
                )
            
            # Create enhanced experience entry
            enhanced_exp = Experience(
                company=exp.company,
                role=exp.role,
                startDate=exp.startDate,
                endDate=exp.endDate,
                location=exp.location,
                bullets=enhanced_bullets[:target_bullets],  # Limit to target
                is_fabricated=exp.is_fabricated
            )
            
            tailored.experience.append(enhanced_exp)
        
        # NOTE: Experience entries (company, role, tenure) are NEVER fabricated
        # Only bullet points within existing experiences can be enhanced/fabricated
        
        # Process projects (no fabrication - only use existing projects)
        tailored.projects = resume.projects.copy()
        
        # Enhance skills section
        if tailored.skills:
            tailored.skills = self._enhance_skills(tailored.skills, job_analysis)
        
        # Add summary if 2+ pages
        if page_plan.include_summary and not tailored.summary:
            tailored.summary = self._generate_summary(tailored, job_analysis)
        
        # Calculate ATS score
        tailored.ats_score = self.ats_scorer.calculate_score(tailored, job_analysis)
        
        return tailored
    
    def _enhance_bullets(
        self,
        bullets: List[str],
        job_analysis: JobAnalysis,
        target_count: int,
        config: GenerationConfig
    ) -> List[str]:
        """Enhance existing bullets with STAR format and metrics"""
        enhanced = []
        
        for bullet in bullets:
            # Enhance with FAANG standards
            enhanced_bullet = self.bullet_generator.enhance_existing_bullet(
                bullet=bullet,
                seniority_level=job_analysis.seniority_level,
                jd_keywords=job_analysis.key_skills
            )
            enhanced.append(enhanced_bullet)
        
        return enhanced
    
    def _add_fabricated_bullets(
        self,
        exp: Experience,
        job_analysis: JobAnalysis,
        count: int,
        config: GenerationConfig
    ) -> List[str]:
        """Add fabricated bullets to fill gaps"""
        fabricated = []
        
        # Determine focus area from role/company
        focus_area = 'backend'  # Default
        if any(term in exp.role.lower() for term in ['frontend', 'ui', 'react', 'angular']):
            focus_area = 'frontend'
        elif any(term in exp.role.lower() for term in ['devops', 'infra', 'sre']):
            focus_area = 'devops'
        elif any(term in exp.role.lower() for term in ['data', 'ml', 'ai']):
            focus_area = 'data'
        
        # Get user's tech stack
        user_tech = []  # Would extract from resume
        
        # Generate bullets for missing skills
        for skill in job_analysis.key_skills[:count]:
            bullet = self.bullet_generator.generate_optimized_bullet(
                skill=skill,
                jd_keywords=job_analysis.key_skills,
                user_tech_stack=user_tech,
                seniority_level=job_analysis.seniority_level,
                focus_area=focus_area
            )
            fabricated.append(bullet)
        
        return fabricated
    
    def _enhance_skills(self, skills: 'Skills', job_analysis: JobAnalysis) -> 'Skills':
        """Enhance skills section with JD keywords"""
        from core.models import Skills
        
        # Add missing key skills if not present
        existing = set([s.lower() for s in skills.languages_frameworks + skills.tools])
        
        for skill in job_analysis.key_skills:
            if skill.lower() not in existing:
                # Add to appropriate category
                if skill.lower() in ['python', 'java', 'javascript', 'typescript', 'go', 'rust', 'c++', 'c#']:
                    skills.languages_frameworks.append(skill)
                else:
                    skills.tools.append(skill)
        
        return skills
    
    def _generate_summary(self, resume: TailoredResume, job_analysis: JobAnalysis) -> str:
        """Generate professional summary"""
        # Simple template-based summary
        years = sum(1 for _ in resume.experience)
        
        summary = (
            f"Experienced {job_analysis.role_title} with {years}+ years building "
            f"scalable systems and delivering high-impact solutions. "
            f"Proficient in {', '.join(job_analysis.key_skills[:3])}. "
            f"Passionate about {', '.join(job_analysis.role_focus_areas[:2] if job_analysis.role_focus_areas else ['system design', 'optimization'])}."
        )
        
        return summary
    
    def get_generation_stats(self, result: TailoredResume) -> dict:
        """Get statistics about generation"""
        total_bullets = sum(len(exp.bullets) for exp in result.experience)
        fabricated_count = sum(1 for exp in result.experience if exp.is_fabricated)
        
        return {
            'total_experiences': len(result.experience),
            'total_bullets': total_bullets,
            'fabricated_entries': fabricated_count,
            'fabrication_notes': len(result.fabrication_notes),
            'projects': len(result.projects),
            'ats_score': result.ats_score.overall if result.ats_score else 0
        }
    
    def regenerate_with_feedback(
        self,
        previous_resume: TailoredResume,
        original_resume: ParsedResume,
        job_analysis: JobAnalysis,
        ats_feedback: 'ATSScore',
        config: GenerationConfig
    ) -> TailoredResume:
        """
        Regenerate resume using Gemma's ATS feedback to fix shortcomings.
        Uses the shortcomings, missing_keywords, and weak_bullets from ATS scoring.
        """
        import requests
        
        # Build improvement prompt with ATS feedback
        shortcomings = "\n".join(f"- {s}" for s in ats_feedback.shortcomings[:5])
        missing_kw = ", ".join(ats_feedback.missing_keywords[:10])
        weak_bullets_text = "\n".join(f"- {b}" for b in ats_feedback.weak_bullets[:5])
        
        improvement_prompt = f"""You are an expert resume writer. The previous resume attempt scored {ats_feedback.overall}/100 on ATS.
To pass FAANG standards, it needs >90.

**JOB REQUIREMENTS:**
- Role: {job_analysis.role_title}
- Seniority: {job_analysis.seniority_level.value}
- Required Skills: {', '.join(job_analysis.key_skills[:10])}

**SHORTCOMINGS FROM ATS EVALUATION (FIX THESE):**
{shortcomings}

**MISSING KEYWORDS (MUST ADD THESE):**
{missing_kw}

**WEAK BULLETS TO IMPROVE:**
{weak_bullets_text}

**CURRENT BULLETS:**
{self._format_current_bullets(previous_resume)}

**YOUR TASK:**
Generate improved bullet points that:
1. Include ALL missing keywords naturally
2. Fix the shortcomings identified
3. Use STAR format (Situation, Task, Action, Result)
4. Include quantified metrics (%, $, scale like K/M)
5. Start with strong action verbs (Architected, Engineered, Spearheaded)

Return a JSON array of improved bullets:
{{"improved_bullets": ["bullet 1", "bullet 2", ...]}}
"""
        
        try:
            # Use AI model (KimiK2.5 primary, StepFun fallback) for regeneration
            print(f"DEBUG: Starting regeneration with {len(ats_feedback.shortcomings)} shortcomings")
            improved_bullets = self._call_ai_model_for_improvement(improvement_prompt)
            
            # Apply improvements to resume
            print(f"DEBUG: Applying {len(improved_bullets)} improvements to resume")
            improved_resume = self._apply_improvements(
                previous_resume, improved_bullets, job_analysis, ats_feedback
            )
            
            # Recalculate ATS score
            print(f"DEBUG: Recalculating ATS score for improved resume")
            improved_resume.ats_score = self.ats_scorer.calculate_score(
                improved_resume, job_analysis
            )
            print(f"DEBUG: New ATS score: {improved_resume.ats_score.overall if improved_resume.ats_score else 'None'}")
            
            improved_resume.fabrication_notes.append(
                f"Regenerated with ATS feedback. Previous score: {ats_feedback.overall}"
            )
            
            print(f"DEBUG: Returning improved resume with {len(improved_resume.fabrication_notes)} fabrication notes")
            return improved_resume
            
        except Exception as e:
            # Fallback: just return previous with note
            previous_resume.fabrication_notes.append(f"Regeneration failed: {str(e)}")
            return previous_resume
    
    def _format_current_bullets(self, resume: TailoredResume) -> str:
        """Format current bullets for the improvement prompt"""
        lines = []
        for exp in resume.experience:
            lines.append(f"\n[{exp.company} - {exp.role}]")
            for bullet in exp.bullets:
                lines.append(f"  - {bullet}")
        return "\n".join(lines)
    
    def _call_ai_model_for_improvement(self, prompt: str) -> List[str]:
        """Call AI model (KimiK2.5 primary, StepFun fallback) to get improved bullets"""
        import requests
        import json
        
        # Try KimiK2.5 first
        try:
            result = self._call_kimi_k2_5(prompt)
            print(f"DEBUG: KimiK2.5 returned {len(result)} improved bullets")
            return result
        except Exception as e:
            print(f"KimiK2.5 failed: {e}, trying StepFun fallback...")
            try:
                result = self._call_stepfun_flash(prompt)
                print(f"DEBUG: StepFun returned {len(result)} improved bullets")
                return result
            except Exception as e2:
                print(f"Both models failed: {e2}")
                return []
    
    def _call_kimi_k2_5(self, prompt: str) -> List[str]:
        """Call KimiK2.5 via NVIDIA API"""
        import requests
        import json
        
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.nvidia_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "moonshotai/kimi-k2.5",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 1.00,
            "top_p": 1.00,
            "max_tokens": 32000,
            "chat_template_kwargs": {"thinking": True},
            "stream": False
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=180)
        response.raise_for_status()
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Parse JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            data = json.loads(json_match.group())
            return data.get("improved_bullets", [])
        
        return []
    
    def _call_stepfun_flash(self, prompt: str) -> List[str]:
        """Call StepFun Flash via OpenAI Client"""
        import json
        try:
            from openai import OpenAI
            
            client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=self.nvidia_api_key
            )
            
            response = client.chat.completions.create(
                model="stepfun-ai/step-3.5-flash",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=32000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content if response.choices else ""
            
            # Parse JSON from response
            import re
            if content:
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    data = json.loads(json_match.group())
                    return data.get("improved_bullets", [])
                else:
                    print(f"DEBUG: No JSON found in StepFun response: {content[:200]}...")
                    return []
            else:
                print("DEBUG: No content in StepFun response")
                return []
            
        except ImportError:
            # Fallback if OpenAI not available
            raise Exception("StepFun fallback requires 'openai' library")
        except Exception as e:
            raise Exception(f"StepFun API call failed: {e}")
    
    def _apply_improvements(
        self,
        resume: TailoredResume,
        improved_bullets: List[str],
        job_analysis: JobAnalysis,
        ats_feedback: 'ATSScore'
    ) -> TailoredResume:
        """Apply improved bullets to resume"""
        from copy import deepcopy
        
        improved = deepcopy(resume)
        
        # Add missing keywords to skills
        if improved.skills and ats_feedback.missing_keywords:
            for kw in ats_feedback.missing_keywords:
                if kw.lower() not in [s.lower() for s in improved.skills.languages_frameworks + improved.skills.tools]:
                    improved.skills.tools.append(kw)
        
        # Replace weak bullets with improved ones
        bullet_idx = 0
        weak_set = set(b.lower().strip() for b in ats_feedback.weak_bullets)
        
        # Debug: Print what we're working with
        print(f"DEBUG: Weak bullets to replace: {ats_feedback.weak_bullets[:3]}")
        print(f"DEBUG: Improved bullets available: {improved_bullets[:3]}")
        
        for exp in improved.experience:
            new_bullets = []
            for bullet in exp.bullets:
                if bullet.lower().strip() in weak_set and bullet_idx < len(improved_bullets):
                    new_bullets.append(improved_bullets[bullet_idx])
                    print(f"DEBUG: Replaced bullet: {bullet[:50]}... -> {improved_bullets[bullet_idx][:50]}...")
                    bullet_idx += 1
                else:
                    new_bullets.append(bullet)
            exp.bullets = new_bullets
        
        # If we have extra improved bullets, add them to first experience
        if bullet_idx < len(improved_bullets) and improved.experience:
            remaining = improved_bullets[bullet_idx:]
            improved.experience[0].bullets.extend(remaining[:2])  # Add up to 2 more
        
        return improved
