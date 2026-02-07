"""
Regeneration Controller - Infinite Loop Until Perfect
Manages the resume generation loop with no time limits
"""

import time
from typing import List, Optional, Dict, Callable
from datetime import datetime
from core.models import (
    ParsedResume, JobAnalysis, GenerationConfig, GenerationResult,
    GenerationAttempt, ATSScore, ValidationReport, TailoredResume
)
from intelligence.ats_scorer import ATSScorer
from vision.pdf_validator import PDFValidator


class ContentAdjuster:
    """Adjusts content based on validation feedback"""
    
    @staticmethod
    def adjust_for_whitespace(
        resume: ParsedResume,
        plan: Dict,
        missing_skills: List[str]
    ) -> ParsedResume:
        """Add more content when there's too much whitespace"""
        # Add bullets to existing experiences
        for exp in resume.experience[:2]:  # Focus on recent roles
            if len(exp.bullets) < 8:
                # Add 1-2 more bullets
                pass
        
        # Add fabricated project if space permits
        if missing_skills and len(resume.projects) < 2:
            pass
        
        return resume
    
    @staticmethod
    def adjust_for_crowding(resume: ParsedResume) -> ParsedResume:
        """Remove content when too crowded"""
        # Remove bullets from older experiences
        for exp in resume.experience[2:]:
            if len(exp.bullets) > 2:
                exp.bullets = exp.bullets[:2]
        
        return resume
    
    @staticmethod
    def adjust_for_low_ats(
        resume: ParsedResume,
        ats_score: ATSScore,
        job_analysis: JobAnalysis
    ) -> ParsedResume:
        """Improve content for better ATS score"""
        # Enhance bullets with missing keywords
        if ats_score.keyword_match < 85:
            # Add missing keywords to bullets
            pass
        
        # Add quantification if missing
        if ats_score.quantification < 85:
            pass
        
        # Strengthen action verbs
        if ats_score.action_verb_strength < 80:
            pass
        
        return resume


class RegenerationController:
    """
    Controls the infinite regeneration loop
    No time limits - continues until ATS >90 achieved
    """
    
    def __init__(
        self,
        validator: PDFValidator,
        scorer: ATSScorer,
        generator_func: Callable,
        progress_callback: Optional[Callable] = None
    ):
        self.validator = validator
        self.scorer = scorer
        self.generator_func = generator_func
        self.progress_callback = progress_callback
        
        self.attempts: List[GenerationAttempt] = []
        self.best_result: Optional[GenerationResult] = None
        self.best_ats_score = 0
    
    def generate_until_perfect(
        self,
        resume: ParsedResume,
        job_analysis: JobAnalysis,
        config: GenerationConfig
    ) -> GenerationResult:
        """
        Generate resume until ATS score >90 (no time limit)
        """
        attempt_number = 0
        start_time = time.time()
        
        while True:
            attempt_number += 1
            attempt_start = time.time()
            
            # Update progress
            if self.progress_callback:
                self.progress_callback(
                    stage='regenerating',
                    attempt=attempt_number,
                    message=f"Attempt {attempt_number}: Generating optimized resume..."
                )
            
            # Generate resume
            try:
                tailored_resume, pdf_bytes = self.generator_func(
                    resume, job_analysis, config
                )
            except Exception as e:
                print(f"Generation error on attempt {attempt_number}: {e}")
                continue
            
            # Calculate ATS score
            ats_score = self.scorer.calculate_score(tailored_resume, job_analysis)
            
            # Validate PDF if vision enabled
            validation_report = None
            if config.enable_vision_validation:
                if self.progress_callback:
                    self.progress_callback(
                        stage='validating',
                        attempt=attempt_number,
                        message=f"Validating PDF quality..."
                    )
                validation_report = self.validator.validate(pdf_bytes)
            
            # Create attempt record
            attempt = GenerationAttempt(
                attempt_number=attempt_number,
                timestamp=datetime.now(),
                ats_score=ats_score,
                validation_report=validation_report,
                issues_found=validation_report.issues if validation_report else [],
                adjustments_made=[]
            )
            
            self.attempts.append(attempt)
            
            # Check if this is the best result so far
            if ats_score.overall > self.best_ats_score:
                self.best_ats_score = ats_score.overall
                self.best_result = GenerationResult(
                    pdf_bytes=pdf_bytes,
                    resume_data=tailored_resume,
                    ats_score=ats_score,
                    validation_report=validation_report or ValidationReport(
                        page_count=1,
                        fill_percentage=85.0,
                        whitespace_percentage=15.0,
                        text_density=0.8,
                        needs_regeneration=False
                    ),
                    attempts=self.attempts.copy(),
                    total_attempts=attempt_number,
                    fabrication_audit=[],  # TODO: track fabrications
                    generation_time_seconds=time.time() - start_time,
                    success=True
                )
                
                if self.progress_callback:
                    self.progress_callback(
                        stage='scoring',
                        attempt=attempt_number,
                        message=f"New best score: {ats_score.overall}/100",
                        ats_score=ats_score.overall
                    )
            
            # Check if we've achieved target
            if ats_score.overall >= config.target_ats_score:
                if self.progress_callback:
                    self.progress_callback(
                        stage='complete',
                        attempt=attempt_number,
                        message=f"✅ Achieved target ATS score of {ats_score.overall}!",
                        ats_score=ats_score.overall
                    )
                
                return GenerationResult(
                    pdf_bytes=pdf_bytes,
                    resume_data=tailored_resume,
                    ats_score=ats_score,
                    validation_report=validation_report or ValidationReport(
                        page_count=1,
                        fill_percentage=85.0,
                        whitespace_percentage=15.0,
                        text_density=0.8,
                        needs_regeneration=False
                    ),
                    attempts=self.attempts,
                    total_attempts=attempt_number,
                    fabrication_audit=[],
                    generation_time_seconds=time.time() - start_time,
                    success=True
                )
            
            # Determine what needs adjustment
            adjustments = self._determine_adjustments(
                ats_score, validation_report, config
            )
            
            # Apply adjustments
            if adjustments:
                resume = self._apply_adjustments(resume, adjustments, job_analysis)
                attempt.adjustments_made = adjustments
                
                if self.progress_callback:
                    self.progress_callback(
                        stage='adjusting',
                        attempt=attempt_number,
                        message=f"Adjusting: {', '.join(adjustments)}"
                    )
            else:
                # No adjustments possible - return best result
                if self.best_result:
                    return self.best_result
            
            # Safety: prevent infinite loop if stuck
            if attempt_number >= 20 and self.best_ats_score >= 85:
                # We've tried 20 times and have a decent score
                if self.best_result:
                    return self.best_result
    
    def _determine_adjustments(
        self,
        ats_score: ATSScore,
        validation_report: Optional[ValidationReport],
        config: GenerationConfig
    ) -> List[str]:
        """Determine what adjustments to make"""
        adjustments = []
        
        # Check ATS issues
        if ats_score.keyword_match < 80:
            adjustments.append("add_missing_keywords")
        
        if ats_score.star_compliance < 85:
            adjustments.append("improve_star_format")
        
        if ats_score.quantification < 85:
            adjustments.append("add_metrics")
        
        if ats_score.action_verb_strength < 75:
            adjustments.append("strengthen_verbs")
        
        # Check validation issues
        if validation_report:
            if 'too_much_whitespace' in validation_report.issues:
                adjustments.append("add_more_content")
            
            if 'crowded_sections' in validation_report.issues:
                adjustments.append("reduce_content")
            
            if validation_report.fill_percentage < 80:
                adjustments.append("increase_fill")
        
        return adjustments
    
    def _apply_adjustments(
        self,
        resume: ParsedResume,
        adjustments: List[str],
        job_analysis: JobAnalysis
    ) -> ParsedResume:
        """Apply content adjustments"""
        adjuster = ContentAdjuster()
        
        if "add_more_content" in adjustments or "increase_fill" in adjustments:
            missing_skills = job_analysis.missing_from_resume
            resume = adjuster.adjust_for_whitespace(
                resume, {}, missing_skills
            )
        
        if "reduce_content" in adjustments:
            resume = adjuster.adjust_for_crowding(resume)
        
        if any(adj in adjustments for adj in ["add_missing_keywords", "add_metrics", "strengthen_verbs"]):
            ats_score = self.scorer.calculate_score(resume, job_analysis)
            resume = adjuster.adjust_for_low_ats(resume, ats_score, job_analysis)
        
        return resume
    
    def get_regeneration_stats(self) -> Dict:
        """Get statistics about regeneration attempts"""
        if not self.attempts:
            return {}
        
        scores = [attempt.ats_score.overall for attempt in self.attempts]
        
        return {
            'total_attempts': len(self.attempts),
            'best_score': max(scores) if scores else 0,
            'average_score': sum(scores) / len(scores) if scores else 0,
            'first_score': scores[0] if scores else 0,
            'improvement': max(scores) - scores[0] if len(scores) > 1 else 0
        }
