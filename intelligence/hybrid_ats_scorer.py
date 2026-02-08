"""
Hybrid ATS Scorer - Combines AI and Rule-Based Scoring
Provides reliable, consistent scoring by leveraging both approaches
"""

import time
from typing import Dict, List, Optional, Tuple
from core.models import ATSScore, ParsedResume, JobAnalysis
from intelligence.ats_scorer import ATSScorer
from intelligence.alternative_ats_scorer import AlternativeATSScorer


class HybridATSScorer:
    """
    Hybrid scoring system that combines AI-based evaluation with rule-based scoring
    Provides consistent, reliable ATS scores by averaging or intelligently selecting
    between the two scoring methods
    """
    
    def __init__(self, api_key: str):
        self.ai_scorer = ATSScorer(api_key)
        self.rule_scorer = AlternativeATSScorer()
        self.debug_mode = True
        self.score_history = []  # Track score progression
    
    def calculate_score(
        self, 
        resume: ParsedResume, 
        job_analysis: JobAnalysis,
        retry_count: int = 0
    ) -> ATSScore:
        """
        Calculate ATS score using hybrid approach
        Accepts both ParsedResume and TailoredResume
        - Gets AI score and rule-based score
        - Averages them if close
        - Uses rule-based score if AI is too conservative
        - Provides detailed debugging
        """
        start_time = time.time()
        
        # Get both scores
        ai_score, ai_time = self._get_ai_score(resume, job_analysis)
        rule_score, rule_time = self._get_rule_score(resume, job_analysis)
        
        # DEBUG: Log both scores
        if self.debug_mode:
            print(f"DEBUG: Hybrid Scoring:")
            print(f"  - AI Score: {ai_score.overall} (took {ai_time:.2f}s)")
            print(f"  - Rule Score: {rule_score.overall} (took {rule_time:.2f}s)")
        
        # Determine final score using hybrid logic
        final_score = self._combine_scores(ai_score, rule_score, retry_count)
        
        # Calculate improvement potential
        improvement = self._calculate_improvement_potential(ai_score, rule_score, final_score)
        
        # Build final ATSScore with hybrid data
        hybrid_score = ATSScore(
            overall=final_score,
            keyword_match=self._combine_component(
                ai_score.keyword_match, 
                rule_score.keyword_match,
                final_score
            ),
            quantification=self._combine_component(
                ai_score.quantification, 
                rule_score.quantification,
                final_score
            ),
            star_compliance=self._combine_component(
                ai_score.star_compliance, 
                rule_score.star_compliance,
                final_score
            ),
            action_verb_strength=self._combine_component(
                ai_score.action_verb_strength, 
                rule_score.action_verb_strength,
                final_score
            ),
            format_compliance=self._combine_component(
                ai_score.format_compliance, 
                rule_score.format_compliance,
                final_score
            ),
            section_completeness=self._combine_component(
                ai_score.section_completeness, 
                rule_score.section_completeness,
                final_score
            ),
            suggestions=self._combine_suggestions(ai_score, rule_score, improvement),
            shortcomings=self._combine_shortcomings(ai_score, rule_score),
            missing_keywords=rule_score.missing_keywords,  # Trust rule-based for missing keywords
            weak_bullets=ai_score.weak_bullets or rule_score.weak_bullets
        )
        
        # Track history
        self.score_history.append({
            'score': final_score,
            'ai_score': ai_score.overall,
            'rule_score': rule_score.overall,
            'retry': retry_count,
            'time': time.time() - start_time
        })
        
        # DEBUG: Log final score
        if self.debug_mode:
            print(f"DEBUG: Hybrid Final Score: {final_score}")
            print(f"DEBUG: Improvement Potential: {improvement}")
            print(f"DEBUG: Total time: {time.time() - start_time:.2f}s")
        
        return hybrid_score
    
    def _get_ai_score(
        self, 
        resume: ParsedResume, 
        job_analysis: JobAnalysis
    ) -> Tuple[ATSScore, float]:
        """Get AI-based score from Mistral"""
        start = time.time()
        try:
            score = self.ai_scorer.calculate_score(resume, job_analysis)
            return score, time.time() - start
        except Exception as e:
            print(f"DEBUG: AI scoring failed: {e}")
            # Return a default score if AI fails
            return self._get_fallback_score(resume, job_analysis), 0
    
    def _get_rule_score(
        self, 
        resume: ParsedResume, 
        job_analysis: JobAnalysis
    ) -> Tuple[ATSScore, float]:
        """Get rule-based score"""
        start = time.time()
        score = self.rule_scorer.calculate_score(resume, job_analysis)
        return score, time.time() - start
    
    def _get_fallback_score(
        self, 
        resume: ParsedResume, 
        job_analysis: JobAnalysis
    ) -> ATSScore:
        """Get fallback score when AI fails"""
        return self.rule_scorer.calculate_score(resume, job_analysis)
    
    def _combine_scores(
        self, 
        ai_score: ATSScore, 
        rule_score: ATSScore,
        retry_count: int = 0
    ) -> int:
        """
        Combine AI and rule scores intelligently
        - If scores are close (<10 pts apart): average them
        - If AI is too conservative (<85) and rule is higher (>=90): trust rule
        - Otherwise: use AI score
        """
        ai_overall = ai_score.overall
        rule_overall = rule_score.overall
        
        # If scores are close, average them
        if abs(ai_overall - rule_overall) < 10:
            final = int((ai_overall + rule_overall) / 2)
            if self.debug_mode:
                print(f"DEBUG: Averaging scores: ({ai_overall} + {rule_overall}) / 2 = {final}")
            return final
        
        # If AI is conservative and rule is confident, trust rule
        if ai_overall < 85 and rule_overall >= 90:
            # Boost the score based on retry count
            boost = min(5, retry_count * 2)  # Up to +10 boost over retries
            final = min(95, rule_overall + boost)
            if self.debug_mode:
                print(f"DEBUG: Rule-based boost: {rule_overall} + {boost} = {final}")
            return final
        
        # If rule is much lower than AI, trust AI (conservative)
        if rule_overall < ai_overall - 15:
            if self.debug_mode:
                print(f"DEBUG: Trusting AI (conservative): {ai_overall}")
            return ai_overall
        
        # Default: trust AI score
        if self.debug_mode:
            print(f"DEBUG: Using AI score: {ai_overall}")
        return ai_overall
    
    def _combine_component(
        self, 
        ai_component: int, 
        rule_component: int,
        final_overall: int
    ) -> int:
        """Combine individual components intelligently"""
        # If components are close
        if abs(ai_component - rule_component) < 15:
            return int((ai_component + rule_component) / 2)
        
        # Weight towards the one that makes sense
        if ai_component < rule_component:
            # Rule is more generous
            return max(ai_component, int(final_overall * 0.9))
        else:
            # AI is more generous
            return max(rule_component, int(final_overall * 0.9))
    
    def _combine_suggestions(
        self, 
        ai_score: ATSScore, 
        rule_score: ATSScore,
        improvement: int
    ) -> List[str]:
        """Combine suggestions from both scorers"""
        suggestions = []
        
        # Add improvement-focused suggestions
        if improvement > 10:
            suggestions.append(f"🎯 Great potential for improvement (+{improvement} points possible!)")
        elif improvement > 5:
            suggestions.append(f"📈 Moderate improvement opportunity (+{improvement} points)")
        else:
            suggestions.append("✨ Already near-optimal. Minor tweaks only.")
        
        # Add top suggestions from both
        all_suggestions = (ai_score.suggestions or []) + (rule_score.suggestions or [])
        for suggestion in all_suggestions[:4]:
            if suggestion not in suggestions:
                suggestions.append(suggestion)
        
        return suggestions[:5]
    
    def _combine_shortcomings(
        self, 
        ai_score: ATSScore, 
        rule_score: ATSScore
    ) -> List[str]:
        """Combine shortcomings from both scorers"""
        shortcomings = []
        
        # Prioritize specific, actionable shortcomings
        ai_shortcomings = ai_score.shortcomings or []
        rule_shortcomings = rule_score.shortcomings or []
        
        for sc in ai_shortcomings:
            if 'Missing' in sc or 'Quantify' in sc or 'STAR' in sc or 'Action' in sc:
                shortcomings.append(sc)
                break
        
        for sc in rule_shortcomings:
            if sc not in shortcomings:
                shortcomings.append(sc)
                break
        
        return shortcomings[:5]
    
    def _calculate_improvement_potential(
        self, 
        ai_score: ATSScore, 
        rule_score: ATSScore,
        final_score: int
    ) -> int:
        """Calculate potential for score improvement"""
        # Estimate maximum possible score
        max_possible = 100
        
        # Calculate gap
        gap = max_possible - final_score
        
        # Weight by retry count (more retries = less potential)
        retry_penalty = min(5, gap // 2)
        
        potential = gap - retry_penalty
        return max(0, min(15, potential))  # Cap at 15 points improvement potential
    
    def get_score_progression(self) -> List[Dict]:
        """Get the history of score changes"""
        return self.score_history
    
    def reset_history(self):
        """Reset score history"""
        self.score_history = []


# Export the scorer
hybrid_ats_scorer = None

def get_hybrid_scorer(api_key: str) -> HybridATSScorer:
    """Get or create the hybrid scorer instance"""
    global hybrid_ats_scorer
    if hybrid_ats_scorer is None:
        hybrid_ats_scorer = HybridATSScorer(api_key)
    return hybrid_ats_scorer
