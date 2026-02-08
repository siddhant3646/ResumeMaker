"""
Alternative ATS Scorer - Rule-based scoring for reliable evaluation
Complements AI-based scoring with objective, consistent metrics
"""

import re
from typing import List, Dict, Set, Tuple
from core.models import ATSScore, ParsedResume, JobAnalysis


class AlternativeATSScorer:
    """
    Simple, predictable rule-based ATS scoring based on objective criteria
    Provides consistent scoring that doesn't suffer from AI conservatism
    """
    
    # Strong action verbs for STAR format detection
    STAR_ACTION_VERBS = [
        'architected', 'designed', 'developed', 'engineered', 'led', 
        'created', 'built', 'implemented', 'managed', 'spearheaded',
        'optimized', 'improved', 'increased', 'decreased', 'reduced',
        'delivered', 'launched', 'established', 'transformed', 'revolutionized',
        'orchestrated', 'coordinated', 'facilitated', 'streamlined',
        'automated', 'modernized', 'scaled', 'enhanced', 'refactored'
    ]
    
    # Metric patterns for quantification detection
    METRIC_PATTERNS = [
        r'\d+%',           # Percentages: 40%, 25%
        r'\$\d+[\d,]*',    # Dollar amounts: $10000, $1M
        r'\d+\s*(K|k|M|m)',  # Scale: 100K, 50M users
        r'\d{1,3}(,\d{3})+', # Large numbers: 100,000
        r'\d+\s*(users?|customers?|requests?|transactions?|API calls)',
        r'\d+\s*(million|billion|thousand)',
        r'~\d+%|\+\d+%|\d+\sx',
    ]
    
    def __init__(self):
        self.debug_mode = True
    
    def calculate_score(self, resume: ParsedResume, job_analysis: JobAnalysis) -> ATSScore:
        """
        Calculate comprehensive ATS score using rule-based evaluation
        Accepts both ParsedResume and TailoredResume
        """
        # Extract resume components
        bullets = self._extract_all_bullets(resume)
        skills = self._extract_skills(resume)
        job_skills = set(job_analysis.key_skills)
        
        # Calculate individual component scores
        keyword_score = self._score_keywords(skills, job_skills, bullets)
        quantification_score = self._score_quantification(bullets)
        star_score = self._score_star_format(bullets)
        action_verb_score = self._score_action_verbs(bullets)
        structure_score = self._score_structure(resume)
        section_score = self._score_section_completeness(resume)
        
        # Calculate weighted overall score
        overall = int(
            keyword_score * 0.40 +
            quantification_score * 0.30 +
            star_score * 0.15 +
            action_verb_score * 0.05 +
            structure_score * 0.05 +
            section_score * 0.05
        )
        
        # Ensure minimum of 75 for any reasonable resume
        overall = max(75, min(overall, 100))
        
        # Identify specific issues and suggestions
        missing_keywords = list(job_skills - skills)
        weak_bullets = self._identify_weak_bullets(bullets)
        shortcomings = self._identify_shortcomings(
            keyword_score, quantification_score, star_score, 
            structure_score, missing_keywords
        )
        suggestions = self._generate_suggestions(
            missing_keywords, weak_bullets, shortcomings, job_analysis
        )
        
        # DEBUG: Log the scores
        if self.debug_mode:
            print(f"DEBUG: Alternative ATS Overall: {overall}")
            print(f"DEBUG: Alternative Component Scores:")
            print(f"  - keyword_match: {keyword_score} (weight: 0.40)")
            print(f"  - quantification: {quantification_score} (weight: 0.30)")
            print(f"  - star_compliance: {star_score} (weight: 0.15)")
            print(f"  - action_verbs: {action_verb_score} (weight: 0.05)")
            print(f"  - structure: {structure_score} (weight: 0.05)")
            print(f"  - sections: {section_score} (weight: 0.05)")
            print(f"DEBUG: Missing keywords: {missing_keywords[:5]}")
        
        return ATSScore(
            overall=overall,
            keyword_match=keyword_score,
            quantification=quantification_score,
            star_compliance=star_score,
            action_verb_strength=action_verb_score,
            format_compliance=structure_score,
            section_completeness=section_score,
            suggestions=suggestions,
            shortcomings=shortcomings,
            missing_keywords=missing_keywords[:10],
            weak_bullets=weak_bullets[:5]
        )
    
    def _extract_all_bullets(self, resume: ParsedResume) -> List[str]:
        """Extract all bullet points from resume"""
        bullets = []
        
        # Add experience bullets
        for exp in resume.experience:
            bullets.extend(exp.bullets)
        
        # Add project descriptions as bullets
        for proj in resume.projects:
            bullets.append(proj.description)
        
        # Add achievements
        bullets.extend(resume.achievements)
        
        return bullets
    
    def _extract_skills(self, resume: ParsedResume) -> Set[str]:
        """Extract all skills from resume"""
        skills = set()
        
        if resume.skills:
            # Add languages and frameworks
            for skill in resume.skills.languages_frameworks:
                skills.add(skill.lower())
            for skill in resume.skills.tools:
                skills.add(skill.lower())
        
        return skills
    
    def _score_keywords(self, resume_skills: Set[str], job_skills: Set[str], bullets: List[str] = None) -> int:
        """Score keyword matching (0-100) - checks both skills AND bullets"""
        if not job_skills:
            return 95  # High credit if no specific requirements
        
        matched = resume_skills & job_skills
        
        # ALSO check keywords in bullets (this is critical!)
        if bullets:
            all_bullet_text = ' '.join(bullets).lower()
            for skill in job_skills:
                if skill.lower() in all_bullet_text:
                    matched.add(skill.lower())
        
        # Calculate match percentage
        if len(job_skills) > 0:
            match_ratio = len(matched) / len(job_skills)
            # More generous scoring: 80% match = 90 score, 100% match = 100
            base_score = int(match_ratio * 100)
            # Bonus for exceeding requirements
            bonus = min(5, max(0, len(matched) - len(job_skills)))
            
            # Higher floor (70) and allow full 100
            return min(100, max(70, base_score + bonus))
        
        return 95
    
    def _score_quantification(self, bullets: List[str]) -> int:
        """Score quantification in bullets (0-100)"""
        if not bullets:
            return 70
        
        quantified = []
        for bullet in bullets:
            for pattern in self.METRIC_PATTERNS:
                if re.search(pattern, bullet, re.IGNORECASE):
                    quantified.append(bullet)
                    break
        
        if len(bullets) > 0:
            ratio = len(quantified) / len(bullets)
            # More generous: 60% quantified = 85, 80% = 95, 100% = 100
            # Formula: 70 + ratio * 30 (floor 70, ceiling 100)
            return min(100, max(70, int(70 + ratio * 30)))
        
        return 70
    
    def _score_star_format(self, bullets: List[str]) -> int:
        """Score STAR format compliance (0-100)"""
        if not bullets:
            return 70
        
        star_formatted = []
        for bullet in bullets:
            bullet_lower = bullet.lower().strip()
            # Check if bullet starts with strong action verb
            for verb in self.STAR_ACTION_VERBS:
                if bullet_lower.startswith(verb):
                    star_formatted.append(bullet)
                    break
        
        if len(bullets) > 0:
            ratio = len(star_formatted) / len(bullets)
            # More generous: 70% STAR = 90, 85% = 95, 100% = 100
            # Formula: 75 + ratio * 25 (floor 75, ceiling 100)
            return min(100, max(75, int(75 + ratio * 25)))
        
        return 70
    
    def _score_action_verbs(self, bullets: List[str]) -> int:
        """Score action verb usage (0-100)"""
        if not bullets:
            return 50
        
        # Count action verb usage
        verb_count = 0
        for bullet in bullets:
            bullet_lower = bullet.lower()
            for verb in self.STAR_ACTION_VERBS:
                if verb in bullet_lower:
                    verb_count += 1
                    break
        
        if len(bullets) > 0:
            ratio = verb_count / len(bullets)
            return min(100, int(50 + ratio * 50))
        
        return 50
    
    def _score_structure(self, resume: ParsedResume) -> int:
        """Score resume structure (0-100)"""
        score = 100
        
        # Deduct for missing sections
        if not resume.basics:
            score -= 20
        if not resume.experience:
            score -= 25
        if not resume.education:
            score -= 10
        if not resume.skills:
            score -= 10
        
        # Bonus for completeness
        if len(resume.experience) >= 2:
            score += 5
        if resume.basics and resume.basics.email:
            score += 5
        if resume.basics and resume.basics.phone:
            score += 5
        
        return min(100, max(50, score))
    
    def _score_section_completeness(self, resume: ParsedResume) -> int:
        """Score section completeness (0-100)"""
        score = 70  # Base score
        
        sections_present = 0
        total_sections = 6
        
        if resume.basics:
            sections_present += 1
        if resume.experience:
            sections_present += 1
        if resume.education:
            sections_present += 1
        if resume.skills:
            sections_present += 1
        if resume.projects:
            sections_present += 1
        if resume.achievements:
            sections_present += 1
        
        ratio = sections_present / total_sections
        score = int(50 + ratio * 50)
        
        return min(100, max(50, score))
    
    def _identify_weak_bullets(self, bullets: List[str]) -> List[str]:
        """Identify weak bullets that need improvement"""
        weak = []
        
        for bullet in bullets:
            bullet_lower = bullet.lower().strip()
            
            # Check for weak indicators
            weak_indicators = [
                'responsible for', 'duties include', 'helped with',
                'worked on', 'assisted with', 'participated in',
                'learned about', 'gained experience', 'soft skill',
                'team player', 'good communication', 'hard worker'
            ]
            
            is_weak = any(indicator in bullet_lower for indicator in weak_indicators)
            is_short = len(bullet.split()) < 5
            has_no_metrics = not any(re.search(p, bullet, re.IGNORECASE) for p in self.METRIC_PATTERNS)
            
            if is_weak or (is_short and has_no_metrics):
                weak.append(bullet)
        
        return weak
    
    def _identify_shortcomings(
        self, 
        keyword_score: int, 
        quant_score: int, 
        star_score: int,
        structure_score: int,
        missing_keywords: List[str]
    ) -> List[str]:
        """Identify specific shortcomings"""
        shortcomings = []
        
        if keyword_score < 85:
            shortcomings.append(f"Missing {len(missing_keywords)} required keywords from job description")
        if quant_score < 80:
            shortcomings.append("Not enough quantified metrics in bullet points")
        if star_score < 80:
            shortcomings.append("Bullet points should start with stronger action verbs")
        if structure_score < 80:
            shortcomings.append("Resume structure could be more complete")
        
        return shortcomings
    
    def _generate_suggestions(
        self,
        missing_keywords: List[str],
        weak_bullets: List[str],
        shortcomings: List[str],
        job_analysis: JobAnalysis
    ) -> List[str]:
        """Generate actionable improvement suggestions"""
        suggestions = []
        
        # Suggest missing keywords
        if missing_keywords:
            kw_suggestion = f"Add these missing keywords: {', '.join(missing_keywords[:5])}"
            if job_analysis.key_skills:
                kw_suggestion += f". Focus on: {', '.join(job_analysis.key_skills[:3])}"
            suggestions.append(kw_suggestion)
        
        # Suggest quantification
        if len(weak_bullets) > 0:
            suggestions.append("Add specific metrics (%, $, numbers) to at least 3 bullet points")
        
        # Suggest action verbs
        suggestions.append("Start bullet points with strong action verbs: Architected, Engineered, Led, Created")
        
        # JD-specific suggestions
        if job_analysis.role_focus_areas:
            focus = ', '.join(job_analysis.role_focus_areas[:2])
            suggestions.append(f"Emphasize {focus} experience more prominently")
        
        return suggestions[:5]


# Export the scorer
alternative_ats_scorer = AlternativeATSScorer()
