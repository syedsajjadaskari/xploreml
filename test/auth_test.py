import streamlit as st
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
import json
import tempfile

def load_credentials_from_secrets():
    """Load Google credentials from Streamlit secrets"""
    try:
        # Get credentials from secrets
        google_creds = st.secrets["google"]
        
        # Create credentials dict
        creds_dict = {
            "type": google_creds.get("type", "service_account"),
            "project_id": google_creds["project_id"],
            "private_key_id": google_creds["private_key_id"],
            "private_key": google_creds["private_key"].replace('\\n', '\n'),
            "client_email": google_creds["client_email"],
            "client_id": google_creds["client_id"],
            "auth_uri": google_creds.get("auth_uri", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": google_creds.get("token_uri", "https://oauth2.googleapis.com/token"),
            "auth_provider_x509_cert_url": google_creds.get("auth_provider_x509_cert_url"),
            "client_x509_cert_url": google_creds.get("client_x509_cert_url")
        }
        
        # For OAuth flow (if using web application credentials)
        if "client_secret" in google_creds:
            oauth_creds = {
                "web": {
                    "client_id": google_creds["client_id"],
                    "client_secret": google_creds["client_secret"],
                    "auth_uri": google_creds.get("auth_uri", "https://accounts.google.com/o/oauth2/auth"),
                    "token_uri": google_creds.get("token_uri", "https://oauth2.googleapis.com/token"),
                    "redirect_uris": google_creds.get("redirect_uris", ["urn:ietf:wg:oauth:2.0:oob"])
                }
            }
            return oauth_creds, creds_dict
            
        return None, creds_dict
        
    except Exception as e:
        st.error(f"Error loading credentials from secrets: {str(e)}")
        return None, None

def check_google_login():
    """Check if Google login is working properly"""
    
    st.title("Google Login Status Checker")
    
    # Configuration check
    st.header("📋 Configuration Check")
    
    config_status = {}
    
    # Check for secrets
    try:
        google_secrets = st.secrets["google"]
        config_status['Secrets Configuration'] = "✅ Found"
        
        # Check required fields
        required_fields = ["client_id", "project_id"]
        for field in required_fields:
            if field in google_secrets:
                config_status[f'{field}'] = "✅ Present"
            else:
                config_status[f'{field}'] = "❌ Missing"
                
    except Exception:
        config_status['Secrets Configuration'] = "❌ Missing or Invalid"
    
    # Check for token file
    if os.path.exists('token.json'):
        config_status['Token File'] = "✅ Found"
    else:
        config_status['Token File'] = "❌ Missing"
    
    # Display configuration status
    for item, status in config_status.items():
        st.write(f"{item}: {status}")
    
    st.divider()
    
    # Login test section
    st.header("🔐 Login Test")
    
    if st.button("Test Google Login", type="primary"):
        try:
            # Load credentials from secrets
            oauth_creds, service_creds = load_credentials_from_secrets()
            
            if not oauth_creds and not service_creds:
                st.error("❌ Could not load credentials from secrets")
                return
            
            creds = None
            
            # Load existing token
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json')
            
            # If no valid credentials, start auth flow
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    st.info("Refreshing expired token...")
                    creds.refresh(Request())
                    st.success("Token refreshed successfully!")
                    
                    # Save refreshed token
                    with open('token.json', 'w') as token:
                        token.write(creds.to_json())
                else:
                    if oauth_creds:
                        st.warning("No valid credentials found. Please run authentication flow.")
                        
                        # Create temporary credentials file
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
                            json.dump(oauth_creds, tmp_file)
                            tmp_creds_path = tmp_file.name
                        
                        try:
                            flow = Flow.from_client_secrets_file(
                                tmp_creds_path,
                                scopes=['https://www.googleapis.com/auth/userinfo.profile',
                                        'https://www.googleapis.com/auth/userinfo.email']
                            )
                            flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
                            
                            auth_url, _ = flow.authorization_url(prompt='consent')
                            st.write("Please visit this URL to authorize the application:")
                            st.code(auth_url)
                            
                            auth_code = st.text_input("Enter the authorization code:")
                            
                            if auth_code:
                                flow.fetch_token(code=auth_code)
                                creds = flow.credentials
                                
                                # Save credentials
                                with open('token.json', 'w') as token:
                                    token.write(creds.to_json())
                                st.success("Authentication successful!")
                                st.experimental_rerun()
                        finally:
                            # Clean up temporary file
                            os.unlink(tmp_creds_path)
                    else:
                        st.error("OAuth credentials not found in secrets. Please add client_secret to your secrets.toml")
            
            # Test API call
            if creds and creds.valid:
                st.success("✅ Google Login is working!")
                
                # Test with a simple API call
                service = build('oauth2', 'v2', credentials=creds)
                user_info = service.userinfo().get().execute()
                
                st.subheader("User Information:")
                st.json(user_info)
                
                # Additional checks
                st.subheader("Token Details:")
                token_info = {
                    "Valid": creds.valid,
                    "Expired": creds.expired if hasattr(creds, 'expired') else False,
                    "Has Refresh Token": bool(creds.refresh_token)
                }
                st.json(token_info)
                
            else:
                st.error("❌ Google Login is not working properly")
                
        except Exception as e:
            st.error(f"❌ Login test failed: {str(e)}")
            st.write("**Error Details:**")
            st.code(str(e))
    
    st.divider()
    
    # Display secrets structure help
    st.header("📝 Secrets Configuration Help")
    
    with st.expander("Expected secrets.toml structure"):
        st.code('''
[google]
type = "web"  # or "service_account"
project_id = "your-project-id"
client_id = "your-client-id.googleusercontent.com"
client_secret = "your-client-secret"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"

# For service account (alternative):
# private_key_id = "your-private-key-id"
# private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
# client_email = "your-service-account@your-project.iam.gserviceaccount.com"
        ''')
    
    # Manual token validation
    st.header("🔍 Manual Token Validation")
    
    if st.button("Validate Current Token"):
        try:
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json')
                
                # Check token validity
                if creds.valid:
                    st.success("✅ Token is valid")
                    
                    # Test with userinfo API
                    headers = {'Authorization': f'Bearer {creds.token}'}
                    response = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', headers=headers)
                    
                    if response.status_code == 200:
                        st.success("✅ API call successful")
                        st.json(response.json())
                    else:
                        st.error(f"❌ API call failed: {response.status_code}")
                        st.write(response.text)
                        
                elif creds.expired and creds.refresh_token:
                    st.warning("Token expired but can be refreshed")
                    if st.button("Refresh Token"):
                        creds.refresh(Request())
                        with open('token.json', 'w') as token:
                            token.write(creds.to_json())
                        st.success("Token refreshed!")
                        st.experimental_rerun()
                else:
                    st.error("❌ Token is invalid")
            else:
                st.error("❌ No token file found")
                
        except Exception as e:
            st.error(f"❌ Token validation failed: {str(e)}")
    
    # Reset option
    st.divider()
    st.header("🔄 Reset Authentication")
    
    if st.button("Clear Saved Tokens", type="secondary"):
        try:
            if os.path.exists('token.json'):
                os.remove('token.json')
                st.success("Token file removed. Please re-authenticate.")
                st.experimental_rerun()
            else:
                st.info("No token file to remove")
        except Exception as e:
            st.error(f"Error removing token file: {str(e)}")

if __name__ == "__main__":
    check_google_login()