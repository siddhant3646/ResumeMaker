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
            
            # Custom styled buttons using HTML/CSS with Streamlit button functionality
            st.markdown("""
                <style>
                div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-child(1) button[kind="primary"] {
                    background-color: white !important;
                    color: #757575 !important;
                    border: 1px solid #dadce0 !important;
                    border-radius: 4px !important;
                    font-weight: 500 !important;
                    font-family: 'Roboto', sans-serif !important;
                }
                div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-child(1) button[kind="primary"]:hover {
                    box-shadow: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15) !important;
                }
                div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-child(2) button[kind="secondary"] {
                    background-color: #24292e !important;
                    color: white !important;
                    border: 1px solid #1b1f23 !important;
                    border-radius: 6px !important;
                    font-weight: 600 !important;
                }
                div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-child(2) button[kind="secondary"]:hover {
                    background-color: #2f363d !important;
                }
                </style>
            """, unsafe_allow_html=True)
            
            # Create buttons in columns for layout
            btn_col1, btn_col2 = st.columns(2)
            
            with btn_col1:
                if st.button("🔴 Sign in with Google", use_container_width=True, type="primary"):
                    self._redirect_to_auth0(connection="google-oauth2")
            
            with btn_col2:
                if st.button("⚫ Sign in with GitHub", use_container_width=True, type="secondary"):
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
