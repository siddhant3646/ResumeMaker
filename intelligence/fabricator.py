"""
FAANG/MAANG Bullet Generation and Experience Fabrication Engine
Generates optimized resume bullets using STAR/XYZ format with realistic metrics
"""

import json
import re
import random
from typing import List, Dict, Optional
from core.models import Experience, Project, SeniorityLevel, Industry, ParsedResume
from intelligence.ai_client import MistralAIClient


class FAANGBulletGenerator:
    """Generate ATS-optimized bullets using FAANG/MAANG standards via Mistral Large 3"""
    
    # Tier 1 Action Verbs (Leadership/Impact)
    TIER_1_VERBS = [
        "Architected", "Spearheaded", "Pioneered", "Orchestrated", "Championed",
        "Directed", "Drove", "Led", "Headed", "Strategized"
    ]
    
    # Tier 2 Action Verbs (Creation/Innovation)
    TIER_2_VERBS = [
        "Engineered", "Designed", "Built", "Implemented", "Developed", "Launched",
        "Created", "Established", "Deployed", "Delivered", "Crafted"
    ]
    
    # Tier 3 Action Verbs (Optimization/Improvement)
    TIER_3_VERBS = [
        "Optimized", "Refactored", "Enhanced", "Streamlined", "Accelerated",
        "Improved", "Upgraded", "Modernized", "Transformed", "Revamped"
    ]
    
    # Realistic FAANG-scale metrics templates
    METRIC_TEMPLATES = {
        'scale': [
            "serving {scale}M+ daily active users",
            "handling {scale}M+ requests per day",
            "processing {scale}TB+ of data daily",
            "supporting {scale}K+ concurrent users",
            "managing {scale}M+ records"
        ],
        'performance': [
            "reduced latency by {pct}% (from {before}ms to {after}ms)",
            "improved throughput by {pct}% ({before} RPS to {after} RPS)",
            "decreased response time by {pct}%",
            "optimized performance by {pct}%",
            "increased efficiency by {pct}%"
        ],
        'reliability': [
            "improved uptime to {pct}%",
            "reduced error rate by {pct}%",
            "achieved {pct}% test coverage",
            "decreased downtime by {pct}%"
        ],
        'business': [
            "saved ${amount}K annually in infrastructure costs",
            "increased revenue by {pct}%",
            "reduced operational costs by {pct}%",
            "accelerated delivery by {time}%"
        ],
        'impact': [
            "adopted by {scale}+ teams across the organization",
            "used by {scale}K+ developers",
            "deployed to {scale}+ production services",
            "impacting {scale}M+ end users"
        ]
    }
    
    # Realistic metric ranges for different seniority levels
    METRIC_RANGES = {
        SeniorityLevel.ENTRY: {
            'scale': (10, 100),
            'pct': (10, 30),
            'amount': (10, 50),
            'time': (10, 25)
        },
        SeniorityLevel.JUNIOR: {
            'scale': (50, 500),
            'pct': (15, 40),
            'amount': (25, 100),
            'time': (15, 35)
        },
        SeniorityLevel.MID: {
            'scale': (100, 1000),
            'pct': (20, 50),
            'amount': (50, 200),
            'time': (20, 40)
        },
        SeniorityLevel.SENIOR: {
            'scale': (500, 5000),
            'pct': (30, 60),
            'amount': (100, 500),
            'time': (25, 50)
        },
        SeniorityLevel.STAFF: {
            'scale': (1000, 10000),
            'pct': (40, 70),
            'amount': (200, 1000),
            'time': (30, 60)
        },
        SeniorityLevel.PRINCIPAL: {
            'scale': (5000, 50000),
            'pct': (50, 80),
            'amount': (500, 5000),
            'time': (40, 70)
        }
    }
    
    # Technical context templates
    TECH_CONTEXTS = {
        'backend': [
            "RESTful APIs", "microservices", "distributed systems", "event-driven architecture",
            "serverless functions", "GraphQL APIs", "gRPC services", "message queues"
        ],
        'frontend': [
            "React components", "Vue.js applications", "Angular modules", "responsive UI",
            "design system", "component library", "single-page applications", "progressive web apps"
        ],
        'devops': [
            "CI/CD pipelines", "container orchestration", "infrastructure as code",
            "monitoring systems", "deployment automation", "cloud infrastructure"
        ],
        'data': [
            "data pipelines", "ETL processes", "real-time analytics", "data warehouse",
            "stream processing", "machine learning models"
        ],
        'mobile': [
            "iOS applications", "Android apps", "cross-platform solutions",
            "mobile SDKs", "React Native apps"
        ]
    }
    
    def __init__(self, api_key: str):
        """Initialize with Mistral AI Client"""
        # Using the provided API key
        self.api_key = api_key
        self.client = MistralAIClient(self.api_key)
        self.available = True
    
    def generate_optimized_bullet(
        self,
        skill: str,
        jd_keywords: List[str],
        user_tech_stack: List[str],
        seniority_level: SeniorityLevel,
        focus_area: str = "backend"
    ) -> str:
        """
        Generate a STAR-formatted bullet with quantified metrics
        Uses AI for generation with structured prompting
        """
        if self.available:
            return self._ai_generate_bullet(skill, jd_keywords, user_tech_stack, seniority_level, focus_area)
        else:
            return self._template_generate_bullet(skill, seniority_level, focus_area)
    
    def _ai_generate_bullet(
        self,
        skill: str,
        jd_keywords: List[str],
        user_tech_stack: List[str],
        seniority_level: SeniorityLevel,
        focus_area: str
    ) -> str:
        """Use AI to generate optimized bullet"""
        
        # Select appropriate verbs based on seniority
        if seniority_level in [SeniorityLevel.SENIOR, SeniorityLevel.STAFF, SeniorityLevel.PRINCIPAL]:
            verb_pool = self.TIER_1_VERBS + self.TIER_2_VERBS[:5]
        elif seniority_level in [SeniorityLevel.MID]:
            verb_pool = self.TIER_2_VERBS + self.TIER_3_VERBS[:5]
        else:
            verb_pool = self.TIER_2_VERBS + self.TIER_3_VERBS
        
        verb = random.choice(verb_pool)
        
        # Get realistic metrics
        metrics = self._generate_realistic_metrics(seniority_level)
        
        prompt = f"""Generate a FAANG-quality resume bullet point following STRICT STAR format.

MANDATORY STAR FORMAT:
- S/T (Situation/Task): Implicit context (max 5 words at start)
- A (Action): Specific technical action YOU took (verb + tech details)
- R (Result): Quantified business impact with SPECIFIC numbers

Context:
- Primary Skill: {skill}
- Seniority: {seniority_level.value}
- Focus Area: {focus_area}
- Start With Action Verb: {verb}
- JD Keywords (MUST include 2-3 of these): {', '.join(jd_keywords[:5])}
- User's Tech Stack: {', '.join(user_tech_stack[:5]) if user_tech_stack else 'N/A'}
- Metrics to embed: {metrics}

STRICT REQUIREMENTS:
1. START with action verb: {verb}
2. MUST include 2-3 keywords from JD: {', '.join(jd_keywords[:3])}
3. MUST have quantified result with SPECIFIC metric (e.g., "reducing latency by 40%", "saving $500K annually", "processing 10M+ requests daily")
4. Structure: [Action Verb] + [Technical What] + [Result with Number]
5. Keep between 20-30 words (one sentence)
6. NO markdown formatting, NO asterisks, NO brackets
7. Be specific about scale (mention team size, user count, or data volume)

EXAMPLE FORMAT:
"{verb} [technical achievement] using [1-2 JD keywords], resulting in [specific numeric improvement]."

Generate ONLY the bullet text:
"""
        
        try:
            response_text = self.client.generate_content(prompt)
            bullet = response_text.strip()
            
            # Clean up the bullet
            bullet = self._clean_bullet(bullet)
            
            # Ensure it has metrics
            if not self._has_metrics(bullet):
                bullet = self._add_metrics_to_bullet(bullet, metrics)
            
            return bullet
            
        except Exception as e:
            print(f"AI generation error: {e}")
            return self._template_generate_bullet(skill, seniority_level, focus_area)
    
    def _template_generate_bullet(self, skill: str, seniority_level: SeniorityLevel, focus_area: str) -> str:
        """Fallback template-based generation"""
        # Select verb
        if seniority_level in [SeniorityLevel.SENIOR, SeniorityLevel.STAFF, SeniorityLevel.PRINCIPAL]:
            verb = random.choice(self.TIER_1_VERBS)
        else:
            verb = random.choice(self.TIER_2_VERBS)
        
        # Get metrics
        metrics = self._generate_realistic_metrics(seniority_level)
        
        # Get tech context
        contexts = self.TECH_CONTEXTS.get(focus_area, self.TECH_CONTEXTS['backend'])
        context = random.choice(contexts)
        
        # Build bullet
        scale_metric = random.choice(self.METRIC_TEMPLATES['scale']).format(**metrics)
        perf_metric = random.choice(self.METRIC_TEMPLATES['performance']).format(**metrics)
        
        bullet = f"{verb} scalable {skill}-based {context} {scale_metric}, {perf_metric}"
        
        return self._clean_bullet(bullet)
    
    def _generate_realistic_metrics(self, seniority_level: SeniorityLevel) -> Dict:
        """Generate realistic metrics based on seniority"""
        ranges = self.METRIC_RANGES.get(seniority_level, self.METRIC_RANGES[SeniorityLevel.MID])
        
        scale = random.randint(*ranges['scale'])
        pct = random.randint(*ranges['pct'])
        amount = random.randint(*ranges['amount'])
        
        # Calculate before/after for performance metrics
        before = random.randint(100, 1000)
        after = int(before * (1 - pct / 100))
        
        return {
            'scale': scale,
            'pct': pct,
            'amount': amount,
            'before': before,
            'after': after,
            'time': random.randint(*ranges['time'])
        }
    
    def _clean_bullet(self, bullet: str) -> str:
        """Clean and format bullet point"""
        # Remove bullet markers
        bullet = re.sub(r'^[\s•\-\*]+', '', bullet)
        
        # Ensure proper capitalization
        bullet = bullet[0].upper() + bullet[1:] if bullet else bullet
        
        # Ensure period at end
        if bullet and not bullet.endswith('.'):
            bullet += '.'
        
        # Limit length
        words = bullet.split()
        if len(words) > 30:
            bullet = ' '.join(words[:30]) + '.'
        
        return bullet.strip()
    
    def _has_metrics(self, bullet: str) -> bool:
        """Check if bullet has quantified metrics"""
        patterns = [
            r'\d+%',  # Percentage
            r'\d+K?',  # Numbers with optional K
            r'\d+M',  # Millions
            r'\$\d+',  # Dollar amounts
            r'\d+ms',  # Milliseconds
            r'\d+RPS',  # Requests per second
        ]
        return any(re.search(pattern, bullet) for pattern in patterns)
    
    def _add_metrics_to_bullet(self, bullet: str, metrics: Dict) -> str:
        """Add metrics to bullet if missing"""
        metric_phrase = random.choice([
            f" improving efficiency by {metrics['pct']}%",
            f" serving {metrics['scale']}K+ users",
            f" reducing latency by {metrics['pct']}%"
        ])
        
        # Insert before period
        if bullet.endswith('.'):
            bullet = bullet[:-1] + metric_phrase + '.'
        else:
            bullet += metric_phrase
        
        return bullet
    
    def apply_xyz_formula(self, bullet: str, context: Dict) -> str:
        """
        Convert bullet to XYZ format:
        Accomplished [X] as measured by [Y], by doing [Z]
        """
        # This is typically applied during the generation phase
        # But can be used to restructure existing bullets
        return bullet
    
    def enhance_existing_bullet(
        self,
        bullet: str,
        seniority_level: SeniorityLevel,
        jd_keywords: List[str]
    ) -> str:
        """
        Enhance an existing bullet with STAR format and JD keywords using AI
        """
        # Check if bullet already has good STAR format with metrics and keywords
        has_metrics = self._has_metrics(bullet)
        keyword_count = sum(1 for kw in jd_keywords if kw.lower() in bullet.lower())
        
        if has_metrics and keyword_count >= 2:
            return bullet  # Already optimized
        
        # Use AI to transform bullet to STAR format with JD keywords
        try:
            prompt = f"""Transform this resume bullet into STRICT STAR format with JD keywords.

ORIGINAL BULLET: {bullet}

MANDATORY REQUIREMENTS:
1. Keep the core achievement/action from the original
2. MUST follow STAR: Action Verb + Technical Achievement + Quantified Result
3. MUST include 2-3 of these JD keywords naturally: {', '.join(jd_keywords[:5])}
4. MUST have specific quantified result (percentage, time, money, scale, users)
5. Start with strong action verb from this list: Architected, Engineered, Spearheaded, Optimized, Implemented, Developed, Designed
6. Keep between 20-30 words (one sentence)
7. NO markdown, NO asterisks, NO brackets
8. Be specific and technical

EXAMPLE TRANSFORMATION:
Before: "Worked on improving the database"
After: "Optimized PostgreSQL database queries using indexing and caching strategies, reducing API latency by 65% for 2M+ daily active users."

Output ONLY the improved bullet, nothing else:
"""
            response = self.client.generate_content(prompt)
            enhanced = response.strip()
            
            # Clean the bullet
            enhanced = self._clean_bullet(enhanced)
            
            # Ensure it has metrics (fallback)
            if not self._has_metrics(enhanced):
                metrics = self._generate_realistic_metrics(seniority_level)
                enhanced = self._add_metrics_to_bullet(enhanced, metrics)
            
            return enhanced
            
        except Exception as e:
            print(f"DEBUG: Bullet enhancement error: {e}")
            # Fallback: Add metrics if missing and strengthen verb
            if not has_metrics:
                metrics = self._generate_realistic_metrics(seniority_level)
                bullet = self._add_metrics_to_bullet(bullet, metrics)
            
            # Strengthen action verb
            for tier_3 in self.TIER_3_VERBS:
                if bullet.lower().startswith(tier_3.lower()):
                    new_verb = random.choice(self.TIER_2_VERBS)
                    bullet = new_verb + bullet[len(tier_3):]
                    break
            
            return self._clean_bullet(bullet)


class ExperienceFabricator:
    """Generate plausible experience to fill gaps via Mistral Large 3"""
    
    def __init__(self, api_key: str, enabled: bool = True):
        self.enabled = enabled
        # Using the provided API key
        self.api_key = api_key
        self.bullet_generator = FAANGBulletGenerator(self.api_key)
    
    def fabricate_experience_entry(
        self,
        skill: str,
        user_context: Dict,
        company_context: Dict,
        seniority_level: SeniorityLevel
    ) -> Experience:
        """
        Generate a plausible experience entry
        Creates realistic company name, role, and achievements
        """
        # Use REAL company name from user context - never create fake companies
        company_name = user_context.get('company_name', 'Current Company')
        
        # Generate role based on existing resume data
        user_roles = user_context.get('existing_roles', ['Software Engineer'])
        base_role = user_roles[0] if user_roles else 'Software Engineer'
        
        # Seniority-appropriate role title
        if seniority_level in [SeniorityLevel.SENIOR, SeniorityLevel.STAFF]:
            role = f"Senior {base_role}"
        elif seniority_level == SeniorityLevel.PRINCIPAL:
            role = f"Principal {base_role}"
        else:
            role = base_role
        
        # Generate realistic bullets (3-5 max)
        bullets = []
        for _ in range(random.randint(3, 5)):
            bullet = self.bullet_generator.generate_optimized_bullet(
                    skill=skill,
                    jd_keywords=company_context.get('jd_keywords', []),
                    user_tech_stack=user_context.get('tech_stack', []),
                    seniority_level=seniority_level,
                    focus_area=company_context.get('focus_area', 'backend')
                )
            bullets.append(bullet)
        
        return Experience(
            company=company_name,  # Use real company name
            role=role,
            startDate="Jan 2020",  # Plausible past dates
            endDate="Dec 2022",
            location=user_context.get('location', 'Remote'),
            bullets=bullets,
            is_fabricated=True  # Mark as fabricated additions
        )
    
    def fabricate_project(
        self,
        required_skills: List[str],
        user_skills: List[str],
        company_type: str
    ) -> Project:
        """Generate a plausible project"""
        # Project name
        project_types = [
            "Platform", "Engine", "Hub", "Framework", "Toolkit",
            "System", "Infrastructure", "Service", "Gateway", "Orchestrator"
        ]
        
        skill = random.choice(required_skills[:3] if required_skills else ["microservices"])
        project_name = f"{skill.title()} {random.choice(project_types)}"
        
        # Tech stack (mix of user skills and required skills)
        stack_skills = list(set(user_skills[:5] + required_skills[:3]))
        tech_stack = ', '.join(stack_skills[:6])
        
        # Description
        descriptions = [
            f"Designed and implemented scalable {skill} architecture handling high-throughput scenarios",
            f"Built distributed {skill} system with focus on reliability and performance",
            f"Developed enterprise-grade {skill} solution adopted across multiple teams"
        ]
        description = random.choice(descriptions)
        
        return Project(
            name=project_name,
            techStack=tech_stack,
            description=description,
            is_fabricated=True
        )
    
    def generate_additional_bullets_for_existing_experience(
        self,
        existing_exp: Experience,
        missing_skills: List[str],
        seniority_level: SeniorityLevel
    ) -> List[str]:
        """Generate additional bullets for existing experience to cover missing skills"""
        new_bullets = []
        
        for skill in missing_skills[:3]:  # Limit to top 3 missing skills
            bullet = self.bullet_generator.generate_optimized_bullet(
                skill=skill,
                jd_keywords=[skill],
                user_tech_stack=[],  # Not needed for enhancement
                seniority_level=seniority_level,
                focus_area="backend"
            )
            new_bullets.append(bullet)
        
        return new_bullets
