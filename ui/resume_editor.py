"""
Interactive Resume Editor
Allows users to edit generated resumes with custom AI prompts
"""

import streamlit as st
from typing import Optional, List, Dict, Any
from core.models import TailoredResume, Experience
from intelligence.ai_client import MistralAIClient


class ResumeEditor:
    """
    Interactive resume editor with AI assistance
    Users can manually edit or use custom prompts for AI improvements
    """
    
    def __init__(self, resume: TailoredResume, api_key: str):
        self.original_resume = resume
        self.edited_resume = self._copy_resume(resume)
        self.api_key = api_key
        self.ai_client = MistralAIClient(api_key)
        self.changes_history = []
    
    def _copy_resume(self, resume: TailoredResume) -> TailoredResume:
        """Create a copy of the resume for editing"""
        import copy
        return copy.deepcopy(resume)
    
    def render_editor(self) -> Optional[TailoredResume]:
        """
        Render the full resume editor interface
        Returns the edited resume when user clicks 'Finalize'
        """
        st.markdown("## ✏️ Edit Your Resume")
        
        st.info("💡 **Tip:** You can manually edit any section or use the '✨ AI Improve' button with custom prompts to enhance specific bullets.")
        
        # Create two columns: Preview and Editor
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### 📝 Editor")
            self._render_editor_panel()
        
        with col2:
            st.markdown("### 👁️ Live Preview")
            self._render_preview_panel()
        
        # Action buttons at bottom
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("↩️ Reset to Original", use_container_width=True):
                self.edited_resume = self._copy_resume(self.original_resume)
                st.session_state['resume_edits'] = {}
                st.rerun()
        
        with col2:
            if st.button("📊 Check ATS Score", use_container_width=True):
                self._show_ats_score()
        
        with col3:
            if st.button("✅ Finalize Resume", type="primary", use_container_width=True):
                return self.edited_resume
        
        return None
    
    def _render_editor_panel(self):
        """Render the editable sections"""
        # Professional Summary
        with st.expander("Professional Summary", expanded=True):
            new_summary = st.text_area(
                "Edit Summary",
                value=self.edited_resume.summary or "",
                height=100,
                key="edit_summary"
            )
            
            # AI improve button
            ai_prompt = st.text_input(
                "What to improve? (e.g., 'Make more technical')",
                key="ai_prompt_summary",
                placeholder="Enter custom prompt..."
            )
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("✨ AI Improve", key="ai_summary_btn"):
                    if ai_prompt:
                        improved = self._ai_improve_text(
                            self.edited_resume.summary or "",
                            ai_prompt,
                            "professional summary"
                        )
                        self.edited_resume.summary = improved
                        st.session_state['edit_summary'] = improved
                        self._log_change("summary", ai_prompt)
                        st.rerun()
            
            with col2:
                if st.button("💾 Save", key="save_summary"):
                    self.edited_resume.summary = new_summary
                    st.success("Saved!")
        
        # Experience Section
        st.markdown("#### Experience")
        for idx, exp in enumerate(self.edited_resume.experience):
            with st.expander(f"{exp.role} at {exp.company}", expanded=(idx == 0)):
                # Edit bullets
                new_bullets = []
                for bullet_idx, bullet in enumerate(exp.bullets):
                    st.markdown(f"**Bullet {bullet_idx + 1}:**")
                    
                    # Text area for bullet
                    bullet_key = f"bullet_{idx}_{bullet_idx}"
                    new_bullet = st.text_area(
                        f"Edit",
                        value=bullet,
                        height=80,
                        key=bullet_key,
                        label_visibility="collapsed"
                    )
                    new_bullets.append(new_bullet)
                    
                    # AI improve with custom prompt
                    ai_col1, ai_col2 = st.columns([3, 1])
                    with ai_col1:
                        ai_prompt = st.text_input(
                            "Custom prompt (e.g., 'Add metrics', 'Make more concise')",
                            key=f"ai_prompt_{idx}_{bullet_idx}",
                            placeholder="How should I improve this?",
                            label_visibility="collapsed"
                        )
                    
                    with ai_col2:
                        if st.button("✨ AI", key=f"ai_btn_{idx}_{bullet_idx}"):
                            if ai_prompt:
                                improved = self._ai_improve_text(
                                    new_bullet,
                                    ai_prompt,
                                    f"bullet for {exp.role}"
                                )
                                # Update session state to show improved version
                                st.session_state[bullet_key] = improved
                                self._log_change(f"experience[{idx}].bullet[{bullet_idx}]", ai_prompt)
                                st.rerun()
                    
                    st.markdown("---")
                
                # Save bullets back
                exp.bullets = new_bullets
                
                # Add new bullet button
                if st.button("➕ Add Bullet", key=f"add_bullet_{idx}"):
                    exp.bullets.append("• ")
                    st.rerun()
        
        # Skills Section
        with st.expander("Skills"):
            st.markdown("**Languages & Frameworks:**")
            st.write(", ".join(self.edited_resume.skills.languages_frameworks))
            
            st.markdown("**Tools:**")
            st.write(", ".join(self.edited_resume.skills.tools))
    
    def _render_preview_panel(self):
        """Render the live preview"""
        # Name and contact
        st.markdown(f"## {self.edited_resume.basics.name}")
        contact_info = []
        if self.edited_resume.basics.email:
            contact_info.append(self.edited_resume.basics.email)
        if self.edited_resume.basics.phone:
            contact_info.append(self.edited_resume.basics.phone)
        if self.edited_resume.basics.location:
            contact_info.append(self.edited_resume.basics.location)
        
        st.markdown(" | ".join(contact_info))
        st.markdown("---")
        
        # Summary
        if self.edited_resume.summary:
            st.markdown("### Summary")
            st.write(self.edited_resume.summary)
            st.markdown("---")
        
        # Experience
        st.markdown("### Experience")
        for exp in self.edited_resume.experience:
            st.markdown(f"**{exp.role}** at {exp.company}")
            date_range = f"{exp.startDate} - {exp.endDate}"
            st.markdown(f"*{date_range}*")
            
            for bullet in exp.bullets:
                st.markdown(f"• {bullet}")
            
            st.markdown("")
        
        # Skills
        st.markdown("### Skills")
        if self.edited_resume.skills.languages_frameworks:
            st.markdown(f"**Languages & Frameworks:** {', '.join(self.edited_resume.skills.languages_frameworks)}")
        if self.edited_resume.skills.tools:
            st.markdown(f"**Tools:** {', '.join(self.edited_resume.skills.tools)}")
    
    def _ai_improve_text(self, original: str, user_prompt: str, context: str) -> str:
        """
        Call AI to improve text based on user prompt
        
        Args:
            original: Original text to improve
            user_prompt: User's custom prompt (e.g., "Make more technical")
            context: Context of the text (e.g., "bullet for Senior Developer")
        
        Returns:
            Improved text
        """
        try:
            system_prompt = f"""You are a professional resume writer helping improve a resume.

CONTEXT: {context}

ORIGINAL TEXT:
{original}

USER'S REQUEST: {user_prompt}

INSTRUCTIONS:
- Rewrite the text following the user's request
- Use STAR format (Situation, Task, Action, Result) where applicable
- Include specific metrics and quantifiable results
- Use strong action verbs
- Keep it concise (1-2 lines maximum)
- Maintain professional tone
- Only return the improved text, nothing else

IMPROVED TEXT:"""

            response = self.ai_client.generate_content(
                system_prompt,
                temperature=0.3,
                max_tokens=200
            )
            
            # Clean up response
            improved = response.strip()
            if improved.startswith('"') and improved.endswith('"'):
                improved = improved[1:-1]
            
            return improved if improved else original
            
        except Exception as e:
            st.error(f"AI improvement failed: {e}")
            return original
    
    def _log_change(self, field: str, prompt: str):
        """Log a change for history"""
        import datetime
        self.changes_history.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "field": field,
            "prompt": prompt
        })
    
    def _show_ats_score(self):
        """Calculate and show current ATS score"""
        with st.spinner("Calculating ATS score..."):
            from intelligence.ats_scorer import ATSScorer
            
            scorer = ATSScorer(self.api_key)
            
            # Create dummy job analysis for scoring
            from core.models import JobAnalysis, SeniorityLevel, Industry, CompanyType
            job_analysis = JobAnalysis(
                role_title="Software Engineer",
                seniority_level=SeniorityLevel.MID,
                years_experience_required=3,
                key_skills=[],
                nice_to_have_skills=[],
                industry=Industry.TECH,
                company_type=CompanyType.ENTERPRISE,
                role_focus_areas=[],
                missing_from_resume=[],
                match_score=85.0
            )
            
            ats_score = scorer.calculate_ats_score(self.edited_resume, job_analysis)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("ATS Score", f"{ats_score.overall}/100")
            with col2:
                if ats_score.overall >= 90:
                    st.success("Excellent! 🎉")
                elif ats_score.overall >= 80:
                    st.info("Good! 👍")
                else:
                    st.warning("Needs improvement ⚠️")
            
            with st.expander("Score Breakdown"):
                st.write(f"Keywords: {ats_score.keyword_match}%")
                st.write(f"STAR Format: {ats_score.star_compliance}%")
                st.write(f"Quantification: {ats_score.quantification}%")
                st.write(f"Action Verbs: {ats_score.action_verb_strength}%")
