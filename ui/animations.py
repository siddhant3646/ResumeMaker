"""
Animation Framework for Backend Operations
Provides smooth, engaging animations for all processing stages
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Callable
import time


@dataclass
class AnimationStage:
    """Defines a single animation stage"""
    icon: str
    title: str
    subtitle: str
    gradient: str = "primary"
    animation_type: str = "pulse"
    show_tips: bool = True


class AnimationManager:
    """Manages animated progress stages for backend operations"""
    
    def __init__(self):
        self.stages = {
            'initializing': AnimationStage(
                icon='🚀',
                title='Initializing AI Engine',
                subtitle='Preparing to craft your perfect resume...',
                gradient='primary',
                animation_type='rocket'
            ),
            'reading_resume': AnimationStage(
                icon='📄',
                title='Reading Your Resume',
                subtitle='Extracting your experience and achievements...',
                gradient='primary',
                animation_type='flip'
            ),
            'analyzing_jd': AnimationStage(
                icon='🔍',
                title='Analyzing Job Description',
                subtitle='Identifying key requirements and keywords...',
                gradient='primary',
                animation_type='search'
            ),
            'detecting_role': AnimationStage(
                icon='🎯',
                title='Detecting Role & Seniority',
                subtitle='Understanding position requirements...',
                gradient='secondary',
                animation_type='target'
            ),
            'analyzing_skills': AnimationStage(
                icon='💡',
                title='Analyzing Skills Gap',
                subtitle='Identifying missing competencies...',
                gradient='secondary',
                animation_type='pulse'
            ),
            'generating': AnimationStage(
                icon='✨',
                title='Crafting Your Resume',
                subtitle='Writing optimized content with FAANG standards...',
                gradient='primary',
                animation_type='magic',
                show_tips=True
            ),
            'amplifying': AnimationStage(
                icon='⚡',
                title='Amplifying Achievements',
                subtitle='Adding quantified metrics and impact...',
                gradient='secondary',
                animation_type='lightning'
            ),
            'optimizing': AnimationStage(
                icon='🎨',
                title='Optimizing for ATS',
                subtitle='Ensuring >90 ATS score with STAR bullets...',
                gradient='secondary',
                animation_type='optimize'
            ),
            'validating': AnimationStage(
                icon='👁️',
                title='AI Vision Validation',
                subtitle='Checking PDF quality and page fill...',
                gradient='warning',
                animation_type='scan'
            ),
            'regenerating': AnimationStage(
                icon='🔄',
                title='Refining Content',
                subtitle='Improving based on validation feedback...',
                gradient='warning',
                animation_type='rotate'
            ),
            'scoring': AnimationStage(
                icon='📊',
                title='Calculating ATS Score',
                subtitle='Validating FAANG/MAANG compliance...',
                gradient='secondary',
                animation_type='chart'
            ),
            'complete': AnimationStage(
                icon='✅',
                title='Resume Ready',
                subtitle='Your optimized resume is ready for download',
                gradient='success',
                animation_type='success'
            ),
            'error': AnimationStage(
                icon='❌',
                title='Generation Error',
                subtitle='An error occurred. Please try again.',
                gradient='error',
                animation_type='shake'
            )
        }
        
        self.tips = [
            "💡 Action verbs like 'Architected' and 'Engineered' make stronger impact",
            "💡 Quantified achievements get 40% more attention from recruiters",
            "💡 ATS systems scan for keywords in the first 1/3 of your resume",
            "💡 Skills matching job description increase interview chances by 3x",
            "💡 Bullet points starting with numbers catch the eye immediately",
            "💡 STAR format (Situation-Task-Action-Result) is FAANG standard",
            "💡 XYZ formula: Accomplished X by Y as measured by Z",
            "💡 Every bullet should have at least one metric",
            "💡 Tier 1 verbs: Architected, Spearheaded, Pioneered, Orchestrated",
            "💡 Google emphasizes algorithms, scale, and system design",
            "💡 Amazon looks for ownership and customer obsession",
            "💡 Meta values move fast, impact, and boldness"
        ]
    
    def get_stage_html(self, stage_key: str, progress: float = 0, 
                      tip_index: int = 0, attempt: int = 0) -> str:
        """Generate HTML for a specific stage"""
        stage = self.stages.get(stage_key, self.stages['initializing'])
        tip = self.tips[tip_index % len(self.tips)] if stage.show_tips else ""
        
        # Gradients based on stage type
        gradients = {
            'primary': 'linear-gradient(135deg, #1e3a5f 0%, #2d5a87 50%, #1e3a5f 100%)',
            'secondary': 'linear-gradient(135deg, #2d5a87 0%, #4a90c2 50%, #2d5a87 100%)',
            'success': 'linear-gradient(90deg, #2d7d46 0%, #4caf50 100%)',
            'warning': 'linear-gradient(135deg, #92400e 0%, #f59e0b 100%)',
            'error': 'linear-gradient(90deg, #8b2635 0%, #c0392b 100%)'
        }
        
        gradient = gradients.get(stage.gradient, gradients['primary'])
        animations = self._get_animation_css(stage.animation_type)
        
        attempt_badge = f'<span style="background:rgba(245,158,11,0.3);padding:4px 12px;border-radius:12px;font-size:12px;margin-left:10px;">Attempt {attempt}</span>' if attempt > 0 else ''
        
        tip_html = f'<div style="background:rgba(255,255,255,0.1);padding:1rem;border-radius:8px;margin-top:1.5rem;border-left:3px solid #4fc3f7;text-align:left;"><div style="color:#81d4fa;font-size:0.9rem;font-style:italic;">{tip}</div></div>' if tip and stage.show_tips else ''
        
        badges_html = '''<div style="margin-top:1.5rem;display:flex;justify-content:center;gap:1rem;flex-wrap:wrap;"><span style="background:rgba(79,195,247,0.2);padding:0.5rem 1rem;border-radius:20px;color:#81d4fa;font-size:0.85rem;border:1px solid rgba(79,195,247,0.3);">🎯 STAR Format</span><span style="background:rgba(79,195,247,0.2);padding:0.5rem 1rem;border-radius:20px;color:#81d4fa;font-size:0.85rem;border:1px solid rgba(79,195,247,0.3);">💡 FAANG Optimized</span><span style="background:rgba(79,195,247,0.2);padding:0.5rem 1rem;border-radius:20px;color:#81d4fa;font-size:0.85rem;border:1px solid rgba(79,195,247,0.3);">📊 ATS >90</span></div>''' if stage_key == 'generating' else ''
        
        html = f'''<div style="text-align:center;padding:2rem;background:{gradient};border-radius:16px;margin:1rem 0;box-shadow:0 8px 32px rgba(0,0,0,0.4);border:1px solid rgba(255,255,255,0.1);"><div style="font-size:3.5rem;margin-bottom:1rem;animation:{stage.animation_type} 2s ease-in-out infinite;display:inline-block;">{stage.icon}</div><div style="color:white;font-size:1.5rem;font-weight:700;margin-bottom:0.5rem;display:flex;align-items:center;justify-content:center;">{stage.title}{attempt_badge}</div><div style="color:#a0c4e8;font-size:1rem;margin-bottom:1.5rem;">{stage.subtitle}</div><div style="display:flex;justify-content:center;gap:8px;margin:1.5rem 0;"><span style="width:10px;height:10px;background:#4fc3f7;border-radius:50%;display:inline-block;animation:bounceDot 1.4s ease-in-out infinite;"></span><span style="width:10px;height:10px;background:#4fc3f7;border-radius:50%;display:inline-block;animation:bounceDot 1.4s ease-in-out 0.2s infinite;"></span><span style="width:10px;height:10px;background:#4fc3f7;border-radius:50%;display:inline-block;animation:bounceDot 1.4s ease-in-out 0.4s infinite;"></span></div>{tip_html}{badges_html}</div><style>@keyframes fadeIn{{from{{opacity:0;transform:translateY(20px);}}to{{opacity:1;transform:translateY(0);}}}} {animations} @keyframes bounceDot{{0%,80%,100%{{transform:scale(0);opacity:0.5;}}40%{{transform:scale(1);opacity:1;}}}}</style>'''
        
        return html
    
    def _get_animation_css(self, animation_type: str) -> str:
        """Get CSS keyframes for specific animation type"""
        animations = {
            'rocket': '''
                @keyframes rocket {{
                    0%, 100% {{ transform: translateY(0) rotate(-5deg); }}
                    25% {{ transform: translateY(-8px) rotate(5deg); }}
                    50% {{ transform: translateY(-15px) rotate(-5deg); }}
                    75% {{ transform: translateY(-8px) rotate(5deg); }}
                }}
            ''',
            'flip': '''
                @keyframes flip {{
                    0%, 100% {{ transform: rotateY(0deg); }}
                    50% {{ transform: rotateY(180deg); }}
                }}
            ''',
            'search': '''
                @keyframes search {{
                    0%, 100% {{ transform: scale(1) rotate(0deg); }}
                    25% {{ transform: scale(1.1) rotate(-10deg); }}
                    75% {{ transform: scale(1.1) rotate(10deg); }}
                }}
            ''',
            'target': '''
                @keyframes target {{
                    0%, 100% {{ transform: scale(1); }}
                    50% {{ transform: scale(1.2); }}
                }}
            ''',
            'pulse': '''
                @keyframes pulse {{
                    0%, 100% {{ transform: scale(1); opacity: 1; }}
                    50% {{ transform: scale(1.1); opacity: 0.8; }}
                }}
            ''',
            'magic': '''
                @keyframes magic {{
                    0%, 100% {{ transform: translateY(0) rotate(-5deg) scale(1); }}
                    25% {{ transform: translateY(-5px) rotate(5deg) scale(1.1); }}
                    50% {{ transform: translateY(0) rotate(-5deg) scale(1); }}
                    75% {{ transform: translateY(-3px) rotate(5deg) scale(1.05); }}
                }}
            ''',
            'lightning': '''
                @keyframes lightning {{
                    0%, 100% {{ transform: scale(1); filter: brightness(1); }}
                    50% {{ transform: scale(1.1); filter: brightness(1.3); }}
                }}
            ''',
            'optimize': '''
                @keyframes optimize {{
                    0%, 100% {{ transform: rotate(0deg); }}
                    25% {{ transform: rotate(90deg); }}
                    50% {{ transform: rotate(180deg); }}
                    75% {{ transform: rotate(270deg); }}
                }}
            ''',
            'scan': '''
                @keyframes scan {{
                    0%, 100% {{ transform: translateX(0); opacity: 1; }}
                    50% {{ transform: translateX(20px); opacity: 0.7; }}
                }}
            ''',
            'rotate': '''
                @keyframes rotate {{
                    from {{ transform: rotate(0deg); }}
                    to {{ transform: rotate(360deg); }}
                }}
            ''',
            'chart': '''
                @keyframes chart {{
                    0%, 100% {{ transform: scaleY(1); }}
                    50% {{ transform: scaleY(1.2); }}
                }}
            ''',
            'success': '''
                @keyframes success {{
                    0% {{ transform: scale(0) rotate(0deg); opacity: 0; }}
                    50% {{ transform: scale(1.2) rotate(180deg); opacity: 1; }}
                    100% {{ transform: scale(1) rotate(360deg); opacity: 1; }}
                }}
            ''',
            'shake': '''
                @keyframes shake {{
                    0%, 100% {{ transform: translateX(0); }}
                    25% {{ transform: translateX(-5px); }}
                    75% {{ transform: translateX(5px); }}
                }}
            '''
        }
        
        return animations.get(animation_type, animations['pulse'])
    
    def get_ats_score_card(self, score: int, details: Dict) -> str:
        """Generate ATS score display card"""
        color = '#10b981' if score >= 90 else '#f59e0b' if score >= 80 else '#ef4444'
        status = 'EXCELLENT' if score >= 90 else 'GOOD' if score >= 80 else 'NEEDS WORK'
        
        metrics = ''.join([
            self._get_metric_row('STAR Format', details.get('star_compliance', 0), color),
            self._get_metric_row('Quantified', details.get('quantification', 0), color),
            self._get_metric_row('Keywords', details.get('keyword_match', 0), color),
            self._get_metric_row('Action Verbs', details.get('action_verbs', 0), color)
        ])
        
        return f'<div style="background:linear-gradient(135deg,rgba(16,185,129,0.1) 0%,rgba(45,90,135,0.1) 100%);border:2px solid {color};border-radius:16px;padding:1.5rem;margin:1rem 0;text-align:center;"><div style="font-size:0.875rem;color:#94a3b8;margin-bottom:0.5rem;">ATS COMPATIBILITY SCORE</div><div style="font-size:4rem;font-weight:800;color:{color};line-height:1;margin-bottom:0.5rem;">{score}</div><div style="font-size:1rem;font-weight:600;color:{color};margin-bottom:1rem;">{status}</div><div style="display:grid;grid-template-columns:repeat(2,1fr);gap:1rem;margin-top:1rem;text-align:left;">{metrics}</div></div>'
    
    def _get_metric_row(self, label: str, value: int, color: str) -> str:
        """Generate metric row for ATS score card"""
        value_color = color if value >= 90 else '#94a3b8'
        return f'<div style="background:rgba(255,255,255,0.05);padding:0.75rem;border-radius:8px;"><div style="font-size:0.75rem;color:#64748b;margin-bottom:0.25rem;">{label}</div><div style="font-size:1.25rem;font-weight:700;color:{value_color};">{value}%</div></div>'


# Global animation manager instance
animation_manager = AnimationManager()
