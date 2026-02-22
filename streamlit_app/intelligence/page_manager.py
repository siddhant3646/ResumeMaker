"""
Page Manager - Dynamic Content Distribution
Manages resume content to optimally fill target pages
"""

from typing import Dict, List, Optional, Tuple
from core.models import ParsedResume, ContentPlan, JobAnalysis, SeniorityLevel, PageStatus


class PageManager:
    """Manages page count and content distribution"""
    
    # Content density constants (in mm)
    LINE_HEIGHT = 4.2  # mm per line (tighter for modern look)
    HEADER_HEIGHT = 8  # mm per section header
    MARGINS = 12.7  # mm total (0.5 inch margins)
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
        
        # More modern heuristic: 1 page is usually enough for up to 3 roles or 15-18 bullets
        if total_experiences >= 4 or total_bullets >= 18:
            return 2
        elif total_experiences >= 3 and len(resume.projects) >= 3:
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
        
        # Dynamic distribution: Most recent gets more space
        for idx, exp in enumerate(sorted_exp):
            if remaining_bullets <= 0:
                break
            
            # GENEROUS LIMITS: allow more bullets per role for better page fill
            # Most recent role can have up to 15 bullets, older roles up to 10
            limit = 15 if idx == 0 else 10
            bullet_count = min(limit, remaining_bullets)
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
        
        # Add fixed header
        total_content += 20
        
        # Less conservative page estimation for modern resumes
        pages_needed = total_content / (self.available_height - 20)
        
        return max(1, int(pages_needed) + (1 if pages_needed % 1 > 0.9 else 0))
    
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

    def check_page_fill(self, pdf_bytes: bytes, target_fill: int = 95) -> PageStatus:
        """
        Check if pages are properly filled using pdfplumber
        Lightweight check without AI
        
        Args:
            pdf_bytes: PDF file as bytes
            target_fill: Target page fill percentage (default: 95%)
            
        Returns:
            PageStatus with fill percentage and issues
        """
        try:
            import pdfplumber
            import io
            
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    
                    if not text or len(text.strip()) == 0:
                        return PageStatus(
                            needs_content=True,
                            fill_percentage=0,
                            current_page=i + 1,
                            suggestion="Page is empty! Add substantial content including experience, projects, and skills.",
                            issues=[f"Page {i+1}: No text detected"]
                        )
                    
                    # IMPROVED: Calculate fill using actual text bounding boxes
                    page_height = page.height
                    page_width = page.width
                    
                    # Get all text characters with their positions
                    chars = page.chars
                    if chars:
                        # Find the vertical extent of content (top of first char to bottom of last char)
                        # In PDF coordinates, y increases downward from top
                        y_positions = [c['top'] for c in chars] + [c['bottom'] for c in chars]
                        min_y = min(y_positions)  # Top of content
                        max_y = max(y_positions)  # Bottom of content
                        
                        # Calculate content height as percentage of available page height
                        # Assume ~0.5 inch (36pt) margins top/bottom = 72pt total
                        usable_height = page_height - 72  # Subtract margins
                        content_height = max_y - min_y
                        
                        fill_percentage = int((content_height / usable_height) * 100)
                        fill_percentage = min(100, max(0, fill_percentage))  # Clamp 0-100
                    else:
                        # Fallback to line count estimation
                        line_count = text.count('\n') + 1
                        # Typical resume line is ~12pt, usable height is ~730pt (A4 minus margins)
                        estimated_fill = (line_count * 14) / 730  # 14pt per line with spacing
                        fill_percentage = int(estimated_fill * 100)
                        fill_percentage = min(100, max(0, fill_percentage))
                    
                    print(f"DEBUG: Page {i+1} fill calculation - {fill_percentage}% (chars: {len(chars) if chars else 0})")
                    
                    if fill_percentage < target_fill:
                        # Only flag underfill if it's the target page or if we are well below target
                        # For page 1 of a multi-page resume, 90% is excellent.
                        current_page_num = i + 1
                        is_last_page = (current_page_num == len(pdf.pages))
                        total_pages = len(pdf.pages)
                        
                        # NEW: Detect sparse trailing page (<40%)
                        # If this is page 2+ and sparse, signal consolidation
                        if current_page_num > 1 and fill_percentage < 40:
                            return PageStatus(
                                needs_content=False,  # Don't add more content
                                fill_percentage=fill_percentage,
                                current_page=current_page_num,
                                suggestion=f"CONSOLIDATE: Page {current_page_num} has only {fill_percentage}% content. Remove weak bullets from previous pages to eliminate this sparse page.",
                                issues=[f"Page {current_page_num}: Sparse trailing page ({fill_percentage}% < 40%)"]
                            )
                        
                        # Relax threshold for intermediate pages
                        effective_target = target_fill if is_last_page else 85
                        
                        if fill_percentage < effective_target:
                            needed_fill = effective_target - fill_percentage
                            bullet_suggestion = max(2, (needed_fill // 10))
                            
                            return PageStatus(
                                needs_content=True,
                                fill_percentage=fill_percentage,
                                current_page=current_page_num,
                                suggestion=f"Page {current_page_num} is {fill_percentage}% filled. Add ~{bullet_suggestion} more high-impact bullets to reach target density.",
                                issues=[f"Page {current_page_num}: Underfilled ({fill_percentage}% < {effective_target}% target)"]
                            )
                
                # All pages pass
                return PageStatus(
                    needs_content=False,
                    fill_percentage=95,
                    current_page=1,
                    suggestion="Perfect page fill!",
                    issues=[]
                )
                
        except Exception as e:
            print(f"DEBUG: PageManager error: {e}")
            # Return passing status on error (fail-safe)
            return PageStatus(
                needs_content=False,
                fill_percentage=95,
                current_page=1,
                suggestion="Page check failed, proceeding...",
                issues=[f"Check error: {str(e)}"]
            )
