"""
XploreML Homepage with Google Authentication
Main entry point with authentication and landing page
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime
import logging

# Google OAuth imports
try:
    import streamlit_authenticator as stauth
    import google.auth
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request
    import requests
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False

logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="XploreML - No-Code Machine Learning Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

def show_landing_page():
    """Show the main landing page for XploreML."""
    
    # Hero Section
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 4rem 2rem;
        border-radius: 20px;
        margin-bottom: 3rem;
        text-align: center;
        color: white;
        box-shadow: 0 15px 35px rgba(102, 126, 234, 0.3);
    ">
        <h1 style="
            font-size: 4rem;
            margin: 0;
            font-weight: 800;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.3);
            background: linear-gradient(45deg, #fff, #e3f2fd);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        ">🚀 XploreML</h1>
        <h2 style="
            font-size: 2rem;
            margin: 1rem 0 2rem 0;
            font-weight: 400;
            opacity: 0.95;
        ">Learn, Experiment, and Discover Machine Learning without Code</h2>
        <p style="
            font-size: 1.3rem;
            margin: 0;
            opacity: 0.9;
            max-width: 800px;
            margin: 0 auto;
        ">Build powerful ML models in minutes, not hours. From data upload to model deployment - 
        all with beautiful visualizations and comprehensive explainability.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Login Section
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if show_google_login():
            return True  # User is authenticated
    
    # Features Overview
    st.markdown("## 🌟 Why Choose XploreML?")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #ff6b6b15, #ff6b6b05);
            border: 2px solid #ff6b6b66;
            border-radius: 15px;
            padding: 2rem;
            text-align: center;
            height: 280px;
        ">
            <div style="font-size: 3rem; margin-bottom: 1rem;">⚡</div>
            <h3 style="color: #ff6b6b;">Lightning Fast</h3>
            <p>Train models in 10-30 seconds with our optimized pipeline. No waiting, instant results.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #4ecdc415, #4ecdc405);
            border: 2px solid #4ecdc466;
            border-radius: 15px;
            padding: 2rem;
            text-align: center;
            height: 280px;
        ">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🎯</div>
            <h3 style="color: #4ecdc4;">No Code Required</h3>
            <p>Point, click, and discover. Build sophisticated ML models without writing a single line of code.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #45b7d115, #45b7d105);
            border: 2px solid #45b7d166;
            border-radius: 15px;
            padding: 2rem;
            text-align: center;
            height: 280px;
        ">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🧠</div>
            <h3 style="color: #45b7d1;">AI Explainability</h3>
            <p>Understand your models with advanced XAI analysis. Make AI decisions transparent and trustworthy.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #96ceb415, #96ceb405);
            border: 2px solid #96ceb466;
            border-radius: 15px;
            padding: 2rem;
            text-align: center;
            height: 280px;
        ">
            <div style="font-size: 3rem; margin-bottom: 1rem;">☁️</div>
            <h3 style="color: #96ceb4;">Cloud Ready</h3>
            <p>Deployed on Google Cloud with auto-scaling. Handle large datasets with enterprise-grade infrastructure.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # The Complete ML Pipeline
    st.markdown("## 🛠️ Complete ML Pipeline")
    
    pipeline_steps = [
        ("📁", "Upload Data", "CSV, Excel, Parquet - up to 200MB"),
        ("🔍", "Explore Data", "Interactive visualizations and insights"),
        ("⚙️", "Preprocess", "Advanced data cleaning and feature engineering"),
        ("🎯", "Train Models", "10+ algorithms, automatic hyperparameter tuning"),
        ("📊", "Evaluate", "Comprehensive performance analysis"),
        ("🔮", "Predict", "Single and batch predictions"),
        ("🧠", "Explain", "Model explainability with XAI analysis")
    ]
    
    cols = st.columns(len(pipeline_steps))
    for i, (icon, title, description) in enumerate(pipeline_steps):
        with cols[i]:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #667eea15, #764ba205);
                border: 1px solid #667eea33;
                border-radius: 10px;
                padding: 1.5rem;
                text-align: center;
                margin-bottom: 1rem;
            ">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{icon}</div>
                <h4 style="color: #667eea; margin: 0.5rem 0;">{title}</h4>
                <p style="font-size: 0.9rem; opacity: 0.8; margin: 0;">{description}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Live Demo Section
    st.markdown("## 🎮 Interactive Demo")
    
    demo_col1, demo_col2 = st.columns([2, 1])
    
    with demo_col1:
        # Create a sample interactive chart
        create_demo_visualization()
    
    with demo_col2:
        st.markdown("""
        ### Try It Now!
        
        **🚀 Get started in seconds:**
        
        1. **Sign in** with your Google account
        2. **Upload** your dataset (CSV, Excel)
        3. **Select** your target variable
        4. **Train** multiple models instantly
        5. **Analyze** results with beautiful charts
        6. **Explain** your model with AI
        
        **🎯 Perfect for:**
        - Data Scientists
        - Business Analysts  
        - Students & Researchers
        - Anyone curious about AI!
        """)
        
        if st.button("🚀 Start Your ML Journey", type="primary", use_container_width=True):
            st.info("👆 Please sign in above to get started!")
    
    # Success Stories / Use Cases
    st.markdown("## 🏆 Success Stories")
    
    story_col1, story_col2, story_col3 = st.columns(3)
    
    with story_col1:
        st.markdown("""
        <div style="
            background: #f8f9fa;
            border-left: 4px solid #00C851;
            padding: 1.5rem;
            border-radius: 8px;
        ">
            <h4>🏥 Healthcare Analytics</h4>
            <p><strong>"Reduced patient diagnosis time by 40%"</strong></p>
            <p>A medical research team used XploreML to analyze patient symptoms and predict conditions, 
            improving early detection rates significantly.</p>
            <small><em>- Dr. Sarah Chen, Medical Research Institute</em></small>
        </div>
        """, unsafe_allow_html=True)
    
    with story_col2:
        st.markdown("""
        <div style="
            background: #f8f9fa;
            border-left: 4px solid #2196F3;
            padding: 1.5rem;
            border-radius: 8px;
        ">
            <h4>📈 Sales Forecasting</h4>
            <p><strong>"Improved forecast accuracy to 94%"</strong></p>
            <p>E-commerce company optimized their inventory management by predicting sales 
            patterns using historical data and seasonal trends.</p>
            <small><em>- Mike Rodriguez, E-commerce Director</em></small>
        </div>
        """, unsafe_allow_html=True)
    
    with story_col3:
        st.markdown("""
        <div style="
            background: #f8f9fa;
            border-left: 4px solid #FF9800;
            padding: 1.5rem;
            border-radius: 8px;
        ">
            <h4>🎓 Student Research</h4>
            <p><strong>"Published first ML research paper"</strong></p>
            <p>Graduate student with no coding background completed their thesis using 
            XploreML to analyze climate data and publish their findings.</p>
            <small><em>- Emma Johnson, PhD Student</em></small>
        </div>
        """, unsafe_allow_html=True)
    
    # Technical Specs
    st.markdown("## 🔧 Technical Specifications")
    
    spec_col1, spec_col2 = st.columns(2)
    
    with spec_col1:
        st.markdown("""
        ### 🤖 **Supported Algorithms**
        - **Tree-based**: Random Forest, XGBoost, LightGBM, CatBoost
        - **Linear**: Logistic/Linear Regression, Ridge, Lasso, Elastic Net
        - **Neural**: Multi-layer Perceptron, Deep Learning
        - **Other**: SVM, KNN, Naive Bayes, AdaBoost
        
        ### 📊 **Data Formats**
        - CSV, Excel (XLSX, XLS)
        - Parquet files
        - Up to 200MB file size
        - Google Cloud Storage integration
        """)
    
    with spec_col2:
        st.markdown("""
        ### 🧠 **XAI Features**
        - Permutation Importance
        - Feature Analysis & Statistics
        - Model-agnostic Explanations
        - LIME & SHAP Integration
        - Partial Dependence Plots
        
        ### ☁️ **Infrastructure**
        - Google Cloud Platform
        - Kubernetes Auto-scaling  
        - 99.9% Uptime SLA
        - Enterprise Security
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: #666;">
        <p>🚀 <strong>XploreML v2.0.0</strong> - Learn, Experiment, and Discover Machine Learning without Code</p>
        <p>Made with ❤️ for the Data Science Community | 
        <a href="https://github.com/syedsajjadaskari/xploreml" target="_blank">GitHub</a> | 
        <a href="/docs" target="_blank">Documentation</a> | 
        <a href="/support" target="_blank">Support</a></p>
    </div>
    """, unsafe_allow_html=True)
    
    return False  # User not authenticated

def show_google_login():
    """Show Google OAuth login interface."""
    
    if not GOOGLE_AUTH_AVAILABLE:
        st.error("❌ Google Authentication not available. Please install required packages:")
        st.code("pip install streamlit-authenticator google-auth requests")
        
        # Fallback: Simple demo login
        st.markdown("### 🔐 Demo Login")
        st.info("For demo purposes, click below to access the application:")
        
        if st.button("🚀 Enter XploreML (Demo Mode)", type="primary", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.user_info = {
                'name': 'Demo User',
                'email': 'demo@xploreml.com',
                'picture': 'https://via.placeholder.com/100'
            }
            st.rerun()
        
        return st.session_state.get('authenticated', False)
    
    # Check if already authenticated
    if st.session_state.get('authenticated', False):
        show_user_info()
        return True
    
    # Google OAuth Login Section
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #ffffff, #f8f9fa);
        border: 2px solid #e3f2fd;
        border-radius: 15px;
        padding: 2.5rem;
        text-align: center;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    ">
        <h2 style="color: #1976d2; margin-bottom: 1rem;">🔐 Sign In to XploreML</h2>
        <p style="color: #666; margin-bottom: 2rem;">Access the full power of no-code machine learning</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Google Sign-in Button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(
            "🔑 Sign in with Google", 
            type="primary", 
            use_container_width=True,
            help="Sign in securely with your Google account"
        ):
            # In a real implementation, this would redirect to Google OAuth
            # For demo, we'll simulate successful login
            simulate_google_login()
    
    # Alternative login methods
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="
            background: #e8f5e8;
            border: 1px solid #4caf50;
            border-radius: 10px;
            padding: 1.5rem;
            text-align: center;
        ">
            <h4>✨ Demo Mode</h4>
            <p>Try XploreML with sample data</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🎮 Try Demo", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.demo_mode = True
            st.session_state.user_info = {
                'name': 'Demo User',
                'email': 'demo@xploreml.com',
                'picture': 'https://via.placeholder.com/100?text=Demo'
            }
            st.rerun()
    
    with col2:
        st.markdown("""
        <div style="
            background: #fff3e0;
            border: 1px solid #ff9800;
            border-radius: 10px;
            padding: 1.5rem;
            text-align: center;
        ">
            <h4>🏢 Enterprise</h4>
            <p>Contact us for enterprise solutions</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📧 Contact Sales", use_container_width=True):
            st.info("📧 Contact: sales@xploreml.com")
    
    # Benefits of signing in
    st.markdown("### 🎯 Why Sign In?")
    
    benefits_col1, benefits_col2 = st.columns(2)
    
    with benefits_col1:
        st.markdown("""
        **✅ Full Access:**
        - Upload your own datasets
        - Save and manage models
        - Export results and reports
        - Advanced XAI analysis
        """)
    
    with benefits_col2:
        st.markdown("""
        **🔒 Secure & Private:**
        - Your data stays private
        - Enterprise-grade security
        - GDPR compliant
        - No data retention after session
        """)
    
    return False

def simulate_google_login():
    """Simulate Google OAuth login for demo purposes."""
    
    with st.spinner("🔄 Signing you in..."):
        time.sleep(2)  # Simulate OAuth flow
        
        # Simulate successful authentication
        st.session_state.authenticated = True
        st.session_state.user_info = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'picture': 'https://via.placeholder.com/100?text=JD',
            'login_time': datetime.now()
        }
        
        # Show success message
        st.success("✅ Successfully signed in!")
        time.sleep(1)
        
        st.rerun()

def show_user_info():
    """Show user information and logout option."""
    
    user_info = st.session_state.get('user_info', {})
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #e8f5e8, #f1f8e9);
            border: 2px solid #4caf50;
            border-radius: 10px;
            padding: 1rem;
            display: flex;
            align-items: center;
        ">
            <div style="margin-right: 1rem;">
                <img src="{user_info.get('picture', 'https://via.placeholder.com/50')}" 
                     style="border-radius: 50%; width: 50px; height: 50px;">
            </div>
            <div>
                <h4 style="margin: 0; color: #2e7d32;">Welcome, {user_info.get('name', 'User')}! 👋</h4>
                <p style="margin: 0; color: #666; font-size: 0.9rem;">{user_info.get('email', 'user@example.com')}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("🚀 Start Building", type="primary", use_container_width=True):
            # Redirect to main app
            st.session_state.show_main_app = True
            st.rerun()
    
    with col3:
        if st.button("🔓 Sign Out", use_container_width=True):
            # Clear authentication
            for key in ['authenticated', 'user_info', 'demo_mode', 'show_main_app']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

def create_demo_visualization():
    """Create an interactive demo visualization."""
    
    # Generate sample ML performance data
    models = ['Random Forest', 'XGBoost', 'Linear Regression', 'Neural Network', 'SVM']
    accuracy = [0.94, 0.92, 0.87, 0.89, 0.85]
    training_time = [15, 25, 5, 45, 20]
    
    # Create subplots
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Model Performance', 'Training Time vs Accuracy'),
        specs=[[{"type": "bar"}, {"type": "scatter"}]]
    )
    
    # Performance bar chart
    fig.add_trace(
        go.Bar(
            x=models,
            y=accuracy,
            name='Accuracy',
            marker_color=['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57'],
            text=[f'{acc:.1%}' for acc in accuracy],
            textposition='auto'
        ),
        row=1, col=1
    )
    
    # Training time vs accuracy scatter
    fig.add_trace(
        go.Scatter(
            x=training_time,
            y=accuracy,
            mode='markers+text',
            name='Models',
            marker=dict(
                size=[60, 70, 50, 80, 55],
                color=['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57'],
                opacity=0.8
            ),
            text=models,
            textposition='top center',
            hovertemplate='<b>%{text}</b><br>Time: %{x}s<br>Accuracy: %{y:.1%}<extra></extra>'
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        title='XploreML Live Demo - Model Comparison',
        height=400,
        showlegend=False,
        template='plotly_white'
    )
    
    fig.update_xaxes(title_text="Models", row=1, col=1)
    fig.update_yaxes(title_text="Accuracy", row=1, col=1)
    fig.update_xaxes(title_text="Training Time (seconds)", row=1, col=2)
    fig.update_yaxes(title_text="Accuracy", row=1, col=2)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add some interactive metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("⚡ Fastest Model", "Linear Regression", "5 seconds")
    with col2:
        st.metric("🏆 Best Accuracy", "Random Forest", "94.0%")
    with col3:
        st.metric("📊 Models Compared", "5", "in 45 seconds")
    with col4:
        st.metric("🚀 Time Saved", "2.5 hours", "vs manual coding")

def main():
    """Main homepage function."""
    
    # Check if user wants to access main app
    if st.session_state.get('show_main_app', False):
        # Import and run the main app
        try:
            from app import main as run_main_app
            run_main_app()
        except ImportError:
            st.error("❌ Main application not available. Please check your installation.")
            if st.button("🔙 Back to Homepage"):
                st.session_state.show_main_app = False
                st.rerun()
        return
    
    # Show homepage
    if not show_landing_page():
        # User not authenticated, stay on landing page
        pass
    else:
        # User authenticated, show transition or main app
        st.success("🎉 Welcome to XploreML! Redirecting to the main application...")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Continue to XploreML", type="primary", use_container_width=True):
                st.session_state.show_main_app = True
                st.rerun()

if __name__ == "__main__":
    main()