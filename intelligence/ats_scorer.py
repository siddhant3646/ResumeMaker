"""
ATS Scoring Module - FAANG/MAANG Standards
Evaluates resume against ATS compatibility requirements
"""

import re
from typing import List, Dict, Tuple
from core.models import ATSScore, ParsedResume, JobAnalysis, SeniorityLevel


class ATSScorer:
    """Calculate ATS compatibility score using FAANG standards"""
    
    # STAR method indicators
    STAR_INDICATORS = {
        'situation': ['faced with', 'when', 'given', 'during', 'amidst', 'in response to'],
        'task': ['tasked with', 'responsible for', 'assigned to', 'needed to', 'required to'],
        'action': ['architected', 'spearheaded', 'engineered', 'designed', 'implemented', 
                   'built', 'developed', 'created', 'optimized', 'led', 'managed'],
        'result': ['resulting in', 'achieving', 'delivering', 'leading to', 'enabling', 
                   'reducing', 'improving', 'increasing', 'saving']
    }
    
    # Action verb tiers
    TIER_1_VERBS = ['architected', 'spearheaded', 'pioneered', 'orchestrated', 'championed',
                   'directed', 'drove', 'strategized', 'revolutionized', 'transformed']
    
    TIER_2_VERBS = ['engineered', 'designed', 'built', 'implemented', 'developed', 'launched',
                   'created', 'established', 'deployed', 'delivered', 'crafted', 'constructed']
    
    TIER_3_VERBS = ['optimized', 'refactored', 'enhanced', 'streamlined', 'accelerated',
                   'improved', 'upgraded', 'modernized', 'revamped', 'maintained', 'supported']
    
    WEAK_VERBS = ['worked on', 'helped with', 'assisted', 'participated', 'involved in',
                  'responsible for', 'tasked with', 'duties included']
    
    # Quantification patterns
    QUANT_PATTERNS = [
        r'\d+%',  # Percentages
        r'\d+K\+?',  # Thousands (e.g., 10K+)
        r'\d+M\+?',  # Millions (e.g., 2M+)
        r'\$\d+[K|M]?',  # Dollar amounts
        r'\d+ms',  # Milliseconds
        r'\d+RPS',  # Requests per second
        r'\d+\s*(million|billion|thousand)',  # Written numbers
        r'99\.\d+%',  # Uptime percentages
    ]
    
    def __init__(self):
        """Initialize scorer"""
        pass
    
    def calculate_score(
        self,
        resume,
        job_analysis: JobAnalysis
    ) -> ATSScore:
        """
        Calculate comprehensive ATS score
        Returns score breakdown across multiple dimensions
        """
        # Collect all resume text
        resume_text = self._extract_resume_text(resume)
        bullets = self._extract_all_bullets(resume)
        
        # Calculate component scores
        keyword_match = self._score_keyword_match(resume_text, job_analysis)
        star_compliance = self._score_star_compliance(bullets)
        quantification = self._score_quantification(bullets)
        action_verb_strength = self._score_action_verbs(bullets)
        format_compliance = self._score_format_compliance(resume)
        section_completeness = self._score_section_completeness(resume)
        
        # Calculate overall score (weighted average)
        overall = int(
            keyword_match * 0.25 +      # 25% - Keywords from JD
            star_compliance * 0.20 +     # 20% - STAR format compliance
            quantification * 0.20 +      # 20% - Quantified metrics
            action_verb_strength * 0.15 + # 15% - Strong action verbs
            format_compliance * 0.10 +   # 10% - ATS-friendly format
            section_completeness * 0.10  # 10% - Complete sections
        )
        
        # Generate suggestions
        suggestions = self._generate_suggestions(
            keyword_match, star_compliance, quantification,
            action_verb_strength, format_compliance, section_completeness,
            bullets, job_analysis
        )
        
        return ATSScore(
            overall=overall,
            keyword_match=keyword_match,
            star_compliance=star_compliance,
            quantification=quantification,
            action_verb_strength=action_verb_strength,
            format_compliance=format_compliance,
            section_completeness=section_completeness,
            suggestions=suggestions
        )
    
    def _extract_resume_text(self, resume: ParsedResume) -> str:
        """Extract all text from resume"""
        text_parts = []
        
        # Experience bullets
        for exp in resume.experience:
            text_parts.extend(exp.bullets)
            text_parts.append(exp.role)
            text_parts.append(exp.company)
        
        # Skills
        if resume.skills:
            text_parts.extend(resume.skills.languages_frameworks)
            text_parts.extend(resume.skills.tools)
        
        # Projects
        for proj in resume.projects:
            text_parts.append(proj.description)
            text_parts.append(proj.techStack)
        
        # Summary
        if resume.summary:
            text_parts.append(resume.summary)
        
        return ' '.join(text_parts).lower()
    
    def _extract_all_bullets(self, resume: ParsedResume) -> List[str]:
        """Extract all bullet points from resume"""
        bullets = []
        
        for exp in resume.experience:
            bullets.extend(exp.bullets)
        
        # Add project descriptions as bullets
        for proj in resume.projects:
            bullets.append(proj.description)
        
        # Add achievements
        bullets.extend(resume.achievements)
        
        return bullets
    
    def _score_keyword_match(self, resume_text: str, job_analysis: JobAnalysis) -> int:
        """Score keyword match with job description"""
        if not job_analysis.key_skills:
            return 100  # No requirements = perfect match
        
        required_skills = [s.lower() for s in job_analysis.key_skills]
        matched = sum(1 for skill in required_skills if skill in resume_text)
        
        # Check for partial matches (e.g., "React" matches "React.js")
        for skill in required_skills:
            if skill not in resume_text:
                # Check for variations
                variations = [skill, skill + '.js', skill + '.py', skill + 'js']
                if any(var in resume_text for var in variations):
                    matched += 0.5
        
        score = int((matched / len(required_skills)) * 100)
        return min(score, 100)
    
    def _score_star_compliance(self, bullets: List[str]) -> int:
        """Score STAR format compliance"""
        if not bullets:
            return 0
        
        compliant_count = 0
        
        for bullet in bullets:
            bullet_lower = bullet.lower()
            
            # Check for action verb (A)
            has_action = any(verb in bullet_lower for verb in 
                           self.TIER_1_VERBS + self.TIER_2_VERBS + self.TIER_3_VERBS)
            
            # Check for result (R) - has metrics or impact statement
            has_result = any(indicator in bullet_lower for indicator in self.STAR_INDICATORS['result'])
            has_metrics = any(re.search(pattern, bullet) for pattern in self.QUANT_PATTERNS)
            
            # STAR compliant if has action + (result or metrics)
            if has_action and (has_result or has_metrics):
                compliant_count += 1
        
        score = int((compliant_count / len(bullets)) * 100)
        return score
    
    def _score_quantification(self, bullets: List[str]) -> int:
        """Score presence of quantified metrics"""
        if not bullets:
            return 0
        
        quantified_count = 0
        
        for bullet in bullets:
            if any(re.search(pattern, bullet) for pattern in self.QUANT_PATTERNS):
                quantified_count += 1
        
        score = int((quantified_count / len(bullets)) * 100)
        return score
    
    def _score_action_verbs(self, bullets: List[str]) -> int:
        """Score strength of action verbs"""
        if not bullets:
            return 0
        
        total_score = 0
        
        for bullet in bullets:
            bullet_lower = bullet.lower()
            
            # Check verb tier
            if any(verb in bullet_lower for verb in self.TIER_1_VERBS):
                total_score += 100
            elif any(verb in bullet_lower for verb in self.TIER_2_VERBS):
                total_score += 75
            elif any(verb in bullet_lower for verb in self.TIER_3_VERBS):
                total_score += 50
            elif any(verb in bullet_lower for verb in self.WEAK_VERBS):
                total_score += 25
            else:
                total_score += 60  # Unknown verb, assume medium
        
        return int(total_score / len(bullets))
    
    def _score_format_compliance(self, resume: ParsedResume) -> int:
        """Score ATS-friendly format compliance"""
        score = 100
        
        # Check for standard sections
        if not resume.experience:
            score -= 30
        if not resume.education:
            score -= 20
        if not resume.skills or (not resume.skills.languages_frameworks and not resume.skills.tools):
            score -= 20
        
        # Check bullet length (should be 1-2 lines, ~25-30 words)
        for exp in resume.experience:
            for bullet in exp.bullets:
                word_count = len(bullet.split())
                if word_count > 35:
                    score -= 5  # Too long
                elif word_count < 10:
                    score -= 3  # Too short
        
        return max(score, 0)
    
    def _score_section_completeness(self, resume: ParsedResume) -> int:
        """Score completeness of resume sections"""
        score = 0
        
        # Basics (20 points)
        if resume.basics and resume.basics.name and resume.basics.email:
            score += 20
        
        # Experience (30 points)
        if resume.experience:
            score += min(len(resume.experience) * 10, 30)
        
        # Education (15 points)
        if resume.education:
            score += min(len(resume.education) * 7, 15)
        
        # Skills (15 points)
        if resume.skills:
            skill_count = len(resume.skills.languages_frameworks) + len(resume.skills.tools)
            score += min(skill_count * 2, 15)
        
        # Projects (10 points) - optional but good to have
        if resume.projects:
            score += min(len(resume.projects) * 5, 10)
        
        # Achievements (10 points) - optional
        if resume.achievements:
            score += min(len(resume.achievements) * 3, 10)
        
        return min(score, 100)
    
    def _generate_suggestions(
        self,
        keyword_match: int,
        star_compliance: int,
        quantification: int,
        action_verb_strength: int,
        format_compliance: int,
        section_completeness: int,
        bullets: List[str],
        job_analysis: JobAnalysis
    ) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        if keyword_match < 80:
            missing = [s for s in job_analysis.key_skills if s.lower() not in ' '.join(bullets).lower()]
            if missing:
                suggestions.append(f"Add keywords: {', '.join(missing[:5])}")
        
        if star_compliance < 80:
            suggestions.append("Use STAR format: Start with strong action verb and include quantified results")
        
        if quantification < 80:
            suggestions.append("Add metrics: Include percentages, scale (K/M), time savings, or dollar amounts")
        
        if action_verb_strength < 70:
            suggestions.append("Strengthen verbs: Use 'Architected', 'Engineered' instead of 'Worked on'")
        
        if format_compliance < 90:
            suggestions.append("Format check: Ensure standard sections and concise bullets (25-30 words)")
        
        if section_completeness < 80:
            suggestions.append("Add missing sections: Ensure Experience, Education, and Skills are complete")
        
        return suggestions
    
    def is_faang_ready(self, score: ATSScore) -> Tuple[bool, List[str]]:
        """Check if resume meets FAANG standards (>90)"""
        ready = score.overall >= 90
        issues = []
        
        if score.keyword_match < 85:
            issues.append("Keyword match below 85%")
        if score.star_compliance < 85:
            issues.append("STAR compliance below 85%")
        if score.quantification < 85:
            issues.append("Not enough quantified metrics")
        if score.action_verb_strength < 80:
            issues.append("Action verbs need strengthening")
        
        return ready, issues
