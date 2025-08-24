"""
Authentication Utilities for XploreML
Handles Google OAuth and user session management
"""

import streamlit as st
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import hashlib
import secrets

# Google OAuth imports
try:
    import google.auth
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request
    import requests
    from google.auth.exceptions import RefreshError
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False
    st.warning("⚠️ Google Auth libraries not available. Install with: pip install google-auth google-auth-requests")

logger = logging.getLogger(__name__)

class GoogleAuthenticator:
    """Handle Google OAuth authentication for XploreML."""
    
    def __init__(self):
        self.client_id = self._get_client_id()
        self.client_secret = self._get_client_secret()
        self.redirect_uri = self._get_redirect_uri()
        
    def _get_client_id(self) -> str:
        """Get Google OAuth client ID from secrets or environment."""
        try:
            # Try Streamlit secrets first
            if hasattr(st, 'secrets') and 'GOOGLE_CLIENT_ID' in st.secrets:
                return st.secrets['GOOGLE_CLIENT_ID']
            
            # Try environment variable
            import os
            client_id = os.getenv('GOOGLE_CLIENT_ID')
            if client_id:
                return client_id
            
            # Demo client ID (replace with your actual client ID)
            return "your-google-client-id.apps.googleusercontent.com"
            
        except Exception as e:
            logger.warning(f"Could not get Google Client ID: {e}")
            return "demo-client-id"
    
    def _get_client_secret(self) -> str:
        """Get Google OAuth client secret from secrets or environment."""
        try:
            # Try Streamlit secrets first
            if hasattr(st, 'secrets') and 'GOOGLE_CLIENT_SECRET' in st.secrets:
                return st.secrets['GOOGLE_CLIENT_SECRET']
            
            # Try environment variable
            import os
            client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
            if client_secret:
                return client_secret
            
            # Demo secret (replace with your actual secret)
            return "your-google-client-secret"
            
        except Exception as e:
            logger.warning(f"Could not get Google Client Secret: {e}")
            return "demo-client-secret"
    
    def _get_redirect_uri(self) -> str:
        """Get OAuth redirect URI."""
        # For local development
        if 'localhost' in st.session_state.get('current_url', 'localhost'):
            return "http://localhost:8501/auth/callback"
        
        # For production (replace with your domain)
        return "https://your-app-domain.com/auth/callback"
    
    def get_authorization_url(self) -> str:
        """Generate Google OAuth authorization URL."""
        try:
            # Generate state parameter for security
            state = secrets.token_urlsafe(32)
            st.session_state.oauth_state = state
            
            # OAuth parameters
            params = {
                'client_id': self.client_id,
                'redirect_uri': self.redirect_uri,
                'scope': 'openid email profile',
                'response_type': 'code',
                'state': state,
                'access_type': 'offline',
                'prompt': 'consent'
            }
            
            # Build authorization URL
            base_url = 'https://accounts.google.com/o/oauth2/v2/auth'
            param_string = '&'.join([f'{k}={v}' for k, v in params.items()])
            
            return f"{base_url}?{param_string}"
            
        except Exception as e:
            logger.error(f"Error generating authorization URL: {e}")
            return None
    
    def exchange_code_for_token(self, authorization_code: str, state: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token."""
        try:
            # Verify state parameter
            if state != st.session_state.get('oauth_state'):
                logger.error("OAuth state mismatch - possible CSRF attack")
                return None
            
            # Token exchange parameters
            token_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': authorization_code,
                'grant_type': 'authorization_code',
                'redirect_uri': self.redirect_uri,
            }
            
            # Exchange code for token
            token_url = 'https://oauth2.googleapis.com/token'
            response = requests.post(token_url, data=token_data)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            return None
    
    def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from Google using access token."""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get user info: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None

class SessionManager:
    """Manage user sessions and authentication state."""
    
    def __init__(self):
        self.session_timeout = 24  # hours
    
    def create_session(self, user_info: Dict[str, Any], tokens: Dict[str, Any] = None) -> str:
        """Create a new user session."""
        try:
            session_id = self._generate_session_id()
            
            session_data = {
                'session_id': session_id,
                'user_info': user_info,
                'tokens': tokens or {},
                'created_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat(),
                'authenticated': True,
                'login_method': 'google_oauth'
            }
            
            # Store in session state
            st.session_state.update(session_data)
            st.session_state.authenticated = True
            
            logger.info(f"Session created for user: {user_info.get('email', 'unknown')}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        timestamp = str(datetime.now().timestamp())
        random_part = secrets.token_hex(16)
        combined = f"{timestamp}_{random_part}"
        return hashlib.sha256(combined.encode()).hexdigest()[:32]
    
    def is_session_valid(self) -> bool:
        """Check if current session is valid."""
        try:
            if not st.session_state.get('authenticated', False):
                return False
            
            # Check session timeout
            created_at = st.session_state.get('created_at')
            if created_at:
                created_time = datetime.fromisoformat(created_at)
                if datetime.now() - created_time > timedelta(hours=self.session_timeout):
                    logger.info("Session expired")
                    self.destroy_session()
                    return False
            
            # Update last activity
            st.session_state.last_activity = datetime.now().isoformat()
            return True
            
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return False
    
    def destroy_session(self):
        """Destroy current session."""
        try:
            user_email = st.session_state.get('user_info', {}).get('email', 'unknown')
            
            # Clear authentication-related session state
            auth_keys = [
                'authenticated', 'user_info', 'tokens', 'session_id',
                'created_at', 'last_activity', 'oauth_state', 'login_method',
                'demo_mode', 'show_main_app'
            ]
            
            for key in auth_keys:
                if key in st.session_state:
                    del st.session_state[key]
            
            logger.info(f"Session destroyed for user: {user_email}")
            
        except Exception as e:
            logger.error(f"Error destroying session: {e}")
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get current user information."""
        return st.session_state.get('user_info', {})
    
    def is_demo_mode(self) -> bool:
        """Check if running in demo mode."""
        return st.session_state.get('demo_mode', False)
    
    def update_user_activity(self):
        """Update user's last activity timestamp."""
        st.session_state.last_activity = datetime.now().isoformat()

class AuthenticationRequired:
    """Decorator/context manager to require authentication."""
    
    def __init__(self, redirect_to_login: bool = True):
        self.redirect_to_login = redirect_to_login
        self.session_manager = SessionManager()
    
    def __call__(self, func):
        """Decorator to require authentication for a function."""
        def wrapper(*args, **kwargs):
            if not self.session_manager.is_session_valid():
                if self.redirect_to_login:
                    st.error("🔐 Authentication required. Please sign in to continue.")
                    st.stop()
                else:
                    return None
            
            # Update activity and proceed
            self.session_manager.update_user_activity()
            return func(*args, **kwargs)
        
        return wrapper

def init_authentication():
    """Initialize authentication system."""
    
    # Initialize session manager
    if 'session_manager' not in st.session_state:
        st.session_state.session_manager = SessionManager()
    
    # Initialize Google authenticator if available
    if GOOGLE_AUTH_AVAILABLE and 'google_auth' not in st.session_state:
        st.session_state.google_auth = GoogleAuthenticator()

def show_google_signin_button():
    """Show Google Sign-In button with proper OAuth flow."""
    
    if not GOOGLE_AUTH_AVAILABLE:
        return show_demo_signin_button()
    
    google_auth = st.session_state.get('google_auth')
    if not google_auth:
        return show_demo_signin_button()
    
    # Custom CSS for Google Sign-In button
    st.markdown("""
    <style>
    .google-signin-btn {
        display: inline-flex;
        align-items: center;
        background-color: #4285f4;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 12px 16px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        text-decoration: none;
        transition: background-color 0.3s;
        width: 100%;
        justify-content: center;
        margin: 10px 0;
    }
    .google-signin-btn:hover {
        background-color: #357ae8;
    }
    .google-signin-btn img {
        margin-right: 8px;
        width: 18px;
        height: 18px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Get authorization URL
    auth_url = google_auth.get_authorization_url()
    
    if auth_url:
        st.markdown(f"""
        <a href="{auth_url}" class="google-signin-btn" target="_self">
            <img src="https://developers.google.com/identity/images/g-logo.png" alt="Google">
            Sign in with Google
        </a>
        """, unsafe_allow_html=True)
        
        st.markdown("*Secure authentication via Google OAuth 2.0*")
        
        return True
    else:
        return show_demo_signin_button()

def show_demo_signin_button():
    """Show demo sign-in button when Google OAuth is not available."""
    
    st.info("🔧 **Demo Mode**: Google OAuth not configured. Using demo authentication.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Demo User Login", type="primary", use_container_width=True):
            session_manager = SessionManager()
            demo_user = {
                'name': 'Demo User',
                'email': 'demo@xploreml.com',
                'picture': 'https://via.placeholder.com/100?text=Demo',
                'verified_email': True,
                'locale': 'en'
            }
            
            session_id = session_manager.create_session(demo_user)
            st.session_state.demo_mode = True
            
            if session_id:
                st.success("✅ Demo login successful!")
                return True
    
    with col2:
        if st.button("👤 Guest Access", use_container_width=True):
            session_manager = SessionManager()
            guest_user = {
                'name': 'Guest User',
                'email': 'guest@xploreml.com',
                'picture': 'https://via.placeholder.com/100?text=Guest',
                'verified_email': False,
                'locale': 'en'
            }
            
            session_id = session_manager.create_session(guest_user)
            st.session_state.demo_mode = True
            st.session_state.guest_mode = True
            
            if session_id:
                st.info("ℹ️ Guest access granted with limited features.")
                return True
    
    return False

def handle_oauth_callback():
    """Handle OAuth callback after user returns from Google."""
    
    # Check if we have the authorization code in query parameters
    query_params = st.experimental_get_query_params()
    
    if 'code' in query_params and 'state' in query_params:
        code = query_params['code'][0]
        state = query_params['state'][0]
        
        google_auth = st.session_state.get('google_auth')
        if not google_auth:
            st.error("❌ Authentication system not initialized")
            return False
        
        # Exchange code for tokens
        with st.spinner("🔄 Completing sign-in..."):
            tokens = google_auth.exchange_code_for_token(code, state)
            
            if tokens and 'access_token' in tokens:
                # Get user information
                user_info = google_auth.get_user_info(tokens['access_token'])
                
                if user_info:
                    # Create session
                    session_manager = SessionManager()
                    session_id = session_manager.create_session(user_info, tokens)
                    
                    if session_id:
                        st.success(f"✅ Welcome, {user_info.get('name', 'User')}!")
                        
                        # Clear query parameters
                        st.experimental_set_query_params()
                        
                        # Redirect to main app
                        st.session_state.show_main_app = True
                        st.rerun()
                        return True
                    else:
                        st.error("❌ Failed to create session")
                else:
                    st.error("❌ Failed to get user information")
            else:
                st.error("❌ Authentication failed")
    
    elif 'error' in query_params:
        error = query_params['error'][0]
        st.error(f"❌ Authentication error: {error}")
    
    return False

def show_user_profile():
    """Show user profile information."""
    
    session_manager = SessionManager()
    user_info = session_manager.get_user_info()
    
    if not user_info:
        st.error("❌ No user information available")
        return
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # User avatar
        picture_url = user_info.get('picture', 'https://via.placeholder.com/100?text=User')
        st.image(picture_url, width=100)
    
    with col2:
        # User details
        st.markdown(f"**Name:** {user_info.get('name', 'Unknown')}")
        st.markdown(f"**Email:** {user_info.get('email', 'Unknown')}")
        
        if user_info.get('verified_email'):
            st.markdown("**Status:** ✅ Verified")
        else:
            st.markdown("**Status:** ⚠️ Unverified")
        
        # Session info
        created_at = st.session_state.get('created_at')
        if created_at:
            created_time = datetime.fromisoformat(created_at)
            st.markdown(f"**Signed in:** {created_time.strftime('%Y-%m-%d %H:%M')}")
        
        # Demo mode indicator
        if session_manager.is_demo_mode():
            st.markdown("**Mode:** 🎮 Demo")
        elif st.session_state.get('guest_mode'):
            st.markdown("**Mode:** 👤 Guest")
        else:
            st.markdown("**Mode:** 🔐 Authenticated")

def show_authentication_status():
    """Show current authentication status in sidebar."""
    
    session_manager = SessionManager()
    
    if session_manager.is_session_valid():
        user_info = session_manager.get_user_info()
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 👤 Account")
        
        # User info
        name = user_info.get('name', 'User')
        email = user_info.get('email', 'user@example.com')
        
        st.sidebar.markdown(f"**{name}**")
        st.sidebar.markdown(f"*{email}*")
        
        # Mode indicator
        if session_manager.is_demo_mode():
            st.sidebar.markdown("🎮 **Demo Mode**")
        elif st.session_state.get('guest_mode'):
            st.sidebar.markdown("👤 **Guest Mode**")
        else:
            st.sidebar.markdown("🔐 **Authenticated**")
        
        # Sign out button
        if st.sidebar.button("🔓 Sign Out", use_container_width=True):
            session_manager.destroy_session()
            st.rerun()
    
    else:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🔐 Authentication")
        st.sidebar.markdown("*Not signed in*")
        
        if st.sidebar.button("🔑 Sign In", use_container_width=True):
            # Redirect to login page
            st.session_state.show_main_app = False
            st.rerun()

def require_authentication(func):
    """Decorator to require authentication for a function."""
    def wrapper(*args, **kwargs):
        session_manager = SessionManager()
        
        if not session_manager.is_session_valid():
            st.error("🔐 **Authentication Required**")
            st.info("Please sign in to access this feature.")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🔑 Go to Sign In", type="primary", use_container_width=True):
                    st.session_state.show_main_app = False
                    st.rerun()
            
            st.stop()
        
        # Update activity and proceed
        session_manager.update_user_activity()
        return func(*args, **kwargs)
    
    return wrapper

def get_user_permissions() -> Dict[str, bool]:
    """Get current user's permissions based on authentication level."""
    
    session_manager = SessionManager()
    
    if not session_manager.is_session_valid():
        return {
            'upload_data': False,
            'save_models': False,
            'export_results': False,
            'advanced_features': False,
            'unlimited_usage': False
        }
    
    # Guest mode permissions
    if st.session_state.get('guest_mode'):
        return {
            'upload_data': False,
            'save_models': False,
            'export_results': False,
            'advanced_features': False,
            'unlimited_usage': False
        }
    
    # Demo mode permissions
    if session_manager.is_demo_mode():
        return {
            'upload_data': True,
            'save_models': False,
            'export_results': True,
            'advanced_features': True,
            'unlimited_usage': False
        }
    
    # Full authenticated user permissions
    return {
        'upload_data': True,
        'save_models': True,
        'export_results': True,
        'advanced_features': True,
        'unlimited_usage': True
    }

def check_feature_access(feature: str) -> bool:
    """Check if current user has access to a specific feature."""
    permissions = get_user_permissions()
    return permissions.get(feature, False)

# Initialize authentication system
init_authentication()