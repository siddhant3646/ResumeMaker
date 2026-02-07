"""
2026 UI/UX Design System - Theme definitions and CSS injection
Modern dark mode optimized for productivity tools
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ColorScheme:
    """2026 Color Palette - Dark Mode Default"""
    # Background Colors
    bg_primary: str = "#0f172a"  # Deep navy
    bg_surface: str = "#1e293b"  # Elevated cards
    bg_surface_highlight: str = "#334155"  # Hover states
    
    # Accent Colors
    accent_primary: str = "#3b82f6"  # Modern blue
    accent_primary_hover: str = "#2563eb"
    accent_secondary: str = "#8b5cf6"  # Vibrant purple
    accent_success: str = "#10b981"  # Emerald
    accent_warning: str = "#f59e0b"  # Amber
    accent_error: str = "#ef4444"  # Red
    
    # Text Colors
    text_primary: str = "#f8fafc"  # Off-white
    text_secondary: str = "#94a3b8"  # Muted gray
    text_tertiary: str = "#64748b"  # Subtle gray
    
    # Gradients
    @property
    def gradient_primary(self) -> str:
        return "linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)"
    
    @property
    def gradient_success(self) -> str:
        return "linear-gradient(135deg, #10b981 0%, #34d399 100%)"
    
    @property
    def gradient_card(self) -> str:
        return "linear-gradient(145deg, rgba(30,41,59,0.9) 0%, rgba(15,23,42,0.9) 100%)"
    
    @property
    def gradient_error(self) -> str:
        return "linear-gradient(90deg, #8b2635 0%, #c0392b 100%)"


class Theme2026:
    """2026 Design System Implementation"""
    
    def __init__(self):
        self.colors = ColorScheme()
        self.typography = {
            "heading": "system-ui, -apple-system, sans-serif",
            "body": "system-ui, -apple-system, sans-serif",
            "mono": "JetBrains Mono, Consolas, monospace"
        }
        self.animation = {
            "duration_micro": "200ms",
            "duration_short": "300ms",
            "duration_medium": "500ms",
            "duration_long": "800ms",
            "easing": "cubic-bezier(0.4, 0, 0.2, 1)",
            "stagger": "50ms"
        }
    
    def get_custom_css(self) -> str:
        """Generate custom CSS for Streamlit"""
        return f"""
        <style>
        /* 2026 Design System - Dark Mode */
        
        /* Main background */
        .stApp {{
            background-color: {self.colors.bg_primary};
        }}
        
        /* Headers */
        h1 {{
            color: {self.colors.text_primary} !important;
            font-family: {self.typography['heading']};
            font-weight: 700;
        }}
        
        h2, h3 {{
            color: {self.colors.text_primary} !important;
            font-family: {self.typography['heading']};
            font-weight: 600;
        }}
        
        /* Body text */
        p, span, label {{
            color: {self.colors.text_secondary};
            font-family: {self.typography['body']};
        }}
        
        /* Cards and containers */
        .stContainer {{
            background: {self.colors.gradient_card};
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }}
        
        /* Buttons */
        .stButton > button {{
            background: {self.colors.gradient_primary};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            transition: all {self.animation['duration_short']} {self.animation['easing']};
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px -5px rgba(59, 130, 246, 0.4);
        }}
        
        /* Form inputs */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {{
            background-color: {self.colors.bg_surface};
            color: {self.colors.text_primary};
            border: 1px solid {self.colors.bg_surface_highlight};
            border-radius: 8px;
        }}
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {{
            border-color: {self.colors.accent_primary};
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }}
        
        /* Progress bar */
        .stProgress > div > div > div {{
            background: {self.colors.gradient_primary};
        }}
        
        /* Sidebar - hide by default or minimize */
        [data-testid="stSidebar"] {{
            background-color: {self.colors.bg_surface};
        }}
        
        /* Expander */
        .streamlit-expanderHeader {{
            background-color: {self.colors.bg_surface};
            color: {self.colors.text_primary};
            border-radius: 8px;
        }}
        
        /* Success/Error/Warning messages */
        .stSuccess {{
            background: rgba(16, 185, 129, 0.1);
            border-left: 4px solid {self.colors.accent_success};
        }}
        
        .stError {{
            background: rgba(239, 68, 68, 0.1);
            border-left: 4px solid {self.colors.accent_error};
        }}
        
        .stWarning {{
            background: rgba(245, 158, 11, 0.1);
            border-left: 4px solid {self.colors.accent_warning};
        }}
        
        /* Scrollbar */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: {self.colors.bg_primary};
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: {self.colors.bg_surface_highlight};
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: {self.colors.accent_primary};
        }}
        
        /* Animations */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        @keyframes slideIn {{
            from {{ transform: translateX(-20px); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        
        .animate-fade-in {{
            animation: fadeIn {self.animation['duration_medium']} {self.animation['easing']} forwards;
        }}
        
        .animate-pulse {{
            animation: pulse 2s {self.animation['easing']} infinite;
        }}
        
        .animate-slide-in {{
            animation: slideIn {self.animation['duration_medium']} {self.animation['easing']} forwards;
        }}
        
        /* Custom progress card */
        .progress-card {{
            background: {self.colors.gradient_card};
            border-radius: 16px;
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        /* Step indicator */
        .step-indicator {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 1rem;
            margin: 2rem 0;
        }}
        
        .step-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: {self.colors.bg_surface_highlight};
            transition: all {self.animation['duration_short']} {self.animation['easing']};
        }}
        
        .step-dot.active {{
            background: {self.colors.accent_primary};
            box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.3);
        }}
        
        .step-dot.completed {{
            background: {self.colors.accent_success};
        }}
        
        /* Info box */
        .info-box {{
            background: rgba(59, 130, 246, 0.1);
            border-left: 4px solid {self.colors.accent_primary};
            padding: 1rem;
            border-radius: 0 8px 8px 0;
            margin: 1rem 0;
        }}
        
        /* Settings panel */
        .settings-panel {{
            background: {self.colors.bg_surface};
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        
        /* Badge */
        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 600;
            background: rgba(59, 130, 246, 0.2);
            color: {self.colors.accent_primary};
            border: 1px solid rgba(59, 130, 246, 0.3);
        }}
        
        /* Metric display */
        .metric {{
            text-align: center;
            padding: 1rem;
        }}
        
        .metric-value {{
            font-size: 2rem;
            font-weight: 700;
            color: {self.colors.accent_primary};
        }}
        
        .metric-label {{
            font-size: 0.875rem;
            color: {self.colors.text_tertiary};
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        </style>
        """
    
    def inject_css(self):
        """Inject CSS into Streamlit"""
        import streamlit as st
        st.markdown(self.get_custom_css(), unsafe_allow_html=True)


# Global theme instance
theme = Theme2026()
