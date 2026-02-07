"""
Page Manager - Dynamic Content Distribution
Manages resume content to optimally fill target pages
"""

from typing import Dict, List, Optional, Tuple
from core.models import ParsedResume, ContentPlan, JobAnalysis, SeniorityLevel


class PageManager:
    """Manages page count and content distribution"""
    
    # Content density constants (in mm)
    LINE_HEIGHT = 4.8  # mm per line
    HEADER_HEIGHT = 10  # mm per section header
    MARGINS = 15  # mm total (top + bottom)
    PAGE_HEIGHT = 297  # A4 height in mm
    PAGE_WIDTH = 210  # A4 width in mm
    
    def __init__(self, target_pages: Optional[int] = None):
        """
        Initialize page manager
        target_pages: None = optimize mode, 1 or 2 = force specific page count
        """
        self.target_pages = target_pages
        self.available_height = self.PAGE_HEIGHT - (self.MARGINS * 2)
    
    def calculate_optimal_content(
        self,
        resume: ParsedResume,
        job_analysis: JobAnalysis,
        fabrication_enabled: bool = True
    ) -> ContentPlan:
        """
        Calculate optimal content distribution across pages
        Returns a plan for how many bullets, which sections to include
        """
        # Determine target pages
        if self.target_pages is None:
            # Optimize mode: determine based on experience depth
            target = self._determine_optimal_pages(resume)
        else:
            target = self.target_pages
        
        # Calculate available space
        total_available = target * self.available_height
        
        # Subtract fixed sections (header, contact info)
        fixed_height = 25  # mm for header + contact
        available_for_content = total_available - fixed_height
        
        # Calculate bullets needed to fill pages
        avg_bullet_lines = 2.5  # Average lines per bullet
        bullet_height = avg_bullet_lines * self.LINE_HEIGHT
        
        # Estimate section headers
        num_sections = self._count_sections(resume)
        headers_height = num_sections * self.HEADER_HEIGHT
        
        # Calculate how many bullets fit
        remaining_space = available_for_content - headers_height
        max_bullets = int(remaining_space / bullet_height)
        
        # Distribute bullets across experiences
        bullets_per_exp = self._distribute_bullets(
            resume, max_bullets, job_analysis
        )
        
        # Determine which sections to include
        include_summary = target >= 2 and len(resume.experience) > 0
        include_projects = len(resume.projects) > 0 or fabrication_enabled
        include_achievements = len(resume.achievements) > 0
        
        # Prioritize sections
        sections_priority = ['experience', 'skills', 'education']
        if include_projects:
            sections_priority.append('projects')
        if include_achievements:
            sections_priority.append('achievements')
        if include_summary:
            sections_priority.insert(0, 'summary')
        
        return ContentPlan(
            target_pages=target,
            total_bullets=sum(bullets_per_exp.values()),
            bullets_per_experience=bullets_per_exp,
            include_summary=include_summary,
            include_projects=include_projects,
            include_achievements=include_achievements,
            sections_priority=sections_priority
        )
    
    def _determine_optimal_pages(self, resume: ParsedResume) -> int:
        """Determine optimal page count based on experience depth"""
        # Count total experience years/bullets
        total_experiences = len(resume.experience)
        total_bullets = sum(len(exp.bullets) for exp in resume.experience)
        
        # Simple heuristic
        if total_experiences >= 3 or total_bullets >= 12:
            return 2
        elif total_experiences >= 2 and len(resume.projects) >= 2:
            return 2
        else:
            return 1
    
    def _count_sections(self, resume: ParsedResume) -> int:
        """Count number of sections in resume"""
        count = 0
        
        if resume.summary:
            count += 1
        if resume.experience:
            count += 1
        if resume.skills and (resume.skills.languages_frameworks or resume.skills.tools):
            count += 1
        if resume.education:
            count += 1
        if resume.projects:
            count += 1
        if resume.achievements:
            count += 1
        
        return count
    
    def _distribute_bullets(
        self,
        resume: ParsedResume,
        max_bullets: int,
        job_analysis: JobAnalysis
    ) -> Dict[str, int]:
        """
        Distribute bullets across experiences
        Most recent gets more, older gets fewer
        """
        if not resume.experience:
            return {}
        
        # Sort by date (most recent first) - already sorted in resume
        sorted_exp = sorted(
            resume.experience,
            key=lambda x: x.startDate,
            reverse=True
        )
        
        distribution = {}
        remaining_bullets = max_bullets
        
        # Fixed distribution: Maximum 3 bullets per company for ATS readability
        for exp in sorted_exp:
            if remaining_bullets <= 0:
                break
            
            # Cap at 3 bullets per company (optimized for ATS parsing)
            bullet_count = min(3, remaining_bullets)
            distribution[exp.company] = bullet_count
            remaining_bullets -= bullet_count
        
        return distribution
    
    def estimate_page_count(
        self,
        bullets: int,
        sections: List[str],
        include_summary: bool = False
    ) -> int:
        """
        Estimate page count based on content
        """
        # Calculate heights (conservative ATS optimization)
        avg_bullet_lines = 2.5
        bullet_height = bullets * avg_bullet_lines * self.LINE_HEIGHT
        
        header_height = len(sections) * self.HEADER_HEIGHT
        summary_height = 10 if include_summary else 0  # Conservative spacing
        
        total_content = bullet_height + header_height + summary_height
        
        # Add fixed header with more padding
        total_content += 25
        
        # Conservative page estimation with extra padding
        pages_needed = total_content / (self.available_height - 80)  # More conservative spacing
        
        return max(1, int(pages_needed) + (1 if pages_needed % 1 > 0.8 else 0))
    
    def estimate_content_density(
        self,
        pdf_bytes: bytes
    ) -> Dict[str, float]:
        """
        Estimate content density from generated PDF
        Returns fill percentage and whitespace metrics
        """
        # This would be called after PDF generation
        # For now, return placeholder
        return {
            'fill_percentage': 0.0,
            'whitespace_percentage': 0.0,
            'text_density': 0.0
        }
    
    def adjust_for_density(
        self,
        current_plan: ContentPlan,
        density: float,
        target_density: float = 0.90
    ) -> ContentPlan:
        """
        Adjust content plan based on actual density
        If too sparse, add more bullets
        If too dense, remove bullets
        """
        adjusted = ContentPlan(
            target_pages=current_plan.target_pages,
            total_bullets=current_plan.total_bullets,
            bullets_per_experience=current_plan.bullets_per_experience.copy(),
            include_summary=current_plan.include_summary,
            include_projects=current_plan.include_projects,
            include_achievements=current_plan.include_achievements,
            sections_priority=current_plan.sections_priority.copy()
        )
        
        if density < target_density - 0.10:
            # Too sparse - add more bullets
            for company in adjusted.bullets_per_experience:
                adjusted.bullets_per_experience[company] += 1
            adjusted.total_bullets = sum(adjusted.bullets_per_experience.values())
            
        elif density > target_density + 0.05:
            # Too dense - remove bullets from older roles
            for company in list(adjusted.bullets_per_experience.keys())[2:]:
                if adjusted.bullets_per_experience[company] > 1:
                    adjusted.bullets_per_experience[company] -= 1
            adjusted.total_bullets = sum(adjusted.bullets_per_experience.values())
        
        return adjusted
    
    def get_bullet_target_for_role(
        self,
        company: str,
        plan: ContentPlan,
        is_most_recent: bool = False
    ) -> int:
        """Get target bullet count for a specific role"""
        return plan.bullets_per_experience.get(company, 3 if is_most_recent else 1)
    
    def should_include_section(
        self,
        section: str,
        plan: ContentPlan,
        available_space: float
    ) -> bool:
        """Determine if a section should be included based on space"""
        if section == 'summary' and not plan.include_summary:
            return False
        if section == 'projects' and not plan.include_projects:
            return False
        if section == 'achievements' and not plan.include_achievements:
            return False
        
        # Check if there's enough space
        section_height = 20 if section != 'summary' else 15
        return available_space >= section_height
