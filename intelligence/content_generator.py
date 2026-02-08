"""
Main Content Generator
Coordinates all intelligence modules to generate optimized resume
"""

from typing import Tuple, List, Dict, Optional
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
        
        # NEW: Handle sparse trailing page consolidation
        # If page 2+ is <20% filled, we should REMOVE weak content, not add more.
        if page_feedback and "CONSOLIDATE" in (page_feedback.suggestion or ""):
            print(f"DEBUG: CONSOLIDATION MODE - Page {page_feedback.current_page} is sparse ({page_feedback.fill_percentage}%)")
            return self._consolidate_resume(previous_resume, ats_feedback)
        
        # Build improvement prompt
        shortcomings = "\n".join(f"- {s}" for s in ats_feedback.shortcomings[:5])
        missing_kw = ", ".join(ats_feedback.missing_keywords[:10])
        weak_bullets_text = "\n".join(f"- {b}" for b in ats_feedback.weak_bullets[:5])
        current_resume_text = self._format_current_bullets(previous_resume)
        
        # Determine how many bullets to ask for based on page feedback
        bullets_needed = 7  # Default baseline (increased from 5)
        if page_feedback and page_feedback.needs_content:
            # If underfilled, ask for more content based on the suggestion
            try:
                # Extract number from suggestion string "Please add at least X more..."
                import re
                match = re.search(r'at least (\d+)', page_feedback.suggestion)
                if match:
                    suggested = int(match.group(1))
                    # Add buffer based on how underfilled we are
                    if page_feedback.fill_percentage < 70:
                        bullets_needed = suggested + 4  # Aggressive: +4 buffer
                    elif page_feedback.fill_percentage < 85:
                        bullets_needed = suggested + 3  # Moderate: +3 buffer
                    else:
                        bullets_needed = suggested + 2  # Standard: +2 buffer
            except:
                # Fallback if parsing fails
                if page_feedback.fill_percentage < 70:
                    bullets_needed = 12
                else:
                    bullets_needed = 8
        
        improvement_prompt = f"""You are an expert resume writer. The previous attempt scored {ats_feedback.overall}/100 and is {page_feedback.fill_percentage if page_feedback else 0}% filled.

To pass FAANG standards, the resume needs an ATS score >90 and should be >95% filled on each page.

JOB: {job_analysis.role_title}
SENIORITY: {job_analysis.seniority_level.value}

CURRENT RESUME CONTENT:
{current_resume_text}

SHORTCOMINGS:
{shortcomings}

REQUIRED KEYWORDS (INTEGRATE ALL OF THESE):
{missing_kw}

WEAK BULLETS TO FIX:
{weak_bullets_text}

INSTRUCTIONS:
1. Generate exactly {bullets_needed} NEW, high-impact achievement bullets.
2. INTEGRATE ALL REQUIRED KEYWORDS into these new bullets naturally.
3. Use the STAR (Situation, Task, Action, Result) format with quantifiable metrics ($, %, #).
4. Ensure the bullets match the seniority level ({job_analysis.seniority_level.value}).
5. Look at the CURRENT RESUME CONTENT and ensure the new bullets are additive or significantly better than existing ones.

Return valid JSON:
{{
    "improved_bullets": ["bullet 1", "bullet 2", ...],
    "replacement_map": {{"weak bullet text": "replacement bullet text"}}
}}
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
    
    def _call_ai_model_for_improvement(self, prompt: str) -> Dict:
        # Try KimiK2.5 primary
        try:
            return self._call_kimi_k2_5(prompt)
        except Exception:
            try:
                return self._call_stepfun_flash(prompt)
            except Exception:
                return {"bullets": [], "replacements": {}}
    
    def _call_kimi_k2_5(self, prompt: str) -> Dict:
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
            data = json.loads(json_match.group())
            return {
                "bullets": data.get("improved_bullets", []),
                "replacements": data.get("replacement_map", {})
            }
        return {"bullets": [], "replacements": {}}

    def _call_stepfun_flash(self, prompt: str) -> Dict:
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
            data = json.loads(json_match.group())
            return {
                "bullets": data.get("improved_bullets", []),
                "replacements": data.get("replacement_map", {})
            }
        return {"bullets": [], "replacements": {}}

    def _apply_improvements(
        self,
        resume: TailoredResume,
        improvements: Dict,
        job_analysis: JobAnalysis,
        ats_feedback: 'ATSScore'
    ) -> TailoredResume:
        from copy import deepcopy
        improved = deepcopy(resume)
        
        new_bullets = improvements.get("bullets", [])
        replacement_map = improvements.get("replacements", {})
        
        # Add missing keywords to skills section
        if improved.skills and ats_feedback.missing_keywords:
            existing = set([s.lower() for s in improved.skills.languages_frameworks + improved.skills.tools])
            for kw in ats_feedback.missing_keywords:
                if kw.lower() not in existing:
                    if any(tech in kw.lower() for tech in ['python', 'java', 'javascript', 'typescript', 'react', 'node', 'spring', 'aws', 'cloud']):
                        improved.skills.languages_frameworks.append(kw)
                    else:
                        improved.skills.tools.append(kw)
        
        # Apply specifically mapped replacements first
        for exp in improved.experience:
            updated_bullets = []
            for bullet in exp.bullets:
                # Check if this bullet should be replaced
                replaced = False
                normalized_bullet = bullet.lower().strip().strip('."')
                
                for weak, better in replacement_map.items():
                    normalized_weak = weak.lower().strip().strip('."')
                    
                    # Fuzzy match: if weak bullet text is largely contained in current bullet
                    # or if current bullet is largely contained in weak bullet text
                    if (normalized_weak in normalized_bullet and len(normalized_weak) > 10) or \
                       (normalized_bullet in normalized_weak and len(normalized_bullet) > 10):
                        updated_bullets.append(better)
                        replaced = True
                        break
                        
                if not replaced:
                    updated_bullets.append(bullet)
            exp.bullets = updated_bullets

        # Define sorted list of experiences
        sorted_exp = sorted(improved.experience, key=lambda x: x.startDate if hasattr(x, 'startDate') else "", reverse=True)

        # Distribute remaining NEW bullets across roles to fill page
        if new_bullets and sorted_exp:
            # Determine dynamic caps based on current page count
            # If we are on page 1 of 1, we should be generous to fill it.
            # If we are on page 3+, we should be strict to reduce length.
            current_pages = len(resume.pages) if hasattr(resume, 'pages') else 1
            
            if current_pages == 1:
                max_recent = 15  # Allow deep depth for single page
                max_older = 8
            else:
                max_recent = 10 # Standard cap for multi-page
                max_older = 6
                
            for i, bullet in enumerate(new_bullets):
                # Try to add to role 0 first if it has space
                if len(sorted_exp[0].bullets) < max_recent:
                    sorted_exp[0].bullets.append(bullet)
                    continue
                
                # Otherwise, try to find another role with space
                added = False
                for exp in sorted_exp[1:]:
                    if len(exp.bullets) < max_older:
                        exp.bullets.append(bullet)
                        added = True
                        break
                
                # If all roles are capped, stop adding
                if not added:
                    break
            
        return improved

    def _consolidate_resume(
        self,
        resume: TailoredResume,
        ats_feedback: 'ATSScore'
    ) -> TailoredResume:
        """
        Iteratively consolidate content by removing weak bullets ONE BY ONE.
        Stops when estimated fill fits on a single page.
        Then does a final polish pass to REPLACE (not add) any remaining weak bullets.
        """
        from copy import deepcopy
        consolidated = deepcopy(resume)
        
        # Get list of weak bullets from ATS feedback
        weak_bullets_set = set(b.lower().strip() for b in ats_feedback.weak_bullets)
        
        # Estimate current bullet count
        total_bullets = sum(len(exp.bullets) for exp in consolidated.experience)
        
        # Target: ~12-15 bullets for a single page (FAANG standard)
        # Each bullet is ~2.5 lines. 1 page ≈ 40 lines of content ≈ 16 bullets max
        TARGET_BULLETS = 14
        
        print(f"DEBUG: Consolidation START - Total bullets: {total_bullets}, Target: {TARGET_BULLETS}")
        
        # PHASE 1: Iterative removal (one by one)
        removed_count = 0
        
        while total_bullets > TARGET_BULLETS:
            # Find the weakest bullet to remove
            weakest_bullet = None
            weakest_exp = None
            weakest_score = float('inf')
            
            # Sort experiences oldest-first (trim older roles first)
            sorted_exp = sorted(consolidated.experience, key=lambda x: x.startDate if hasattr(x, 'startDate') else "", reverse=False)
            
            for exp in sorted_exp:
                for bullet in exp.bullets:
                    score = self._score_bullet_strength(bullet, weak_bullets_set)
                    if score < weakest_score:
                        weakest_score = score
                        weakest_bullet = bullet
                        weakest_exp = exp
            
            # Remove the weakest bullet
            if weakest_bullet and weakest_exp:
                weakest_exp.bullets.remove(weakest_bullet)
                removed_count += 1
                total_bullets -= 1
                print(f"DEBUG: Removed bullet (score {weakest_score}): {weakest_bullet[:40]}...")
                print(f"DEBUG: Remaining bullets: {total_bullets}")
            else:
                break  # No more bullets to remove
        
        print(f"DEBUG: Phase 1 complete - Removed {removed_count} bullets, now at {total_bullets}")
        
        # PHASE 2: Final Polish - Replace weak bullets WITHOUT increasing count
        # Find any remaining weak bullets and call AI to improve them
        weak_remaining = []
        for exp in consolidated.experience:
            for bullet in exp.bullets:
                score = self._score_bullet_strength(bullet, weak_bullets_set)
                if score < 50:  # Below threshold
                    weak_remaining.append((exp, bullet))
        
        if weak_remaining:
            print(f"DEBUG: Phase 2 - Polishing {len(weak_remaining)} weak bullets")
            consolidated = self._polish_weak_bullets(consolidated, weak_remaining, ats_feedback)
        
        return consolidated
    
    def _score_bullet_strength(self, bullet: str, weak_bullets_set: set) -> int:
        """
        Score a bullet from 0-100 based on strength.
        Lower score = weaker = more likely to be removed.
        """
        score = 50  # Base score
        normalized = bullet.lower().strip()
        
        # Penalty: matches known weak bullets
        for weak in weak_bullets_set:
            if weak in normalized or normalized in weak:
                score -= 30
                break
        
        # Penalty: too short
        if len(bullet) < 50:
            score -= 20
        
        # Penalty: no numbers (no quantification)
        if not any(char.isdigit() for char in bullet):
            score -= 15
        
        # Bonus: has strong action verbs
        strong_verbs = ['architected', 'engineered', 'spearheaded', 'optimized', 'reduced', 'increased', 'led', 'designed', 'implemented']
        if any(verb in normalized for verb in strong_verbs):
            score += 10
        
        # Bonus: has percentage or dollar signs
        if '%' in bullet or '$' in bullet:
            score += 10
        
        return max(0, min(100, score))
    
    def _polish_weak_bullets(
        self,
        resume: TailoredResume,
        weak_bullets: list,
        ats_feedback: 'ATSScore'
    ) -> TailoredResume:
        """
        Call AI to improve weak bullets WITHOUT adding new ones.
        """
        if not weak_bullets or not self.nvidia_api_key:
            return resume
        
        # Build a prompt to improve specific bullets
        weak_text = "\n".join([f"- {bullet}" for _, bullet in weak_bullets[:5]])
        missing_kw = ", ".join(ats_feedback.missing_keywords[:8])
        
        prompt = f"""You are an expert resume writer. Improve these weak resume bullets to be FAANG-standard.

WEAK BULLETS TO IMPROVE:
{weak_text}

REQUIRED KEYWORDS TO INTEGRATE:
{missing_kw}

RULES:
1. Return EXACTLY the same number of bullets as input.
2. Each improved bullet must use STAR format (Situation, Task, Action, Result).
3. Each bullet must have at least ONE quantified metric (%, $, numbers).
4. Integrate at least one required keyword per bullet.
5. Keep bullets under 120 characters.

OUTPUT FORMAT:
Return ONLY a JSON array of improved bullets, nothing else:
["Improved bullet 1", "Improved bullet 2", ...]
"""
        
        try:
            response = self._call_ai_model_for_improvement(prompt)
            improved_bullets = response.get("bullets", [])
            
            if improved_bullets and len(improved_bullets) == len(weak_bullets):
                # Replace weak bullets with improved versions
                for i, (exp, old_bullet) in enumerate(weak_bullets):
                    if i < len(improved_bullets):
                        idx = exp.bullets.index(old_bullet)
                        exp.bullets[idx] = improved_bullets[i]
                        print(f"DEBUG: Polished bullet: {old_bullet[:30]}... -> {improved_bullets[i][:30]}...")
        except Exception as e:
            print(f"DEBUG: Polish failed: {e}")
        
        return resume
