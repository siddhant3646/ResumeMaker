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


def get_modern_css() -> str:
    """Generate ultra-modern CSS with aurora effects and glass morphism"""
    theme = ModernTheme()
    
    return f"""
    <style>
    /* ===== RESET & BASE ===== */
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}
    
    /* ===== AURORA BACKGROUND ===== */
    .stApp {{
        background: {theme.bg_dark};
        position: relative;
        overflow-x: hidden;
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
    
    @keyframes aurora {{
        0%, 100% {{
            transform: translate(0, 0) rotate(0deg);
        }}
        25% {{
            transform: translate(2%, 2%) rotate(2deg);
        }}
        50% {{
            transform: translate(-1%, 3%) rotate(-1deg);
        }}
        75% {{
            transform: translate(3%, -2%) rotate(1deg);
        }}
    }}
    
    /* ===== GLASS CARD ===== */
    .glass-card {{
        background: {theme.glass_bg};
        backdrop-filter: {theme.glass_blur};
        -webkit-backdrop-filter: {theme.glass_blur};
        border: 1px solid {theme.glass_border};
        border-radius: 24px;
        padding: 2rem;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
    }}
    
    .glass-card:hover {{
        transform: translateY(-4px);
        box-shadow: 
            0 12px 48px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.15);
        border-color: rgba(255, 255, 255, 0.2);
    }}
    
    /* ===== GRADIENT TEXT ===== */
    .gradient-text {{
        background: {theme.gradient_text};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800;
    }}
    
    /* ===== HERO SECTION ===== */
    .hero-section {{
        text-align: center;
        padding: 4rem 2rem;
        position: relative;
        z-index: 1;
    }}
    
    .hero-title {{
        font-size: 4rem;
        font-weight: 900;
        margin-bottom: 1rem;
        background: {theme.gradient_text};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.02em;
        line-height: 1.1;
    }}
    
    .hero-subtitle {{
        font-size: 1.5rem;
        color: {theme.text_gray_300};
        font-weight: 400;
        max-width: 600px;
        margin: 0 auto;
        line-height: 1.6;
    }}
    
    /* ===== BENTO GRID ===== */
    .bento-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
        position: relative;
        z-index: 1;
    }}
    
    .bento-item {{
        background: {theme.glass_bg};
        backdrop-filter: {theme.glass_blur};
        -webkit-backdrop-filter: {theme.glass_blur};
        border: 1px solid {theme.glass_border};
        border-radius: 20px;
        padding: 2rem;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    
    .bento-item:hover {{
        transform: scale(1.02);
        border-color: rgba(139, 92, 246, 0.3);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
    }}
    
    .bento-item.large {{
        grid-column: span 2;
    }}
    
    /* ===== MODERN BUTTON ===== */
    .modern-button {{
        background: {theme.gradient_button};
        color: white;
        border: none;
        border-radius: 12px;
        padding: 1rem 2rem;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
    }}
    
    .modern-button::before {{
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s ease;
    }}
    
    .modern-button:hover::before {{
        left: 100%;
    }}
    
    .modern-button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.5);
    }}
    
    /* ===== UPLOAD ZONE ===== */
    .upload-zone {{
        background: {theme.glass_bg};
        backdrop-filter: {theme.glass_blur};
        border: 2px dashed {theme.glass_border};
        border-radius: 24px;
        padding: 3rem;
        text-align: center;
        transition: all 0.3s ease;
        cursor: pointer;
    }}
    
    .upload-zone:hover {{
        border-color: {theme.accent_blue};
        background: rgba(59, 130, 246, 0.1);
        transform: scale(1.01);
    }}
    
    .upload-icon {{
        font-size: 3rem;
        margin-bottom: 1rem;
        background: {theme.gradient_text};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    
    /* ===== STEP INDICATOR ===== */
    .step-indicator-modern {{
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 0.5rem;
        margin: 2rem 0;
        position: relative;
        z-index: 1;
    }}
    
    .step-line {{
        width: 60px;
        height: 2px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 1px;
    }}
    
    .step-line.active {{
        background: {theme.gradient_button};
    }}
    
    .step-dot-modern {{
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: {theme.glass_bg};
        border: 2px solid {theme.glass_border};
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: {theme.text_gray_400};
        transition: all 0.3s ease;
    }}
    
    .step-dot-modern.active {{
        background: {theme.gradient_button};
        border-color: transparent;
        color: white;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
    }}
    
    .step-dot-modern.completed {{
        background: {theme.gradient_success};
        border-color: transparent;
        color: white;
    }}
    
    /* ===== FLOATING STATS ===== */
    .floating-stat {{
        display: inline-flex;
        align-items: center;
        gap: 0.75rem;
        background: {theme.glass_bg};
        backdrop-filter: {theme.glass_blur};
        border: 1px solid {theme.glass_border};
        border-radius: 100px;
        padding: 0.75rem 1.5rem;
        font-size: 0.9rem;
        color: {theme.text_gray_300};
        transition: all 0.3s ease;
    }}
    
    .floating-stat:hover {{
        transform: translateY(-2px);
        border-color: rgba(139, 92, 246, 0.3);
    }}
    
    .floating-stat .value {{
        font-weight: 700;
        color: {theme.accent_blue};
    }}
    
    /* ===== ATS SCORE DISPLAY ===== */
    .ats-score-container {{
        background: {theme.glass_bg};
        backdrop-filter: {theme.glass_blur};
        border: 1px solid {theme.glass_border};
        border-radius: 24px;
        padding: 2.5rem;
        text-align: center;
        position: relative;
        overflow: hidden;
    }}
    
    .ats-score-container::before {{
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(16, 185, 129, 0.2) 0%, transparent 70%);
        animation: pulse-glow 3s ease-in-out infinite;
    }}
    
    @keyframes pulse-glow {{
        0%, 100% {{ transform: scale(1); opacity: 0.5; }}
        50% {{ transform: scale(1.1); opacity: 0.8; }}
    }}
    
    .ats-score-value {{
        font-size: 5rem;
        font-weight: 900;
        background: {theme.gradient_success};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1;
        position: relative;
        z-index: 1;
    }}
    
    .ats-score-label {{
        font-size: 1rem;
        color: {theme.text_gray_400};
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 0.5rem;
        position: relative;
        z-index: 1;
    }}
    
    /* ===== SETTINGS PANEL ===== */
    .settings-panel-modern {{
        background: {theme.glass_bg};
        backdrop-filter: {theme.glass_blur};
        border: 1px solid {theme.glass_border};
        border-radius: 20px;
        padding: 2rem;
    }}
    
    .settings-title {{
        font-size: 1.25rem;
        font-weight: 700;
        color: {theme.text_white};
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}
    
    /* ===== TOGGLE SWITCH ===== */
    .toggle-container {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 0;
        border-bottom: 1px solid {theme.glass_border};
    }}
    
    .toggle-label {{
        color: {theme.text_gray_300};
        font-weight: 500;
    }}
    
    /* ===== ANIMATIONS ===== */
    @keyframes fadeInUp {{
        from {{
            opacity: 0;
            transform: translateY(30px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    @keyframes float {{
        0%, 100% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-10px); }}
    }}
    
    .animate-fade-in-up {{
        animation: fadeInUp 0.6s ease-out forwards;
    }}
    
    .animate-float {{
        animation: float 4s ease-in-out infinite;
    }}
    
    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: rgba(255, 255, 255, 0.05);
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: rgba(255, 255, 255, 0.2);
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: rgba(255, 255, 255, 0.3);
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
    
    /* ===== STREAMLIT OVERRIDES ===== */
    .stButton > button {{
        background: {theme.gradient_button} !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.875rem 2rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.5) !important;
    }}
    
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        background: {theme.glass_bg} !important;
        border: 1px solid {theme.glass_border} !important;
        border-radius: 12px !important;
        color: white !important;
        padding: 1rem !important;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: {theme.accent_blue} !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }}
    
    .stSelectbox > div > div,
    .stSlider > div {{
        background: {theme.glass_bg} !important;
        border: 1px solid {theme.glass_border} !important;
        border-radius: 12px !important;
    }}
    
    .stProgress > div > div > div {{
        background: {theme.gradient_button} !important;
        border-radius: 10px !important;
    }}
    
    .stFileUploader {{
        background: {theme.glass_bg} !important;
        border: 2px dashed {theme.glass_border} !important;
        border-radius: 20px !important;
        padding: 2rem !important;
    }}
    
    .stFileUploader:hover {{
        border-color: {theme.accent_blue} !important;
        background: rgba(59, 130, 246, 0.1) !important;
    }}
    
    /* ===== PARTICLE BACKGROUND ===== */
    .particle-container {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 0;
        overflow: hidden;
    }}
    
    .particle {{
        position: absolute;
        width: 4px;
        height: 4px;
        background: rgba(255, 255, 255, 0.5);
        border-radius: 50%;
        animation: float-particle 15s infinite;
    }}
    
    @keyframes float-particle {{
        0%, 100% {{
            transform: translateY(100vh) rotate(0deg);
            opacity: 0;
        }}
        10% {{
            opacity: 1;
        }}
        90% {{
            opacity: 1;
        }}
        100% {{
            transform: translateY(-100vh) rotate(720deg);
            opacity: 0;
        }}
    }}
    
    /* ===== 3D CARD TILT ===== */
    .tilt-card {{
        transform-style: preserve-3d;
        transform: perspective(1000px);
        transition: transform 0.3s ease;
    }}
    
    .tilt-card:hover {{
        transform: perspective(1000px) rotateX(5deg) rotateY(5deg) translateZ(20px);
    }}
    
    .tilt-card-inner {{
        transform: translateZ(30px);
    }}
    
    /* ===== LOADING SKELETON ===== */
    .skeleton {{
        background: linear-gradient(90deg, 
            rgba(255, 255, 255, 0.05) 25%, 
            rgba(255, 255, 255, 0.1) 50%, 
            rgba(255, 255, 255, 0.05) 75%);
        background-size: 200% 100%;
        animation: skeleton-loading 1.5s infinite;
        border-radius: 8px;
    }}
    
    @keyframes skeleton-loading {{
        0% {{ background-position: 200% 0; }}
        100% {{ background-position: -200% 0; }}
    }}
    
    .skeleton-text {{
        height: 1rem;
        margin-bottom: 0.5rem;
    }}
    
    .skeleton-title {{
        height: 1.5rem;
        width: 60%;
        margin-bottom: 1rem;
    }}
    
    .skeleton-circle {{
        width: 60px;
        height: 60px;
        border-radius: 50%;
    }}
    
    /* ===== MICRO-INTERACTIONS ===== */
    .micro-button {{
        position: relative;
        overflow: hidden;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    
    .micro-button::after {{
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
    
    .micro-button:active::after {{
        width: 300px;
        height: 300px;
    }}
    
    .micro-button:active {{
        transform: scale(0.95);
    }}
    
    .micro-hover {{
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    
    .micro-hover:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }}
    
    /* Magnetic Button Effect */
    .magnetic-button {{
        transition: transform 0.2s ease-out;
    }}
    
    /* ===== PARALLAX SCROLLING ===== */
    .parallax-container {{
        position: relative;
        overflow: hidden;
    }}
    
    .parallax-layer {{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 120%;
        will-change: transform;
    }}
    
    .parallax-bg {{
        background: radial-gradient(circle at 30% 30%, rgba(59, 130, 246, 0.15) 0%, transparent 50%);
        transform: translateZ(-1px) scale(2);
    }}
    
    /* Scroll Reveal Animation */
    .reveal {{
        opacity: 0;
        transform: translateY(30px);
        transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    
    .reveal.active {{
        opacity: 1;
        transform: translateY(0);
    }}
    
    .reveal-delay-1 {{ transition-delay: 0.1s; }}
    .reveal-delay-2 {{ transition-delay: 0.2s; }}
    .reveal-delay-3 {{ transition-delay: 0.3s; }}
    .reveal-delay-4 {{ transition-delay: 0.4s; }}
    
    /* ===== NEON GLOW EFFECTS ===== */
    .neon-glow {{
        box-shadow: 
            0 0 5px rgba(59, 130, 246, 0.5),
            0 0 10px rgba(59, 130, 246, 0.3),
            0 0 20px rgba(59, 130, 246, 0.2);
    }}
    
    .neon-text {{
        text-shadow: 
            0 0 5px rgba(139, 92, 246, 0.8),
            0 0 10px rgba(139, 92, 246, 0.5),
            0 0 20px rgba(139, 92, 246, 0.3);
    }}
    
    /* ===== SHIMMER EFFECT ===== */
    .shimmer {{
        position: relative;
        overflow: hidden;
    }}
    
    .shimmer::after {{
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 50%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        animation: shimmer 2s infinite;
    }}
    
    @keyframes shimmer {{
        100% {{ left: 200%; }}
    }}
    
    /* ===== MORPHING BLOB ===== */
    .blob {{
        position: absolute;
        border-radius: 50%;
        filter: blur(60px);
        opacity: 0.4;
        animation: morph 15s ease-in-out infinite;
    }}
    
    @keyframes morph {{
        0%, 100% {{ border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; }}
        25% {{ border-radius: 30% 60% 70% 40% / 50% 60% 30% 60%; }}
        50% {{ border-radius: 50% 60% 30% 60% / 30% 40% 70% 60%; }}
        75% {{ border-radius: 60% 40% 60% 30% / 70% 30% 50% 60%; }}
    }}
    
    /* ===== CURSOR GLOW ===== */
    .cursor-glow {{
        position: fixed;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
        z-index: 9999;
        transform: translate(-50%, -50%);
        transition: opacity 0.3s;
    }}
    
    /* ===== LIQUID BUTTON ===== */
    .liquid-button {{
        position: relative;
        overflow: hidden;
        z-index: 1;
    }}
    
    .liquid-button::before {{
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
        transition: left 0.5s;
        z-index: -1;
    }}
    
    .liquid-button:hover::before {{
        left: 100%;
    }}
    
    /* ===== TEXT SCRAMBLE EFFECT ===== */
    .scramble-text {{
        display: inline-block;
    }}
    
    /* ===== GRADIENT BORDER ===== */
    .gradient-border {{
        position: relative;
        background: {theme.bg_navy};
        border-radius: 16px;
    }}
    
    .gradient-border::before {{
        content: '';
        position: absolute;
        inset: -2px;
        border-radius: 18px;
        background: linear-gradient(135deg, #60a5fa, #a78bfa, #f472b6);
        z-index: -1;
        opacity: 0;
        transition: opacity 0.3s;
    }}
    
    .gradient-border:hover::before {{
        opacity: 1;
    }}
    
    /* ===== STAGGERED GRID ANIMATION ===== */
    .stagger-grid > * {{
        opacity: 0;
        transform: translateY(20px);
        animation: stagger-in 0.5s ease forwards;
    }}
    
    .stagger-grid > *:nth-child(1) {{ animation-delay: 0.1s; }}
    .stagger-grid > *:nth-child(2) {{ animation-delay: 0.2s; }}
    .stagger-grid > *:nth-child(3) {{ animation-delay: 0.3s; }}
    .stagger-grid > *:nth-child(4) {{ animation-delay: 0.4s; }}
    .stagger-grid > *:nth-child(5) {{ animation-delay: 0.5s; }}
    .stagger-grid > *:nth-child(6) {{ animation-delay: 0.6s; }}
    
    @keyframes stagger-in {{
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    /* ===== HOLOGRAPHIC EFFECT ===== */
    .holographic {{
        background: linear-gradient(
            135deg,
            rgba(255, 255, 255, 0.1) 0%,
            rgba(255, 255, 255, 0.05) 25%,
            rgba(255, 255, 255, 0.1) 50%,
            rgba(255, 255, 255, 0.05) 75%,
            rgba(255, 255, 255, 0.1) 100%
        );
        background-size: 200% 200%;
        animation: holographic-shift 3s linear infinite;
    }}
    
    @keyframes holographic-shift {{
        0% {{ background-position: 0% 0%; }}
        100% {{ background-position: 200% 200%; }}
    }}
    </style>
    """


def get_interactive_js() -> str:
    """Generate JavaScript for interactive effects"""
    return """
    <script>
    // ===== PARALLAX SCROLLING =====
    document.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        const parallaxElements = document.querySelectorAll('.parallax-layer');
        
        parallaxElements.forEach((el, index) => {
            const speed = 0.5 + (index * 0.1);
            el.style.transform = `translateY(${scrolled * speed}px)`;
        });
    });
    
    // ===== SCROLL REVEAL =====
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
            }
        });
    }, observerOptions);
    
    document.querySelectorAll('.reveal').forEach(el => {
        observer.observe(el);
    });
    
    // ===== MAGNETIC BUTTON EFFECT =====
    document.querySelectorAll('.magnetic-button').forEach(button => {
        button.addEventListener('mousemove', (e) => {
            const rect = button.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            
            button.style.transform = `translate(${x * 0.3}px, ${y * 0.3}px)`;
        });
        
        button.addEventListener('mouseleave', () => {
            button.style.transform = 'translate(0, 0)';
        });
    });
    
    // ===== 3D TILT EFFECT =====
    document.querySelectorAll('.tilt-card').forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateX = (y - centerY) / 20;
            const rotateY = (centerX - x) / 20;
            
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(20px)`;
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateZ(0)';
        });
    });
    
    // ===== CURSOR GLOW EFFECT =====
    const cursorGlow = document.createElement('div');
    cursorGlow.className = 'cursor-glow';
    document.body.appendChild(cursorGlow);
    
    let mouseX = 0, mouseY = 0;
    let currentX = 0, currentY = 0;
    
    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
    });
    
    function animateCursor() {
        currentX += (mouseX - currentX) * 0.1;
        currentY += (mouseY - currentY) * 0.1;
        
        cursorGlow.style.left = currentX + 'px';
        cursorGlow.style.top = currentY + 'px';
        
        requestAnimationFrame(animateCursor);
    }
    animateCursor();
    
    // ===== PARTICLE GENERATION =====
    function createParticles() {
        const container = document.createElement('div');
        container.className = 'particle-container';
        document.body.appendChild(container);
        
        for (let i = 0; i < 30; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.animationDelay = Math.random() * 15 + 's';
            particle.style.animationDuration = (15 + Math.random() * 10) + 's';
            container.appendChild(particle);
        }
    }
    createParticles();
    
    // ===== TEXT SCRAMBLE EFFECT =====
    class TextScramble {
        constructor(el) {
            this.el = el;
            this.chars = '!<>-_\\/[]{}—=+*^?#________';
            this.update = this.update.bind(this);
        }
        
        setText(newText) {
            const oldText = this.el.innerText;
            const length = Math.max(oldText.length, newText.length);
            const promise = new Promise((resolve) => this.resolve = resolve);
            this.queue = [];
            
            for (let i = 0; i < length; i++) {
                const from = oldText[i] || '';
                const to = newText[i] || '';
                const start = Math.floor(Math.random() * 20);
                const end = start + Math.floor(Math.random() * 20);
                this.queue.push({ from, to, start, end });
            }
            
            cancelAnimationFrame(this.frameRequest);
            this.frame = 0;
            this.update();
            return promise;
        }
        
        update() {
            let output = '';
            let complete = 0;
            
            for (let i = 0, n = this.queue.length; i < n; i++) {
                let { from, to, start, end, char } = this.queue[i];
                
                if (this.frame >= end) {
                    complete++;
                    output += to;
                } else if (this.frame >= start) {
                    if (!char || Math.random() < 0.28) {
                        char = this.randomChar();
                        this.queue[i].char = char;
                    }
                    output += `<span style="color: #60a5fa">${char}</span>`;
                } else {
                    output += from;
                }
            }
            
            this.el.innerHTML = output;
            
            if (complete === this.queue.length) {
                this.resolve();
            } else {
                this.frameRequest = requestAnimationFrame(this.update);
                this.frame++;
            }
        }
        
        randomChar() {
            return this.chars[Math.floor(Math.random() * this.chars.length)];
        }
    }
    
    // Apply scramble to elements with class 'scramble-text'
    document.querySelectorAll('.scramble-text').forEach(el => {
        const fx = new TextScramble(el);
        let counter = 0;
        const phrases = [el.innerText];
        
        el.addEventListener('mouseenter', () => {
            fx.setText(phrases[counter]).then(() => {
                counter = (counter + 1) % phrases.length;
            });
        });
    });
    </script>
    """


def inject_modern_theme():
    """Inject modern CSS and JS into Streamlit"""
    import streamlit as st
    st.markdown(get_modern_css(), unsafe_allow_html=True)
    st.markdown(get_interactive_js(), unsafe_allow_html=True)
