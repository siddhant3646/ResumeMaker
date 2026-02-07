"""
Professional ATS-Optimized Design System
Clean, readable interface optimized for resume generation and ATS compliance
"""

from dataclasses import dataclass


@dataclass
class ProfessionalTheme:
    """
    Clean, ATS-optimized design system
    Features: White background, black borders, professional colors, minimal effects
    """
    
    # Base Colors - Professional white theme
    bg_white: str = "#ffffff"  # Pure white
    bg_light_gray: str = "#f8fafc"  # Very light gray
    bg_card: str = "#ffffff"  # White cards
    
    # Professional Colors
    text_primary: str = "#1f2937"  # Dark professional text
    text_secondary: str = "#64748b"  # Muted gray
    text_muted: str = "#9ca3af"   # Light gray
    
    # Accent Colors - Professional blue
    accent_blue: str = "#2563eb"  # Professional blue
    accent_light_blue: str = "#dbeafe"  # Light blue
    border_color: str = "#1f2937"  # Professional border
    
    # Status Colors
    success_green: str = "#16a34a"  # Professional green
    warning_orange: str = "#f59e0b"  # Professional orange
    
    # Clean Effects - Minimal shadows and borders
    shadow_subtle: str = "0 2px 8px rgba(0, 0, 0, 0.1)"
    shadow_card: str = "0 4px 16px rgba(0, 0, 0, 0.08)"
    shadow_hover: str = "0 6px 20px rgba(37, 99, 235, 0.15)"


def get_professional_css() -> str:
    """Generate clean, ATS-friendly CSS"""
    theme = ProfessionalTheme()
    
    return f"""
    <style>
    /* ===== RESET & BASE ===== */
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
        font-family: 'Georgia', 'Times New Roman', serif;
    }}
    
    /* ===== BODY ===== */
    .stApp {{
        background: {theme.bg_white};
        color: {theme.text_primary};
        min-height: 100vh;
    }}
    
    /* ===== CLEAN CARDS ===== */
    .clean-card {{
        background: {theme.bg_card};
        border: 2px solid {theme.border_color};
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: {theme.shadow_card};
        transition: all 0.2s ease;
    }}
    
    .clean-card:hover {{
        transform: translateY(-2px);
        box-shadow: {theme.shadow_hover};
        border-color: {theme.accent_blue};
    }}
    
    /* ===== PROFESSIONAL BUTTONS ===== */
    .stButton > button {{
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-family: inherit !important;
        transition: all 0.2s ease !important;
        box-shadow: {theme.shadow_subtle};
    }}
    
    .stButton > button:hover {{
        transform: translateY(-1px) !important;
        box-shadow: {theme.shadow_hover} !important;
    }}
    
    /* ===== ATS SCORE DISPLAY ===== */
    .ats-score-display {{
        background: {theme.bg_light_gray};
        border: 2px solid {theme.border_color};
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }}
    
    .ats-score-value {{
        font-size: 3rem;
        font-weight: 800;
        color: {theme.text_primary};
        margin-bottom: 0.5rem;
    }}
    
    /* ===== CLEAN INPUTS ===== */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        background: {theme.bg_white} !important;
        border: 2px solid {theme.border_color} !important;
        border-radius: 6px !important;
        padding: 1rem !important;
        font-family: inherit !important;
        transition: border-color 0.2s ease !important;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: {theme.accent_blue} !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
        outline: none !important;
    }}
    
    /* ===== UPLOAD AREA ===== */
    .upload-zone {{
        background: {theme.bg_light_gray};
        border: 2px dashed {theme.text_muted};
        border-radius: 8px;
        padding: 3rem;
        text-align: center;
        transition: all 0.2s ease;
    }}
    
    .upload-zone:hover {{
        border-color: {theme.accent_blue};
        background: {theme.accent_light_blue};
    }}
    
    /* ===== PROGRESS BARS ===== */
    .stProgress > div > div > div {{
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%) !important;
        border-radius: 4px !important;
    }}
    
    /* ===== CLEAN SCROLLBAR ===== */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: {theme.bg_light_gray};
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: {theme.text_muted};
        border-radius: 4px;
    }}
    
    /* ===== REMOVE FANCY EFFECTS ===== */
    .blob, .aurora, .floating-particle {{
        display: none !important;
    }}
    
    /* ===== HIDE STREAMLIT BRANDING ===== */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* ===== MAIN CONTENT Z-INDEX FIX ===== */
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"],
    .main .block-container,
    .stApp > div {{
        position: relative;
        z-index: 1;
    }}
    </style>
    """


def inject_professional_theme():
    """Inject professional CSS into Streamlit"""
    import streamlit as st
    st.markdown(get_professional_css(), unsafe_allow_html=True)
    
    # Hide sidebar completely
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)