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
    
    def optimize_for_ats_only(
        self,
        resume: ParsedResume,
        config: GenerationConfig
    ) -> Tuple[TailoredResume, JobAnalysis]:
        """
        Optimize resume for ATS without job description
        Single pass, no regeneration, no new fabricated content
        Target ATS: 90
        """
        from intelligence.ai_client import MistralAIClient
        
        # Create a generic job analysis for ATS optimization
        job_analysis = JobAnalysis(
            role_title="Software Engineer",
            seniority_level="mid",
            years_experience_required=3,
            key_skills=["programming", "software development", "problem solving"],
            nice_to_have_skills=[],
            industry="technology",
            company_type="enterprise",
            role_focus_areas=["backend", "frontend", "full-stack"],
            missing_from_resume=[],
            match_score=85.0
        )
        
        # Generate ATS-optimized content using AI
        client = MistralAIClient(self.api_key)
        
        # Build prompt for ATS-only optimization
        resume_json = resume.json()
        
        prompt = f"""Optimize this resume for ATS compatibility WITHOUT adding new experience:

ORIGINAL RESUME (JSON):
{resume_json}

STRICT RULES:
1. SINGLE PASS - Generate once, no iterations
2. Target ATS Score: 90
3. NO new experience - only improve existing content
4. NO fabricated projects or skills
5. Keep same structure and sections
6. Maintain all original dates, companies, and roles

IMPROVEMENTS TO MAKE:
- Rewrite bullets using STAR format (Situation, Task, Action, Result)
- Add quantification where missing (use realistic estimates if needed)
- Use stronger action verbs
- Optimize keywords for software engineering roles
- Fix grammar and clarity
- Ensure every bullet has metrics

IMPORTANT:
- Keep all existing job entries
- Keep all existing dates
- Only rewrite bullet text
- Make bullets more impactful and measurable

Return the optimized resume in the same JSON format with all fields preserved."""

        # Call AI to optimize
        response = client.generate_content(prompt, temperature=0.2, max_tokens=4096)
        
        # Parse response
        import json
        import re
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                optimized_data = json.loads(json_match.group())
                
                # Create TailoredResume from optimized data
                tailored = TailoredResume(
                    basics=resume.basics,
                    summary=optimized_data.get("summary", resume.summary),
                    education=resume.education,
                    experience=[],
                    skills=resume.skills,
                    projects=resume.projects if config.include_projects else [],
                    achievements=resume.achievements if config.include_achievements else [],
                    fabrication_notes=["ATS-optimized version of original resume (no new content added)"]
                )
                
                # Parse experience from optimized data
                for exp_data in optimized_data.get("experience", []):
                    exp = Experience(
                        company=exp_data.get("company", ""),
                        location=exp_data.get("location", ""),
                        role=exp_data.get("role", ""),
                        startDate=exp_data.get("startDate", ""),
                        endDate=exp_data.get("endDate", ""),
                        bullets=exp_data.get("bullets", []),
                        is_fabricated=False
                    )
                    tailored.experience.append(exp)
                
                # If no experience parsed, use original
                if not tailored.experience:
                    tailored.experience = resume.experience
                
                # Calculate ATS score
                ats_score = self.ats_scorer.calculate_ats_score(tailored, job_analysis)
                tailored.ats_score = ats_score
                
                return tailored, job_analysis
                
        except Exception as e:
            print(f"DEBUG: ATS-only optimization error: {e}")
            # Fallback: return original with basic improvements
            tailored = TailoredResume(
                basics=resume.basics,
                summary=resume.summary,
                education=resume.education,
                experience=resume.experience,
                skills=resume.skills,
                projects=resume.projects if config.include_projects else [],
                achievements=resume.achievements if config.include_achievements else [],
                fabrication_notes=["Error in ATS optimization - using original"]
            )
            
            ats_score = self.ats_scorer.calculate_ats_score(tailored, job_analysis)
            tailored.ats_score = ats_score
            
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
            # FLEXIBLE LIMITS: allow more bullets for initial generation, regeneration adds more if needed
            target_bullets = min(12 if is_most_recent else 8, page_plan.bullets_per_experience.get(exp.company, 10 if is_most_recent else 6))
            
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
            
            # SANITIZE all bullets (remove markdown, brackets, etc.)
            sanitized_bullets = [self._sanitize_bullet(b) for b in enhanced_bullets]
            
            # DEDUPLICATE bullets (keep first occurrence)
            seen_bullets = set()
            unique_bullets = []
            for bullet in sanitized_bullets:
                normalized = bullet.lower().strip()[:50]  # Compare first 50 chars
                if normalized not in seen_bullets:
                    seen_bullets.add(normalized)
                    unique_bullets.append(bullet)
            
            # Create enhanced experience entry
            enhanced_exp = Experience(
                company=exp.company,
                role=exp.role,
                startDate=exp.startDate,
                endDate=exp.endDate,
                location=exp.location,
                bullets=unique_bullets[:target_bullets],  # Limit to target
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
        """Enhance existing bullets with STAR format and metrics (batched - single AI call)"""
        return self.bullet_generator.enhance_bullets_batch(
            bullets=bullets,
            seniority_level=job_analysis.seniority_level,
            jd_keywords=job_analysis.key_skills
        )
    
    def _sanitize_bullet(self, bullet: str) -> str:
        """
        Sanitize a bullet point:
        1. Remove markdown formatting (**bold**, *italic*)
        2. Remove parenthetical text like (Singleton and Factory patterns)
        3. Clean up extra whitespace
        """
        import re
        
        # Remove markdown bold: **text** -> text
        sanitized = re.sub(r'\*\*([^*]+)\*\*', r'\1', bullet)
        
        # Remove markdown italic: *text* -> text
        sanitized = re.sub(r'\*([^*]+)\*', r'\1', sanitized)
        
        # Remove parenthetical content that looks like elaboration
        # e.g., "(Singleton and Factory patterns)" but keep "(10M+ users)"
        # Only remove if > 20 chars inside parens (likely elaboration, not metrics)
        sanitized = re.sub(r'\s*\([^)]{20,}\)', '', sanitized)
        
        # Clean up double spaces
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized
    
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
        """
        Enhance and CLEAN UP skills section:
        1. Add missing JD keywords
        2. Remove duplicates (case-insensitive)
        3. Remove redundant skills (Spring when Spring Boot exists)
        4. Remove filler/basic skills for SDE-2+ level
        """
        from core.models import Skills
        
        # FILLER SKILLS BLOCKLIST - remove these for SDE-2+ roles
        filler_skills = {
            # Agile/Process terms
            'agile methodologies', 'agile', 'scrum', 'kanban',
            # Vague principles
            'maintainability principles', 'maintainability',
            'modular and loosely coupled code', 'loosely coupled', 'loosely coupled systems',
            'code quality practices', 'code quality',
            'maintainability best practices', 'best practices',
            'security fundamentals', 'security best practices', 'security',
            'performance optimization', 'optimization',
            # Basic web (assumed for any dev)
            'html', 'css', 'html5', 'css3',
            # DSA/Fundamentals (assumed at SDE-2 level)
            'time/space complexity analysis', 'complexity analysis', 'time/space complexity',
            'data structures', 'algorithms', 'dsa',
            'oop concepts', 'object-oriented', 'oops', 'oop',
            # Tools category terms (too vague)
            'static analysis tools',
            'profiling tools', 'instrumentation',
            'cloud',  # Too vague when specific providers listed
            'database',  # Too vague
            # Generic filler
            'programming', 'coding',
            'software development', 'software engineering',
            'problem solving', 'analytical skills',
            'team player', 'communication',
            # Architecture buzzwords without specifics
            'design patterns', 'system design patterns', 'solid',
            'modular coding',
            'distributed systems',  # Too vague
            'scalable systems',  # Too vague
            'messaging', 'messaging systems',
            'reliability engineering',
            # Version control (assumed)
            'git', 'github', 'gitlab', 'version control',
            # Java/Spring buzzwords (too vague - keep specific ones)
            'j2ee', 'ioc', 'aop', 'mvc', 'spring (mvc, ioc, aop, security)',
            'spring mvc', 'spring aop', 'spring ioc',
            # Web services buzzwords
            'web-services', 'web-services (json, soap)', 'json, soap',
            'soap', 'xml',  # Legacy protocols
            # IDE/Tools (not skills)
            'eclipse', 'intellij', 'myeclipse', 'eclipse/myeclipse ide',
            # Database generic
            'rdbms', 'rdbms (oracle, postgres)', 'sql',
            # Build tools (keep if specific, remove generic)
            'maven/ant/gradle', 'ant',
        }
        
        # REDUNDANCY MAP - if key exists, remove values
        redundancy_map = {
            'spring boot': ['spring', 'spring framework', 'spring mvc'],
            'react': ['reactjs', 'react.js'],
            'node.js': ['nodejs', 'node'],
            'typescript': ['ts'],
            'javascript': ['js'],
            'kubernetes': ['k8s'],
            'postgresql': ['postgres'],
            'mongodb': ['mongo'],
            'aws': ['amazon web services'],
            'gcp': ['google cloud platform', 'google cloud'],
            'azure': ['microsoft azure'],
        }
        
        def normalize(s: str) -> str:
            return s.lower().strip()
        
        def should_remove(skill: str, all_skills_normalized: set) -> bool:
            norm = normalize(skill)
            
            # Check filler blocklist
            if norm in filler_skills:
                return True
            
            # Check redundancy - if a "parent" skill exists, remove this variant
            for parent, variants in redundancy_map.items():
                if norm in [normalize(v) for v in variants]:
                    if parent in all_skills_normalized:
                        return True
            
            # Check for "(one of these)" type patterns only
            if 'one of' in norm:
                return True
                
            return False
        
        def transform_skill(skill: str) -> str:
            """Transform skill: replace / with , and normalize capitalization"""
            # Known proper capitalizations
            proper_caps = {
                'java': 'Java', 'javascript': 'JavaScript', 'typescript': 'TypeScript',
                'python': 'Python', 'nodejs': 'NodeJS', 'node.js': 'Node.js',
                'reactjs': 'ReactJS', 'react': 'React', 'angular': 'Angular',
                'vue': 'Vue', 'vuejs': 'VueJS', 'nextjs': 'Next.js',
                'spring boot': 'Spring Boot', 'spring': 'Spring', 'hibernate': 'Hibernate',
                'aws': 'AWS', 'gcp': 'GCP', 'azure': 'Azure',
                'docker': 'Docker', 'kubernetes': 'Kubernetes', 'k8s': 'K8s',
                'mongodb': 'MongoDB', 'mysql': 'MySQL', 'postgresql': 'PostgreSQL',
                'redis': 'Redis', 'kafka': 'Kafka', 'rabbitmq': 'RabbitMQ',
                'graphql': 'GraphQL', 'rest': 'REST', 'grpc': 'gRPC',
                'ci/cd': 'CI/CD', 'ci cd': 'CI/CD', 'jenkins': 'Jenkins',
                'terraform': 'Terraform', 'ansible': 'Ansible',
                'jira': 'Jira', 'confluence': 'Confluence', 'gitlab': 'GitLab',
                'github': 'GitHub', 'bitbucket': 'Bitbucket',
                'intellij': 'IntelliJ', 'vscode': 'VSCode',
                'junit': 'JUnit', 'pytest': 'PyTest', 'selenium': 'Selenium',
                'elasticsearch': 'Elasticsearch', 'kibana': 'Kibana', 'grafana': 'Grafana',
                'prometheus': 'Prometheus', 'splunk': 'Splunk', 'datadog': 'Datadog',
                'apache spark': 'Apache Spark', 'apache kafka': 'Apache Kafka',
                'apache flink': 'Apache Flink', 'hadoop': 'Hadoop', 'hive': 'Hive',
                'airflow': 'Airflow', 'mlflow': 'MLflow',
                'nosql': 'NoSQL', 'sql': 'SQL', 'plsql': 'PL/SQL',
                'oauth': 'OAuth', 'jwt': 'JWT', 'saml': 'SAML',
                'solid': 'SOLID', 'oop': 'OOP', 'ddd': 'DDD', 'tdd': 'TDD',
                'api': 'API', 'sdk': 'SDK', 'cli': 'CLI',
                'json': 'JSON', 'xml': 'XML', 'yaml': 'YAML',
                'html': 'HTML', 'css': 'CSS', 'sass': 'SASS', 'less': 'LESS',
                'go': 'Go', 'golang': 'Golang', 'rust': 'Rust', 'kotlin': 'Kotlin',
                'scala': 'Scala', 'c++': 'C++', 'c#': 'C#',
                'fortify': 'Fortify', 'sonarqube': 'SonarQube',
                'maven': 'Maven', 'gradle': 'Gradle', 'npm': 'npm',
                'postman': 'Postman', 'swagger': 'Swagger', 'openapi': 'OpenAPI',
            }
            
            # Replace "/" with ", "
            result = skill.replace('/', ', ') if '/' in skill else skill
            
            # Check for known proper capitalization
            lower = result.lower().strip()
            if lower in proper_caps:
                return proper_caps[lower]
            
            # For unknown skills, use title case
            return result.title()
        
        # Combine all skills for analysis
        all_skills = skills.languages_frameworks + skills.tools
        all_normalized = set(normalize(s) for s in all_skills)
        
        # Step 1: Deduplicate (case-insensitive, keep first occurrence)
        seen = set()
        deduped_langs = []
        for s in skills.languages_frameworks:
            norm = normalize(s)
            if norm not in seen:
                seen.add(norm)
                deduped_langs.append(s)
        
        deduped_tools = []
        for s in skills.tools:
            norm = normalize(s)
            if norm not in seen:
                seen.add(norm)
                deduped_tools.append(s)
        
        # Step 2: Remove filler and redundant skills
        cleaned_langs = [s for s in deduped_langs if not should_remove(s, all_normalized)]
        cleaned_tools = [s for s in deduped_tools if not should_remove(s, all_normalized)]
        
        # Step 2.5: Transform skills (replace / with ,)
        cleaned_langs = [transform_skill(s) for s in cleaned_langs]
        cleaned_tools = [transform_skill(s) for s in cleaned_tools]
        
        # Step 3: Add missing JD keywords (only non-filler ones)
        existing = set(normalize(s) for s in cleaned_langs + cleaned_tools)
        for skill in job_analysis.key_skills:
            norm = normalize(skill)
            if norm not in existing and norm not in filler_skills:
                if norm in ['python', 'java', 'javascript', 'typescript', 'go', 'rust', 'c++', 'c#', 'kotlin', 'scala']:
                    cleaned_langs.append(skill)
                else:
                    cleaned_tools.append(skill)
                existing.add(norm)
        
        print(f"DEBUG: Skills cleanup - Langs: {len(skills.languages_frameworks)} -> {len(cleaned_langs)}, Tools: {len(skills.tools)} -> {len(cleaned_tools)}")
        
        skills.languages_frameworks = cleaned_langs
        skills.tools = cleaned_tools
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
    
    def _clean_skills_section(self, skills: 'Skills', preserve_keywords: set = None) -> 'Skills':
        """
        Clean skills section: remove duplicates and filler.
        Lightweight cleanup for use during regeneration.
        
        Args:
            skills: Skills object to clean
            preserve_keywords: Set of lowercase keywords to NEVER remove (JD-required)
        """
        preserve_keywords = preserve_keywords or set()
        
        # FILLER BLOCKLIST (must match _enhance_skills)
        filler_skills = {
            'agile methodologies', 'agile', 'scrum', 'kanban',
            'solid', 'design patterns', 'system design patterns',
            'git', 'github', 'gitlab', 'version control',
            'j2ee', 'ioc', 'aop', 'mvc', 'spring (mvc, ioc, aop, security)',
            'spring mvc', 'spring aop', 'spring ioc',
            'web-services', 'web-services (json, soap)', 'json, soap', 'soap', 'xml',
            'eclipse', 'intellij', 'myeclipse', 'eclipse/myeclipse ide',
            'rdbms', 'rdbms (oracle, postgres)', 'sql',
            'maven/ant/gradle', 'ant',
            'security', 'security fundamentals', 'security best practices',
            'html', 'css', 'html5', 'css3',
            'oop', 'oops', 'oop concepts', 'object-oriented',
            'data structures', 'algorithms', 'dsa',
        }
        
        def normalize(s: str) -> str:
            return s.lower().strip()
        
        def is_filler(norm: str) -> bool:
            """Check if skill is filler, but preserve JD keywords"""
            if norm in preserve_keywords:
                return False  # Never filter JD-required keywords
            return norm in filler_skills
        
        # Deduplicate and remove filler from languages_frameworks
        seen = set()
        cleaned_langs = []
        for s in skills.languages_frameworks:
            norm = normalize(s)
            if norm not in seen and not is_filler(norm):
                seen.add(norm)
                cleaned_langs.append(s)
        
        # Deduplicate and remove filler from tools
        cleaned_tools = []
        for s in skills.tools:
            norm = normalize(s)
            if norm not in seen and not is_filler(norm):
                seen.add(norm)
                cleaned_tools.append(s)
        
        skills.languages_frameworks = cleaned_langs
        skills.tools = cleaned_tools
        
        print(f"DEBUG: Skills cleanup - {len(cleaned_langs)} langs, {len(cleaned_tools)} tools, preserved {len(preserve_keywords)} JD keywords")
        return skills
    
    def regenerate_with_feedback(
        self,
        previous_resume: TailoredResume,
        original_resume: ParsedResume,
        job_analysis: JobAnalysis,
        ats_feedback: 'ATSScore',
        config: GenerationConfig,
        retry_count: int = 1,
        page_feedback=None,
        force_variation: bool = False
    ) -> TailoredResume:
        """
        Regenerate resume using Mistral's ATS feedback to fix shortcomings.
        """
        print(f"DEBUG: regenerate_with_feedback ENTERED - retry {retry_count}, force_variation={force_variation}")
        
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
        
        # VARIATION: Add creative variation instructions when score is stale
        variation_instructions = ""
        if force_variation:
            import random
            variation_styles = [
                "Use completely different action verbs than before (try: orchestrated, spearheaded, pioneered, revolutionized, transformed, accelerated).",
                "Focus on DIFFERENT metrics than previous attempts (try: cost savings $, time reduction %, user growth #, revenue impact $).",
                "Emphasize a DIFFERENT aspect: leadership/mentoring in some bullets, technical depth in others.",
                "Use higher impact numbers than before (aim for 50%+, $1M+, 10x improvements).",
                "Reframe achievements from a business impact perspective rather than technical tasks.",
            ]
            selected_variations = random.sample(variation_styles, min(3, len(variation_styles)))
            variation_instructions = "\n\nCRITICAL VARIATION REQUIRED (previous attempts produced same results):\n" + "\n".join(f"- {v}" for v in selected_variations)
        
        improvement_prompt = f"""You are an expert resume writer. The previous attempt scored {ats_feedback.overall}/100 with ONLY {ats_feedback.keyword_match}% keyword match.

CRITICAL: KEYWORD DENSITY IS THE #1 PRIORITY. The resume MUST include these MISSING KEYWORDS:
{missing_kw}

JOB: {job_analysis.role_title}
SENIORITY: {job_analysis.seniority_level.value}

CURRENT RESUME CONTENT:
{current_resume_text}

SHORTCOMINGS:
{shortcomings}

WEAK BULLETS TO FIX:
{weak_bullets_text}

INSTRUCTIONS:
1. Generate exactly {bullets_needed} NEW, high-impact achievement bullets.
2. **KEYWORD INTEGRATION IS MANDATORY**: Each bullet MUST contain 2-3 keywords from the MISSING KEYWORDS list above.
3. Distribute ALL missing keywords across your bullets. Do NOT leave any keyword unused.
4. Use the STAR (Situation, Task, Action, Result) format with quantifiable metrics ($, %, #).
5. Ensure the bullets match the seniority level ({job_analysis.seniority_level.value}).
6. Keywords can be used naturally - e.g., "Spring Boot microservices" counts for both "Spring Boot" and "Microservices".
{variation_instructions}

EXAMPLE OF GOOD KEYWORD INTEGRATION:
- Missing keywords: ["Spring Boot", "Microservices", "AWS", "CI/CD"]
- Good bullet: "Architected Spring Boot microservices deployed on AWS with CI/CD pipelines, reducing deployment time by 70%."
- This single bullet naturally integrates ALL 4 missing keywords.

Return valid JSON:
{{
    "improved_bullets": ["bullet 1", "bullet 2", ...],
    "replacement_map": {{"weak bullet text": "replacement bullet text"}}
}}
"""
        
        try:
            improved_bullets = self._call_ai_model_for_improvement(improvement_prompt)
            improved_resume = self._apply_improvements(
                previous_resume, improved_bullets, job_analysis, ats_feedback, page_feedback
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
            "max_tokens": 4096,
            "stream": False
        }
        response = requests.post(url, headers=headers, json=payload, timeout=90)
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
            "max_tokens": 4096,
            "stream": False
        }
        response = requests.post(url, headers=headers, json=payload, timeout=60)
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
        ats_feedback: 'ATSScore',
        page_feedback=None
    ) -> TailoredResume:
        """
        Apply AI-generated improvements to a resume.
        Dynamically adjusts bullet caps based on page fill percentage.
        """
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
        
        # Clean up skills section (remove duplicates and filler, but PRESERVE JD keywords)
        jd_keywords = set(kw.lower() for kw in (ats_feedback.missing_keywords or []))
        if improved.skills:
            improved.skills = self._clean_skills_section(improved.skills, preserve_keywords=jd_keywords)
        
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
            # DYNAMIC CAPS based on page fill - if underfilled, be more generous
            page_fill = page_feedback.fill_percentage if page_feedback else 100
            
            if page_fill < 70:
                # Severely underfilled - allow MANY more bullets
                max_recent = 20
                max_older = 12
                print(f"DEBUG: Page {page_fill}% underfilled - raising caps to {max_recent}/{max_older}")
            elif page_fill < 85:
                # Moderately underfilled - raise caps
                max_recent = 18
                max_older = 10
                print(f"DEBUG: Page {page_fill}% underfilled - raising caps to {max_recent}/{max_older}")
            elif page_fill < 95:
                # Slightly underfilled - standard caps
                max_recent = 15
                max_older = 8
            else:
                # Good fill - strict caps
                max_recent = 12
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
