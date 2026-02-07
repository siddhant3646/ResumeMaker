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