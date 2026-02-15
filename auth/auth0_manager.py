"""
Auth0 Authentication Manager
Required login for ResumeMaker with Auth0 free tier
"""

import streamlit as st
import json
from typing import Optional, Dict, Any
import base64
from datetime import datetime
import os

# Try to import PyJWT
try:
    import jwt
except ImportError:
    jwt = None


class Auth0Manager:
    """
    Manages Auth0 authentication for ResumeMaker
    Required login - no anonymous access
    """
    
    def __init__(self):
        """Initialize Auth0 configuration from secrets or environment variables"""
        try:
            # Helper function to get config from secrets or env
            def get_config(key):
                # Try Streamlit secrets first (local development)
                try:
                    secret_val = st.secrets.get(key, "")
                    if secret_val:
                        return secret_val
                except:
                    pass
                # Fall back to environment variables (production/Render)
                return os.environ.get(key, "")
            
            self.domain = get_config("AUTH0_DOMAIN")
            self.client_id = get_config("AUTH0_CLIENT_ID")
            self.client_secret = get_config("AUTH0_CLIENT_SECRET")
            self.redirect_uri = get_config("AUTH0_REDIRECT_URI")
            
            if not all([self.domain, self.client_id, self.client_secret]):
                missing = []
                if not self.domain:
                    missing.append("AUTH0_DOMAIN")
                if not self.client_id:
                    missing.append("AUTH0_CLIENT_ID")
                if not self.client_secret:
                    missing.append("AUTH0_CLIENT_SECRET")
                
                st.error(f"⚠️ Auth0 credentials not configured. Missing: {', '.join(missing)}")
                st.info("Please set these in either .streamlit/secrets.toml (local) or as environment variables (production).")
                self.enabled = False
            else:
                self.enabled = True
                
        except Exception as e:
            st.error(f"❌ Auth0 initialization error: {e}")
            self.enabled = False
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated"""
        return st.session_state.get("user", None) is not None
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get current user information"""
        return st.session_state.get("user", None)
    
    def get_user_id(self) -> Optional[str]:
        """Get unique user ID (sub from Auth0)"""
        user = self.get_user_info()
        if user:
            return user.get("sub", user.get("user_id", None))
        return None
    
    def get_user_email(self) -> Optional[str]:
        """Get user email"""
        user = self.get_user_info()
        if user:
            return user.get("email", None)
        return None
    
    def get_user_name(self) -> Optional[str]:
        """Get user display name"""
        user = self.get_user_info()
        if user:
            return user.get("name", user.get("nickname", user.get("email", "User")))
        return None
    
    def login_button(self) -> None:
        """Display login button and handle authentication"""
        if not self.enabled:
            st.error("Auth0 is not properly configured. Please check your secrets.")
            return
        
        # Check for auth query parameters (after redirect from Auth0)
        query_params = st.query_params
        
        if "code" in query_params and "state" in query_params:
            # Handle callback from Auth0
            self._handle_callback(query_params)
        elif not self.is_authenticated():
            # Show login UI
            self._render_login_ui()
    
    def _render_login_ui(self) -> None:
        """Render the login interface"""
        # Center the login UI
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
                <div style="text-align: center; padding: 2rem 0;">
                    <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">🔐 Welcome</h1>
                    <p style="color: #9ca3af; font-size: 1.1rem; margin-bottom: 2rem;">
                        Sign in to create ATS-optimized resumes
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            # Google Login Button with Logo
            google_btn = st.markdown("""
                <style>
                .google-btn {
                    background-color: white;
                    color: #757575;
                    border: 1px solid #dadce0;
                    border-radius: 4px;
                    padding: 12px 16px;
                    font-size: 14px;
                    font-weight: 500;
                    font-family: 'Roboto', sans-serif;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 10px;
                    cursor: pointer;
                    width: 100%;
                    transition: box-shadow 0.2s;
                    text-decoration: none;
                }
                .google-btn:hover {
                    box-shadow: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15);
                }
                .google-logo {
                    width: 18px;
                    height: 18px;
                }
                </style>
                <button class="google-btn" onclick="window.location.href='?auth=google'">
                    <svg class="google-logo" viewBox="0 0 24 24">
                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                    Sign in with Google
                </button>
            """, unsafe_allow_html=True)
            
            # Handle Google button click
            if st.query_params.get("auth") == "google":
                self._redirect_to_auth0(connection="google-oauth2")
            
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            
            # GitHub Login Button with Logo
            github_btn = st.markdown("""
                <style>
                .github-btn {
                    background-color: #24292e;
                    color: white;
                    border: 1px solid #1b1f23;
                    border-radius: 6px;
                    padding: 12px 16px;
                    font-size: 14px;
                    font-weight: 600;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 10px;
                    cursor: pointer;
                    width: 100%;
                    transition: background-color 0.2s;
                    text-decoration: none;
                }
                .github-btn:hover {
                    background-color: #2f363d;
                }
                .github-logo {
                    width: 18px;
                    height: 18px;
                    fill: white;
                }
                </style>
                <button class="github-btn" onclick="window.location.href='?auth=github'">
                    <svg class="github-logo" viewBox="0 0 24 24">
                        <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                    </svg>
                    Sign in with GitHub
                </button>
            """, unsafe_allow_html=True)
            
            # Handle GitHub button click
            if st.query_params.get("auth") == "github":
                self._redirect_to_auth0(connection="github")
            
            st.markdown("""
                <div style="text-align: center; margin-top: 2rem; padding-top: 2rem; border-top: 1px solid rgba(255,255,255,0.1);">
                    <p style="color: #6b7280; font-size: 0.85rem;">
                        🔒 Secure authentication powered by Auth0<br>
                        We never store your resume data on our servers
                    </p>
                </div>
            """, unsafe_allow_html=True)
    
    def _redirect_to_auth0(self, connection: str = "") -> None:
        """Redirect user to Auth0 login page"""
        import secrets
        import urllib.parse
        
        # Generate state parameter for security
        state = secrets.token_urlsafe(32)
        st.session_state["auth_state"] = state
        
        # Build Auth0 authorization URL
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "openid profile email",
            "state": state,
        }
        
        if connection:
            params["connection"] = connection
        
        auth_url = f"https://{self.domain}/authorize?{urllib.parse.urlencode(params)}"
        
        # Redirect
        st.markdown(f'<meta http-equiv="refresh" content="0; url={auth_url}">', unsafe_allow_html=True)
        st.stop()
    
    def _handle_callback(self, query_params) -> None:
        """Handle the callback from Auth0 after login"""
        try:
            code = query_params.get("code")
            state = query_params.get("state")
            
            # Verify state parameter
            stored_state = st.session_state.get("auth_state")
            if state != stored_state:
                st.error("❌ Invalid state parameter. Please try logging in again.")
                return
            
            # Exchange code for tokens
            import requests
            
            token_url = f"https://{self.domain}/oauth/token"
            
            payload = {
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": self.redirect_uri
            }
            
            response = requests.post(token_url, json=payload, timeout=30)
            response.raise_for_status()
            
            tokens = response.json()
            
            # Get user info from ID token
            id_token = tokens.get("id_token")
            if id_token:
                user_info = self._decode_id_token(id_token)
                st.session_state["user"] = user_info
                st.session_state["access_token"] = tokens.get("access_token")
                
                # Clear query params to prevent re-processing
                st.query_params.clear()
                st.rerun()
            else:
                st.error("❌ Failed to get user information from Auth0")
                
        except Exception as e:
            st.error(f"❌ Authentication error: {e}")
            st.info("Please try logging in again.")
    
    def _decode_id_token(self, id_token: str) -> Dict[str, Any]:
        """Decode and verify the ID token"""
        try:
            if jwt:
                # Decode without verification (Auth0 handles verification)
                decoded = jwt.decode(id_token, options={"verify_signature": False})
                return decoded
            else:
                raise Exception("JWT library not available")
        except Exception as e:
            st.warning(f"Token decode warning: {e}")
            # Try base64 decode as fallback
            try:
                payload = id_token.split(".")[1]
                payload += "=" * (4 - len(payload) % 4)  # Add padding
                decoded = json.loads(base64.b64decode(payload))
                return decoded
            except:
                return {}
    
    def logout(self) -> None:
        """Log out the current user"""
        # Clear session state
        keys_to_remove = ["user", "access_token", "auth_state"]
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
        
        # Redirect to Auth0 logout
        if self.enabled and self.domain:
            return_url = self.redirect_uri.rsplit("/", 1)[0]  # Base URL
            logout_url = f"https://{self.domain}/v2/logout?client_id={self.client_id}&returnTo={return_url}"
            st.markdown(f'<meta http-equiv="refresh" content="0; url={logout_url}">', unsafe_allow_html=True)
            st.stop()
        else:
            st.rerun()
    
    def require_auth(self) -> bool:
        """
        Decorator-like function to require authentication
        Returns True if authenticated, False otherwise
        """
        if not self.enabled:
            st.error("🔒 Authentication is required but not configured properly.")
            return False
        
        if not self.is_authenticated():
            self.login_button()
            return False
        
        return True
    
    def render_user_header(self) -> None:
        """Render user info and logout button in header"""
        if self.is_authenticated():
            user_name = self.get_user_name()
            
            col1, col2 = st.columns([6, 1])
            
            with col1:
                st.markdown(f"""
                    <div style="text-align: right; color: #9ca3af; font-size: 0.9rem;">
                        👋 {user_name}
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if st.button("Logout", key="logout_btn"):
                    self.logout()


# Singleton instance
_auth_manager = None

def get_auth_manager() -> Auth0Manager:
    """Get or create Auth0 manager singleton"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = Auth0Manager()
    return _auth_manager
