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
    Main coordinator for resume content generation using Mistral Large 3
    Orchestrates all intelligence modules
    """
    
    def __init__(self, api_key: str, nvidia_api_key: str):
        self.api_key = api_key
        self.nvidia_api_key = nvidia_api_key
        
        # Initialize all modules using Mistral (via api_key) where applicable
        self.role_detector = RoleDetector(api_key)
        self.bullet_generator = FAANGBulletGenerator(api_key)
        self.fabricator = ExperienceFabricator(api_key, enabled=True)
        self.ats_scorer = ATSScorer(api_key)
        self.skills_analyzer = SkillsGapAnalyzer()
        self.page_manager = PageManager()
        
        # Initialize hybrid scorer for better scoring
        try:
            from intelligence.hybrid_ats_scorer import HybridATSScorer
            self.hybrid_scorer = HybridATSScorer(api_key)
            self.use_hybrid_scoring = True
            print("DEBUG: Hybrid ATS scorer initialized successfully")
        except ImportError:
            self.use_hybrid_scoring = False
            print("DEBUG: Hybrid scorer not available, using AI scorer only")
    
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
            target_bullets = page_plan.bullets_per_experience.get(exp.company, 8 if is_most_recent else 4)
            
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
        
        # Process projects (no fabrication - only use existing projects)
        tailored.projects = resume.projects.copy()
        
        # Enhance skills section
        if tailored.skills:
            tailored.skills = self._enhance_skills(tailored.skills, job_analysis)
        
        # Add summary if 2+ pages
        if page_plan.include_summary and not tailored.summary:
            tailored.summary = self._generate_summary(tailored, job_analysis)
        
        # Calculate ATS score
        if self.use_hybrid_scoring and hasattr(self, 'hybrid_scorer'):
            tailored.ats_score = self.hybrid_scorer.calculate_score(tailored, job_analysis)
        else:
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
        focus_area = 'backend'
        if any(term in exp.role.lower() for term in ['frontend', 'ui', 'react', 'angular']):
            focus_area = 'frontend'
        elif any(term in exp.role.lower() for term in ['devops', 'infra', 'sre']):
            focus_area = 'devops'
        elif any(term in exp.role.lower() for term in ['data', 'ml', 'ai']):
            focus_area = 'data'
        
        user_tech = []
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
        existing = set([s.lower() for s in skills.languages_frameworks + skills.tools])
        for skill in job_analysis.key_skills:
            if skill.lower() not in existing:
                if skill.lower() in ['python', 'java', 'javascript', 'typescript', 'go', 'rust', 'c++', 'c#']:
                    skills.languages_frameworks.append(skill)
                else:
                    skills.tools.append(skill)
        return skills
    
    def _generate_summary(self, resume: TailoredResume, job_analysis: JobAnalysis) -> str:
        """Generate professional summary"""
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
        config: GenerationConfig,
        retry_count: int = 1,
        page_feedback=None
    ) -> TailoredResume:
        """
        Regenerate resume using Mistral's ATS feedback to fix shortcomings.
        """
        print(f"DEBUG: regenerate_with_feedback ENTERED - retry {retry_count}")
        
        # Add page fill feedback if provided
        if page_feedback and page_feedback.needs_content:
            ats_feedback.shortcomings.append(f"PAGE FILL: {page_feedback.suggestion}")
            ats_feedback.suggestions.append(
                f"Add {3 if page_feedback.fill_percentage < 80 else 2} fabricated quantified achievements to fill page properly."
            )
        
        # Build improvement prompt
        shortcomings = "\n".join(f"- {s}" for s in ats_feedback.shortcomings[:5])
        missing_kw = ", ".join(ats_feedback.missing_keywords[:10])
        weak_bullets_text = "\n".join(f"- {b}" for b in ats_feedback.weak_bullets[:5])
        
        improvement_prompt = f"""You are an expert resume writer. The previous attempt scored {ats_feedback.overall}/100.
To pass FAANG standards, it needs >90.

JOB: {job_analysis.role_title}
SENIORITY: {job_analysis.seniority_level.value}

SHORTCOMINGS:
{shortcomings}

MISSING KEYWORDS:
{missing_kw}

WEAK BULLETS:
{weak_bullets_text}
"""
        
        try:
            improved_bullets = self._call_ai_model_for_improvement(improvement_prompt)
            improved_resume = self._apply_improvements(
                previous_resume, improved_bullets, job_analysis, ats_feedback
            )
            
            if self.use_hybrid_scoring and hasattr(self, 'hybrid_scorer'):
                improved_resume.ats_score = self.hybrid_scorer.calculate_score(
                    improved_resume, job_analysis, retry_count=retry_count
                )
            else:
                improved_resume.ats_score = self.ats_scorer.calculate_score(
                    improved_resume, job_analysis
                )
            
            improved_resume.fabrication_notes.append(f"Regenerated with ATS feedback (score: {ats_feedback.overall})")
            return improved_resume
        except Exception as e:
            previous_resume.fabrication_notes.append(f"Regeneration failed: {str(e)}")
            return previous_resume

    def _format_current_bullets(self, resume: TailoredResume) -> str:
        lines = []
        for exp in resume.experience:
            lines.append(f"\n[{exp.company} - {exp.role}]")
            for bullet in exp.bullets:
                lines.append(f"  - {bullet}")
        return "\n".join(lines)
    
    def _call_ai_model_for_improvement(self, prompt: str) -> List[str]:
        # Try KimiK2.5 primary
        try:
            return self._call_kimi_k2_5(prompt)
        except Exception:
            try:
                return self._call_stepfun_flash(prompt)
            except Exception:
                return []
    
    def _call_kimi_k2_5(self, prompt: str) -> List[str]:
        import requests
        import json
        import re
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.nvidia_api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "moonshotai/kimi-k2.5",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 1.0,
            "max_tokens": 8000,
            "stream": False
        }
        response = requests.post(url, headers=headers, json=payload, timeout=180)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            return json.loads(json_match.group()).get("improved_bullets", [])
        return []

    def _call_stepfun_flash(self, prompt: str) -> List[str]:
        import requests
        import json
        import re
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.nvidia_api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "stepfun-ai/step-3.5-flash",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 8000,
            "stream": False
        }
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            return json.loads(json_match.group()).get("improved_bullets", [])
        return []

    def _apply_improvements(
        self,
        resume: TailoredResume,
        improved_bullets: List[str],
        job_analysis: JobAnalysis,
        ats_feedback: 'ATSScore'
    ) -> TailoredResume:
        from copy import deepcopy
        improved = deepcopy(resume)
        
        # Add missing keywords
        if improved.skills and ats_feedback.missing_keywords:
            existing = set([s.lower() for s in improved.skills.languages_frameworks + improved.skills.tools])
            for kw in ats_feedback.missing_keywords:
                if kw.lower() not in existing:
                    if any(tech in kw.lower() for tech in ['python', 'java', 'javascript', 'typescript', 'react', 'node']):
                        improved.skills.languages_frameworks.append(kw)
                    else:
                        improved.skills.tools.append(kw)
        
        # Replace weak bullets
        bullet_idx = 0
        weak_set = set(b.lower().strip() for b in ats_feedback.weak_bullets)
        for exp in improved.experience:
            new_bullets = []
            for bullet in exp.bullets:
                if bullet.lower().strip() in weak_set and bullet_idx < len(improved_bullets):
                    new_bullets.append(improved_bullets[bullet_idx])
                    bullet_idx += 1
                else:
                    new_bullets.append(bullet)
            exp.bullets = new_bullets
            
        return improved
