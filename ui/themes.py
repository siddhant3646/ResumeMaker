"""
Ultra-Modern 2026 UI Design System
Glass morphism, aurora gradients, bento grids, modern typography
"""

from dataclasses import dataclass


@dataclass
class ModernTheme:
    """
    Ultra-modern 2026 design system
    Features: Glass morphism, aurora gradients, floating cards, bento layout
    """
    
    # Base Colors
    bg_dark: str = "#030712"  # Almost black
    bg_navy: str = "#0f172a"  # Deep navy
    bg_card: str = "rgba(15, 23, 42, 0.6)"  # Glass effect
    
    # Aurora Gradients
    aurora_1: str = "rgba(59, 130, 246, 0.4)"  # Blue
    aurora_2: str = "rgba(139, 92, 246, 0.4)"  # Purple  
    aurora_3: str = "rgba(236, 72, 153, 0.3)"  # Pink
    aurora_4: str = "rgba(16, 185, 129, 0.3)"  # Emerald
    
    # Accent Colors
    accent_blue: str = "#60a5fa"
    accent_purple: str = "#a78bfa"
    accent_pink: str = "#f472b6"
    accent_emerald: str = "#34d399"
    accent_orange: str = "#fb923c"
    
    # Gradients
    gradient_hero: str = "linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)"
    gradient_text: str = "linear-gradient(135deg, #60a5fa 0%, #a78bfa 50%, #f472b6 100%)"
    gradient_card: str = "linear-gradient(145deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)"
    gradient_button: str = "linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)"
    gradient_success: str = "linear-gradient(135deg, #10b981 0%, #34d399 100%)"
    
    # Glass Effect
    glass_bg: str = "rgba(15, 23, 42, 0.4)"
    glass_border: str = "rgba(255, 255, 255, 0.1)"
    glass_blur: str = "blur(20px)"
    
    # Text
    text_white: str = "#ffffff"
    text_gray_100: str = "#f3f4f6"
    text_gray_300: str = "#d1d5db"
    text_gray_400: str = "#9ca3af"
    text_gray_500: str = "#6b7280"
    text_gray_600: str = "#4b5563"
    text_gray_700: str = "#374151"
    text_gray_800: str = "#1f2937"
    text_gray_900: str = "#111827"


def get_modern_css() -> str:
    """Generate ultra-modern CSS with glass morphism and aurora effects"""
    theme = ModernTheme()
    
    return f"""
    <style>
    /* ===== RESET & BASE ===== */
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}
    
    /* ===== BODY ===== */
    .stApp {{
        background: {theme.bg_dark};
        position: relative;
        overflow-x: hidden;
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
        color: {theme.text_white};
    }}
    
    .stApp::before {{
        content: '';
        position: fixed;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: 
            radial-gradient(circle at 20% 30%, {theme.aurora_1} 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, {theme.aurora_2} 0%, transparent 40%),
            radial-gradient(circle at 60% 80%, {theme.aurora_3} 0%, transparent 45%),
            radial-gradient(circle at 30% 70%, {theme.aurora_4} 0%, transparent 35%);
        animation: aurora 20s ease-in-out infinite;
        pointer-events: none;
        z-index: 0;
    }}
    
    /* ===== AURORA ANIMATION ===== */
    @keyframes aurora {{
        0%, 100% {{
            transform: rotate(0deg) scale(1);
            opacity: 0.5;
        }}
        25% {{
            transform: rotate(90deg) scale(1.1);
            opacity: 0.7;
        }}
        50% {{
            transform: rotate(180deg) scale(0.9);
            opacity: 0.6;
        }}
        75% {{
            transform: rotate(270deg) scale(1.05);
            opacity: 0.8;
        }}
    }}
    
    /* ===== GLASS CARDS ===== */
    .glass-card {{
        background: {theme.glass_bg};
        border: 1px solid {theme.glass_border};
        border-radius: 16px;
        backdrop-filter: {theme.glass_blur};
        -webkit-backdrop-filter: {theme.glass_blur};
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }}
    
    .glass-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, 
            rgba(255,255,255,0.1) 0%, 
            rgba(255,255,255,0.05) 50%,
            rgba(255,255,255,0.02) 100%);
        border-radius: 16px;
        pointer-events: none;
    }}
    
    .glass-card:hover {{
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.45);
        border-color: rgba(255, 255, 255, 0.2);
    }}
    
    /* ===== FLOATING BENTO GRIDS ===== */
    .bento-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
        padding: 2rem;
    }}
    
    .bento-item {{
        background: {theme.glass_bg};
        border: 1px solid {theme.glass_border};
        border-radius: 12px;
        backdrop-filter: {theme.glass_blur};
        -webkit-backdrop-filter: {theme.glass_blur};
        padding: 1.5rem;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }}
    
    .bento-item:hover {{
        transform: translateY(-2px);
        border-color: {theme.accent_blue};
        box-shadow: 0 8px 25px 0 rgba(96, 165, 250, 0.3);
    }}
    
    /* ===== MAGNETIC BUTTONS ===== */
    .magnetic-button {{
        background: {theme.gradient_button};
        color: {theme.text_white};
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-family: inherit;
        transition: all 0.2s ease;
        position: relative;
        overflow: hidden;
        cursor: pointer;
        text-decoration: none;
        display: inline-block;
    }}
    
    .magnetic-button::before {{
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }}
    
    .magnetic-button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 25px 0 rgba(59, 130, 246, 0.4);
    }}
    
    /* ===== 3D TILT EFFECT ===== */
    .tilt-card {{
        perspective: 1000px;
        transition: all 0.3s ease;
    }}
    
    .tilt-inner {{
        background: {theme.glass_bg};
        border: 1px solid {theme.glass_border};
        border-radius: 16px;
        backdrop-filter: {theme.glass_blur};
        -webkit-backdrop-filter: {theme.glass_blur};
        transition: transform 0.1s ease-out;
        transform-style: preserve-3d;
    }}
    
    /* ===== GLITCH TEXT EFFECT ===== */
    .glitch-text {{
        position: relative;
        font-weight: 700;
        text-transform: uppercase;
        color: {theme.text_white};
        letter-spacing: 2px;
    }}
    
    .glitch-text::before,
    .glitch-text::after {{
        content: attr(data-text);
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
    }}
    
    .glitch-text::before {{
        animation: glitch-1 0.5s infinite linear alternate-reverse;
        color: {theme.accent_blue};
        z-index: -1;
    }}
    
    .glitch-text::after {{
        animation: glitch-2 0.5s infinite linear alternate;
        color: {theme.accent_pink};
        z-index: -2;
    }}
    
    @keyframes glitch-1 {{
        0%, 100% {{ clip: rect(42px, 9999px, 44px, 0); }}
        25% {{ clip: rect(12px, 9999px, 80px, 0); }}
        50% {{ clip: rect(32px, 9999px, 60px, 0); }}
        75% {{ clip: rect(20px, 9999px, 90px, 0); }}
    }}
    
    @keyframes glitch-2 {{
        0%, 100% {{ clip: rect(65px, 9999px, 119px, 0); }}
        25% {{ clip: rect(30px, 9999px, 100px, 0); }}
        50% {{ clip: rect(85px, 9999px, 40px, 0); }}
        75% {{ clip: rect(15px, 9999px, 105px, 0); }}
    }}
    
    /* ===== PROFESSIONAL BUTTONS ===== */
    .stButton > button {{
        background: {theme.gradient_button} !important;
        color: {theme.text_white} !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-family: inherit !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 12px 0 rgba(59, 130, 246, 0.3) !important;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px 0 rgba(59, 130, 246, 0.4) !important;
    }}
    
    /* ===== SECTION HEADERS ===== */
    .modern-header {{
        background: {theme.gradient_text};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
        font-size: 1.5rem;
        margin-bottom: 1rem;
    }}
    
    /* ===== INPUT FIELDS ===== */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        background: {theme.glass_bg} !important;
        border: 1px solid {theme.glass_border} !important;
        border-radius: 8px !important;
        backdrop-filter: {theme.glass_blur} !important;
        -webkit-backdrop-filter: {theme.glass_blur} !important;
        color: {theme.text_white} !important;
        padding: 0.75rem !important;
        transition: all 0.2s ease !important;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: {theme.accent_blue} !important;
        box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.2) !important;
        outline: none !important;
    }}
    
    /* ===== PROGRESS BARS ===== */
    .stProgress > div > div > div {{
        background: {theme.gradient_button} !important;
        border-radius: 4px !important;
    }}
    
    /* ===== UPLOAD AREA ===== */
    .upload-zone {{
        background: {theme.glass_bg};
        border: 2px dashed {theme.glass_border};
        border-radius: 12px;
        padding: 3rem;
        text-align: center;
        backdrop-filter: {theme.glass_blur};
        -webkit-backdrop-filter: {theme.glass_blur};
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }}
    
    .upload-zone::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, 
            rgba(59, 130, 246, 0.1) 0%, 
            rgba(139, 92, 246, 0.05) 100%);
        pointer-events: none;
    }}
    
    .upload-zone:hover {{
        border-color: {theme.accent_blue};
        background: rgba(59, 130, 246, 0.1);
        transform: translateY(-2px);
    }}
    
    /* ===== FLOATING PARTICLES ===== */
    .particle {{
        position: fixed;
        pointer-events: none;
        opacity: 0.5;
        animation: float 20s infinite linear;
        z-index: 0;
    }}
    
    @keyframes float {{
        0% {{
            transform: translateY(100vh) rotate(0deg);
            opacity: 0;
        }}
        10% {{
            opacity: 0.5;
        }}
        90% {{
            opacity: 0.5;
        }}
        100% {{
            transform: translateY(-100vh) rotate(360deg);
            opacity: 0;
        }}
    }}
    
    /* ===== CLEAN SCROLLBAR ===== */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: {theme.bg_navy};
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: {theme.text_gray_600};
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: {theme.accent_blue};
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
    
    /* ===== ANIMATED HERO LOGO ===== */
    .hero-logo {{
        font-size: 11rem;
        font-weight: 900;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #667eea 75%, #764ba2 100%);
        background-size: 300% 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: gradient-shift 4s ease infinite;
        text-shadow: 0 0 60px rgba(102, 126, 234, 0.6);
        letter-spacing: -2px;
    }}
    
    @keyframes gradient-shift {{
        0%, 100% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
    }}
    
    .hero-tagline {{
        font-size: 1.25rem;
        color: {theme.text_gray_400};
        margin-top: 0.75rem;
        opacity: 0;
        animation: fade-in-up 0.8s ease forwards 0.3s;
    }}
    
    @keyframes fade-in-up {{
        from {{
            opacity: 0;
            transform: translateY(20px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    /* ===== STEP PROGRESS WIZARD ===== */
    .step-wizard {{
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 0;
        margin: 2rem 0;
        padding: 0 2rem;
    }}
    
    .step-item {{
        display: flex;
        align-items: center;
        position: relative;
    }}
    
    .step-circle {{
        width: 48px;
        height: 48px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 1.1rem;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        z-index: 2;
    }}
    
    .step-circle.completed {{
        background: {theme.gradient_success};
        color: white;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.5);
    }}
    
    .step-circle.active {{
        background: {theme.gradient_button};
        color: white;
        box-shadow: 0 0 25px rgba(59, 130, 246, 0.6);
        animation: pulse-glow 2s ease-in-out infinite;
    }}
    
    .step-circle.inactive {{
        background: {theme.glass_bg};
        border: 2px solid {theme.glass_border};
        color: {theme.text_gray_500};
    }}
    
    @keyframes pulse-glow {{
        0%, 100% {{
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.4);
            transform: scale(1);
        }}
        50% {{
            box-shadow: 0 0 35px rgba(139, 92, 246, 0.6);
            transform: scale(1.05);
        }}
    }}
    
    .step-connector {{
        width: 80px;
        height: 4px;
        background: {theme.glass_border};
        position: relative;
        overflow: hidden;
    }}
    
    .step-connector.completed {{
        background: {theme.gradient_success};
    }}
    
    .step-connector.active {{
        background: linear-gradient(90deg, {theme.accent_emerald} 0%, {theme.accent_blue} 100%);
    }}
    
    .step-label {{
        position: absolute;
        top: 60px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 0.85rem;
        white-space: nowrap;
        color: {theme.text_gray_400};
        font-weight: 500;
    }}
    
    .step-circle.active + .step-label,
    .step-circle.completed + .step-label {{
        color: {theme.text_white};
    }}
    
    /* ===== CIRCULAR ATS GAUGE ===== */
    .ats-gauge {{
        position: relative;
        width: 180px;
        height: 180px;
        margin: 0 auto;
    }}
    
    .ats-gauge svg {{
        transform: rotate(-90deg);
    }}
    
    .ats-gauge-bg {{
        fill: none;
        stroke: {theme.glass_border};
        stroke-width: 12;
    }}
    
    .ats-gauge-fill {{
        fill: none;
        stroke-width: 12;
        stroke-linecap: round;
        transition: stroke-dashoffset 1.5s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    
    .ats-gauge-fill.excellent {{
        stroke: url(#gauge-gradient-excellent);
    }}
    
    .ats-gauge-fill.good {{
        stroke: url(#gauge-gradient-good);
    }}
    
    .ats-gauge-fill.needs-work {{
        stroke: url(#gauge-gradient-warning);
    }}
    
    .ats-gauge-value {{
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        text-align: center;
    }}
    
    .ats-gauge-number {{
        font-size: 3rem;
        font-weight: 800;
        background: {theme.gradient_text};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1;
    }}
    
    .ats-gauge-label {{
        font-size: 0.9rem;
        color: {theme.text_gray_400};
        margin-top: 0.25rem;
    }}
    
    /* ===== SCORE BREAKDOWN BARS ===== */
    .score-bar-container {{
        margin: 0.75rem 0;
    }}
    
    .score-bar-header {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }}
    
    .score-bar-label {{
        color: {theme.text_gray_300};
        font-weight: 500;
    }}
    
    .score-bar-value {{
        color: {theme.text_white};
        font-weight: 700;
    }}
    
    .score-bar-track {{
        height: 8px;
        background: {theme.glass_bg};
        border-radius: 4px;
        overflow: hidden;
    }}
    
    .score-bar-fill {{
        height: 100%;
        border-radius: 4px;
        transition: width 1.2s cubic-bezier(0.4, 0, 0.2, 1);
        background: {theme.gradient_button};
    }}
    
    .score-bar-fill.excellent {{
        background: {theme.gradient_success};
    }}
    
    .score-bar-fill.good {{
        background: {theme.gradient_button};
    }}
    
    .score-bar-fill.warning {{
        background: linear-gradient(90deg, #f59e0b 0%, #fbbf24 100%);
    }}
    
    /* ===== PULSING LOADING ANIMATION ===== */
    .loading-pulse {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }}
    
    .loading-dot {{
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: {theme.accent_blue};
        animation: loading-bounce 1.4s infinite ease-in-out both;
    }}
    
    .loading-dot:nth-child(1) {{ animation-delay: -0.32s; background: {theme.accent_blue}; }}
    .loading-dot:nth-child(2) {{ animation-delay: -0.16s; background: {theme.accent_purple}; }}
    .loading-dot:nth-child(3) {{ animation-delay: 0s; background: {theme.accent_pink}; }}
    
    @keyframes loading-bounce {{
        0%, 80%, 100% {{
            transform: scale(0);
        }}
        40% {{
            transform: scale(1);
        }}
    }}
    
    /* ===== SKELETON LOADING ===== */
    .skeleton {{
        background: linear-gradient(90deg, {theme.glass_bg} 25%, rgba(255,255,255,0.1) 50%, {theme.glass_bg} 75%);
        background-size: 200% 100%;
        animation: skeleton-shimmer 1.5s infinite;
        border-radius: 8px;
    }}
    
    @keyframes skeleton-shimmer {{
        0% {{ background-position: 200% 0; }}
        100% {{ background-position: -200% 0; }}
    }}
    
    /* ===== CONFETTI CELEBRATION ===== */
    .confetti-container {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 9999;
        overflow: hidden;
    }}
    
    .confetti {{
        position: absolute;
        width: 10px;
        height: 10px;
        animation: confetti-fall 3s linear forwards;
    }}
    
    @keyframes confetti-fall {{
        0% {{
            opacity: 1;
            transform: translateY(-10vh) rotate(0deg);
        }}
        100% {{
            opacity: 0;
            transform: translateY(100vh) rotate(720deg);
        }}
    }}
    
    /* ===== SUCCESS CARD ===== */
    .success-card {{
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(52, 211, 153, 0.1) 100%);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        animation: success-pop 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
    }}
    
    @keyframes success-pop {{
        0% {{
            transform: scale(0.8);
            opacity: 0;
        }}
        100% {{
            transform: scale(1);
            opacity: 1;
        }}
    }}
    
    .success-icon {{
        font-size: 4rem;
        margin-bottom: 1rem;
        animation: bounce-in 0.6s ease-out 0.2s backwards;
    }}
    
    @keyframes bounce-in {{
        0% {{
            transform: scale(0);
        }}
        50% {{
            transform: scale(1.2);
        }}
        100% {{
            transform: scale(1);
        }}
    }}
    
    /* ===== FEATURE PILLS ===== */
    .feature-pills {{
        display: flex;
        justify-content: center;
        gap: 1rem;
        flex-wrap: wrap;
        margin: 1.5rem 0;
    }}
    
    .feature-pill {{
        background: {theme.glass_bg};
        border: 1px solid {theme.glass_border};
        border-radius: 50px;
        padding: 0.5rem 1.25rem;
        font-size: 0.9rem;
        color: {theme.text_gray_300};
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}
    
    .feature-pill:hover {{
        border-color: {theme.accent_blue};
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
    }}
    
    .feature-pill .icon {{
        font-size: 1.1rem;
    }}
    
    /* ===== ANIMATED DOWNLOAD BUTTON ===== */
    .download-btn {{
        background: {theme.gradient_success};
        color: white;
        border: none;
        border-radius: 12px;
        padding: 1rem 2.5rem;
        font-size: 1.1rem;
        font-weight: 700;
        cursor: pointer;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }}
    
    .download-btn::before {{
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        transition: left 0.5s ease;
    }}
    
    .download-btn:hover::before {{
        left: 100%;
    }}
    
    .download-btn:hover {{
        transform: translateY(-3px);
        box-shadow: 0 10px 30px rgba(16, 185, 129, 0.4);
    }}
    
    /* ===== MOBILE RESPONSIVE STYLES ===== */
    
    /* Tablet and smaller (max-width: 1024px) */
    @media screen and (max-width: 1024px) {{
        .bento-grid {{
            grid-template-columns: 1fr;
            gap: 1rem;
            padding: 1rem;
        }}
        
        .hero-logo {{
            font-size: 6rem !important;
        }}
        
        .step-wizard {{
            padding: 0 1rem;
        }}
        
        .step-connector {{
            width: 40px;
        }}
    }}
    
    /* Mobile devices (max-width: 768px) */
    @media screen and (max-width: 768px) {{
        /* Hero section */
        .hero-logo {{
            font-size: 3.5rem !important;
            letter-spacing: -1px;
        }}
        
        .hero-tagline {{
            font-size: 1rem !important;
        }}
        
        /* Bento grid single column */
        .bento-grid {{
            grid-template-columns: 1fr;
            gap: 0.75rem;
            padding: 0.75rem;
        }}
        
        .bento-item {{
            padding: 1rem;
        }}
        
        /* Step wizard vertical on mobile */
        .step-wizard {{
            flex-direction: column;
            gap: 1rem;
        }}
        
        .step-connector {{
            width: 4px;
            height: 30px;
        }}
        
        .step-item {{
            flex-direction: row;
            width: 100%;
            justify-content: flex-start;
            gap: 1rem;
        }}
        
        .step-label {{
            position: static;
            transform: none;
            text-align: left;
        }}
        
        /* Smaller gauges */
        .ats-gauge {{
            width: 120px;
            height: 120px;
        }}
        
        .ats-gauge-number {{
            font-size: 2rem;
        }}
        
        /* Feature pills wrap */
        .feature-pills {{
            gap: 0.5rem;
        }}
        
        .feature-pill {{
            padding: 0.4rem 0.8rem;
            font-size: 0.8rem;
        }}
        
        /* Touch-friendly buttons */
        .stButton > button {{
            min-height: 44px;
            font-size: 0.9rem;
        }}
        
        /* Glass cards */
        .glass-card {{
            border-radius: 12px;
        }}
        
        /* Adjust main container padding */
        .main .block-container {{
            padding-left: 1rem;
            padding-right: 1rem;
        }}
    }}
    
    /* Small mobile devices (max-width: 480px) */
    @media screen and (max-width: 480px) {{
        .hero-logo {{
            font-size: 2.5rem !important;
        }}
        
        .hero-tagline {{
            font-size: 0.9rem !important;
        }}
        
        .step-circle {{
            width: 36px;
            height: 36px;
            font-size: 0.9rem;
        }}
        
        .step-label {{
            font-size: 0.75rem;
        }}
        
        .bento-item {{
            padding: 0.75rem;
        }}
        
        .feature-pill {{
            font-size: 0.75rem;
            padding: 0.3rem 0.6rem;
        }}
        
        /* Smaller ATS gauge */
        .ats-gauge {{
            width: 100px;
            height: 100px;
        }}
        
        .ats-gauge-number {{
            font-size: 1.5rem;
        }}
        
        .ats-gauge-label {{
            font-size: 0.75rem;
        }}
        
        /* Full-width upload zone */
        .upload-zone {{
            padding: 1.5rem 1rem;
        }}
        
        /* Score bars */
        .score-bar-container {{
            margin: 0.5rem 0;
        }}
        
        .score-bar-label, .score-bar-value {{
            font-size: 0.8rem;
        }}
    }}
    
    /* Touch device optimizations */
    @media (hover: none) and (pointer: coarse) {{
        .glass-card:hover,
        .bento-item:hover,
        .magnetic-button:hover {{
            transform: none;
        }}
        
        .tilt-card {{
            perspective: none;
        }}
        
        .tilt-inner {{
            transform: none !important;
        }}
    }}
    
    /* Safe area for notched devices */
    @supports (padding: max(0px)) {{
        .stApp {{
            padding-left: max(1rem, env(safe-area-inset-left));
            padding-right: max(1rem, env(safe-area-inset-right));
        }}
    }}
    </style>
    """


def inject_modern_theme():
    """Inject modern CSS and JS into Streamlit"""
    import streamlit as st
    st.markdown(get_modern_css(), unsafe_allow_html=True)
    st.markdown(get_interactive_js(), unsafe_allow_html=True)


def get_interactive_js() -> str:
    """Add interactive JavaScript for 3D effects and animations"""
    return """
    <script>
    // Add floating particles
    function createParticles() {
        const colors = ['#3b82f6', '#8b5cf6', '#f59e0b', '#10b981'];
        for (let i = 0; i < 5; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.left = Math.random() * window.innerWidth + 'px';
            particle.style.width = particle.style.height = Math.random() * 4 + 2 + 'px';
            particle.style.background = colors[Math.floor(Math.random() * colors.length)];
            particle.style.animationDelay = Math.random() * 20 + 's';
            particle.style.animationDuration = (Math.random() * 20 + 10) + 's';
            document.body.appendChild(particle);
        }
    }
    
    // Create 3D tilt effect
    function addTiltEffect() {
        const cards = document.querySelectorAll('.tilt-card');
        cards.forEach(card => {
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;
                
                const rotateX = (y - centerY) / 10;
                const rotateY = (centerX - x) / 10;
                
                card.querySelector('.tilt-inner').style.transform = 
                    `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
            });
            
            card.addEventListener('mouseleave', () => {
                card.querySelector('.tilt-inner').style.transform = 
                    'perspective(1000px) rotateX(0deg) rotateY(0deg)';
            });
        });
    }
    
    // Initialize effects
    document.addEventListener('DOMContentLoaded', () => {
        createParticles();
        addTiltEffect();
    });
    </script>
    """