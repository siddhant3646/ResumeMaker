"""
Skills Gap Analyzer
Identifies missing skills and suggests strategies to address gaps
"""

from typing import List, Dict, Set, Tuple
from core.models import SkillsGapReport, ParsedResume, JobAnalysis


class SkillsGapAnalyzer:
    """Analyze gaps between user skills and job requirements"""
    
    # Skill similarity mappings for reframing
    SKILL_SYNONYMS = {
        # Programming Languages
        'python': ['django', 'flask', 'fastapi', 'pandas', 'numpy', 'ml'],
        'javascript': ['js', 'typescript', 'ts', 'node', 'nodejs', 'react', 'angular', 'vue'],
        'java': ['spring', 'spring boot', 'jvm', 'kotlin', 'android'],
        'go': ['golang'],
        'c++': ['cpp', 'cplusplus'],
        'c#': ['csharp', 'dotnet', '.net'],
        
        # Frontend
        'react': ['reactjs', 'react.js', 'frontend', 'ui', 'spa'],
        'angular': ['angularjs', 'frontend', 'spa'],
        'vue': ['vuejs', 'vue.js', 'frontend', 'spa'],
        
        # Backend
        'django': ['python', 'backend', 'web framework'],
        'flask': ['python', 'backend', 'microframework'],
        'spring': ['java', 'spring boot', 'backend', 'enterprise'],
        'express': ['nodejs', 'node', 'backend', 'api'],
        
        # Databases
        'postgresql': ['postgres', 'sql', 'rdbms', 'database'],
        'mysql': ['sql', 'rdbms', 'database'],
        'mongodb': ['mongo', 'nosql', 'document database'],
        'redis': ['cache', 'in-memory', 'database'],
        'elasticsearch': ['elastic', 'search', 'elk'],
        
        # Cloud
        'aws': ['amazon web services', 'cloud', 'ec2', 's3', 'lambda'],
        'azure': ['microsoft azure', 'cloud'],
        'gcp': ['google cloud', 'google cloud platform'],
        
        # DevOps
        'docker': ['containerization', 'containers'],
        'kubernetes': ['k8s', 'container orchestration', 'docker'],
        'jenkins': ['ci/cd', 'pipeline', 'automation'],
        'terraform': ['infrastructure as code', 'iac', 'devops'],
        
        # Data/ML
        'tensorflow': ['tf', 'deep learning', 'ml', 'ai'],
        'pytorch': ['torch', 'deep learning', 'ml', 'ai'],
        'kafka': ['event streaming', 'message queue', 'pub sub'],
        'spark': ['apache spark', 'big data', 'data processing'],
        
        # Mobile
        'react native': ['mobile', 'cross platform', 'ios', 'android'],
        'flutter': ['dart', 'mobile', 'cross platform'],
        'swift': ['ios', 'mobile', 'apple'],
        'kotlin': ['android', 'mobile', 'java'],
    }
    
    # Transferrable skill mappings
    TRANSFERRABLE_SKILLS = {
        'aws': ['cloud computing', 'cloud infrastructure', 'cloud services'],
        'docker': ['containerization', 'container orchestration', 'microservices deployment'],
        'kubernetes': ['container management', 'orchestration', 'scalable deployment'],
        'react': ['frontend development', 'ui development', 'component-based architecture'],
        'spring': ['enterprise java', 'backend development', 'microservices'],
        'django': ['python web development', 'full-stack python', 'backend python'],
        'postgresql': ['sql databases', 'relational databases', 'data modeling'],
        'mongodb': ['nosql', 'document databases', 'schema-less data'],
        'machine learning': ['data science', 'predictive modeling', 'statistical analysis'],
    }
    
    def __init__(self):
        """Initialize analyzer"""
        pass
    
    def analyze_gaps(
        self,
        resume: ParsedResume,
        job_analysis: JobAnalysis
    ) -> SkillsGapReport:
        """
        Comprehensive skills gap analysis
        """
        # Extract user skills
        user_skills = self._extract_user_skills(resume)
        
        # Required skills from job
        required_skills = set([s.lower() for s in job_analysis.key_skills])
        nice_to_have = set([s.lower() for s in job_analysis.nice_to_have_skills])
        
        # Find matches and gaps
        exact_matches = []
        partial_matches = []
        missing_critical = []
        missing_nice = []
        fabrication_candidates = []
        transferrable = []
        reframing_suggestions = {}
        
        for required in required_skills:
            # Check exact match
            if required in user_skills:
                exact_matches.append(required)
            # Check partial/synonym match
            elif self._check_similarity(required, user_skills):
                matched_skill = self._find_similar_skill(required, user_skills)
                partial_matches.append(f"{required} (similar to {matched_skill})")
            else:
                # Check if user has transferrable skill
                transfer = self._find_transferrable_skill(required, user_skills)
                if transfer:
                    transferrable.append(f"{required} can be reframed from {transfer}")
                    reframing_suggestions[required] = transfer
                else:
                    missing_critical.append(required)
                    fabrication_candidates.append(required)
        
        # Check nice-to-have skills
        for nice in nice_to_have:
            if nice not in user_skills and nice not in required_skills:
                missing_nice.append(nice)
        
        return SkillsGapReport(
            exact_matches=exact_matches,
            partial_matches=partial_matches,
            missing_critical=missing_critical,
            missing_nice_to_have=missing_nice,
            fabrication_candidates=fabrication_candidates,
            transferrable_skills=transferrable,
            reframing_suggestions=reframing_suggestions
        )
    
    def _extract_user_skills(self, resume: ParsedResume) -> Set[str]:
        """Extract all skills from resume"""
        skills = set()
        
        if resume.skills:
            skills.update([s.lower() for s in resume.skills.languages_frameworks])
            skills.update([s.lower() for s in resume.skills.tools])
        
        # Extract from experience bullets
        for exp in resume.experience:
            exp_text = ' '.join(exp.bullets + [exp.role]).lower()
            # Add common skills found in text
            for skill in self.SKILL_SYNONYMS.keys():
                if skill in exp_text:
                    skills.add(skill)
        
        return skills
    
    def _check_similarity(self, skill1: str, user_skills: Set[str]) -> bool:
        """Check if skill1 is similar to any user skill"""
        skill1_lower = skill1.lower()
        
        # Direct synonym check
        if skill1_lower in self.SKILL_SYNONYMS:
            synonyms = self.SKILL_SYNONYMS[skill1_lower]
            return any(syn in user_skills for syn in synonyms)
        
        # Reverse check
        for user_skill in user_skills:
            if user_skill in self.SKILL_SYNONYMS:
                if skill1_lower in self.SKILL_SYNONYMS[user_skill]:
                    return True
        
        # Fuzzy match
        for user_skill in user_skills:
            if self._fuzzy_match(skill1_lower, user_skill):
                return True
        
        return False
    
    def _find_similar_skill(self, target: str, user_skills: Set[str]) -> str:
        """Find the most similar user skill to target"""
        target_lower = target.lower()
        
        for user_skill in user_skills:
            if self._fuzzy_match(target_lower, user_skill):
                return user_skill
        
        return list(user_skills)[0] if user_skills else ""
    
    def _fuzzy_match(self, s1: str, s2: str, threshold: float = 0.7) -> bool:
        """Simple fuzzy string matching"""
        # Check if one contains the other
        if s1 in s2 or s2 in s1:
            return True
        
        # Check word overlap
        words1 = set(s1.split())
        words2 = set(s2.split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union)
        return similarity >= threshold
    
    def _find_transferrable_skill(self, required: str, user_skills: Set[str]) -> str:
        """Find a transferrable skill that can be reframed"""
        required_lower = required.lower()
        
        # Check if required has transferrable mappings
        if required_lower in self.TRANSFERRABLE_SKILLS:
            transferrable_options = self.TRANSFERRABLE_SKILLS[required_lower]
            for option in transferrable_options:
                for user_skill in user_skills:
                    if option in user_skill or user_skill in option:
                        return user_skill
        
        # Check reverse mapping
        for user_skill in user_skills:
            if user_skill in self.TRANSFERRABLE_SKILLS:
                if required_lower in self.TRANSFERRABLE_SKILLS[user_skill]:
                    return user_skill
        
        return ""
    
    def get_reframing_strategy(self, missing_skill: str, user_skill: str) -> str:
        """Get strategy for reframing a skill"""
        strategies = {
            'aws': f"Highlight {user_skill} experience and mention AWS-specific implementations",
            'docker': f"Emphasize containerization experience with {user_skill}",
            'kubernetes': f"Show orchestration experience using {user_skill}",
            'react': f"Demonstrate component architecture experience with {user_skill}",
            'spring': f"Show enterprise development experience using {user_skill}",
        }
        
        return strategies.get(missing_skill, f"Connect {user_skill} experience to {missing_skill} concepts")
    
    def prioritize_missing_skills(self, gaps: SkillsGapReport, job_analysis: JobAnalysis) -> List[str]:
        """Prioritize which missing skills to address first"""
        # Priority 1: Critical skills that appear multiple times in JD
        # Priority 2: Skills mentioned in first half of JD
        # Priority 3: Skills related to core job function
        
        prioritized = []
        
        # Add critical missing skills first
        prioritized.extend(gaps.missing_critical)
        
        # Then nice-to-have
        prioritized.extend(gaps.missing_nice_to_have)
        
        return prioritized
