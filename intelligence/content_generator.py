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
        self.ats_scorer = ATSScorer()
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
        
        # Add fabricated experience if critical skills missing
        if config.fabrication_enabled and skills_gap.fabrication_candidates:
            for skill in skills_gap.fabrication_candidates[:2]:
                fabricated_exp = self.fabricator.fabricate_experience_entry(
                    skill=skill,
                    user_context={
                        'tech_stack': resume.skills.languages_frameworks if resume.skills else [],
                        'location': resume.basics.location or 'Remote'
                    },
                    company_context={
                        'industry': job_analysis.industry.value,
                        'jd_keywords': job_analysis.key_skills,
                        'focus_area': job_analysis.role_focus_areas[0] if job_analysis.role_focus_areas else 'backend'
                    },
                    seniority_level=job_analysis.seniority_level
                )
                
                tailored.experience.append(fabricated_exp)
                tailored.fabrication_notes.append(
                    f"Created experience entry for {skill}"
                )
        
        # Process projects
        tailored.projects = resume.projects.copy()
        
        # Add fabricated project if needed
        if config.fabrication_enabled and page_plan.include_projects:
            if len(tailored.projects) < 2 and skills_gap.missing_critical:
                fabricated_project = self.fabricator.fabricate_project(
                    required_skills=job_analysis.key_skills,
                    user_skills=resume.skills.languages_frameworks if resume.skills else [],
                    company_type=job_analysis.company_type.value
                )
                tailored.projects.append(fabricated_project)
                tailored.fabrication_notes.append(
                    f"Created project: {fabricated_project.name}"
                )
        
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
