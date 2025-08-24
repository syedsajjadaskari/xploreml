"""
XploreML Homepage with Google Authentication
Welcome page and authentication flow
"""

import streamlit as st
from utils.auth_handler import GoogleAuthHandler

def show_homepage():
    """Display XploreML homepage with authentication."""
    
    # Initialize auth handler
    auth_handler = GoogleAuthHandler()
    
    # Check if already authenticated
    if auth_handler.is_authenticated():
        show_authenticated_homepage(auth_handler)
    else:
        show_login_page(auth_handler)

def show_login_page(auth_handler):
    """Show login page with Google authentication."""
    
    # Hero section
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 4rem 2rem;
        border-radius: 20px;
        margin-bottom: 3rem;
        text-align: center;
        color: white;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
    ">
        <h1 style="
            font-size: 4rem;
            margin: 0;
            font-weight: 700;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            margin-bottom: 1rem;
        ">🚀 XploreML</h1>
        <h2 style="
            font-size: 2rem;
            margin: 0;
            font-weight: 300;
            opacity: 0.95;
            margin-bottom: 1rem;
        ">Learn, Experiment, and Discover</h2>
        <p style="
            font-size: 1.2rem;
            margin: 0;
            opacity: 0.9;
            max-width: 600px;
            margin: 0 auto;
        ">Machine Learning without Code - Build, analyze, and deploy ML models with zero coding required</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main content in columns
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Welcome message
        st.markdown("### 🎯 Welcome to XploreML")
        st.markdown("""
        Ready to dive into machine learning? Sign in with your Google account to start exploring, 
        training, and deploying ML models in minutes.
        """)
        
        st.markdown("---")
        
        # Authentication section
        st.markdown("### 🔐 Sign In")
        
        # Google login
        auth_handler.login_with_google()
        
        st.markdown("---")
        
        # Features preview
        st.markdown("### ✨ What You'll Get")
        
        features = [
            ("🔥", "Lightning Fast Training", "Train models in 10-30 seconds with optimized algorithms"),
            ("📊", "Interactive Data Explorer", "Visualize and understand your data without code"),
            ("🧠", "AI Model Explainability", "Understand how your models make decisions"),
            ("🤖", "Multiple ML Algorithms", "Classification, regression, and more"),
            ("☁️", "Cloud-Ready Deployment", "Deploy models with Kubernetes integration"),
            ("🎯", "No Code Required", "Build professional ML pipelines visually")
        ]
        
        for icon, title, description in features:
            st.markdown(f"""
            <div style="
                display: flex;
                align-items: center;
                padding: 1rem;
                margin: 0.5rem 0;
                background: #f8f9fa;
                border-radius: 10px;
                border-left: 4px solid #667eea;
            ">
                <div style="font-size: 2rem; margin-right: 1rem;">{icon}</div>
                <div>
                    <strong>{title}</strong><br>
                    <span style="color: #666;">{description}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

def show_authenticated_homepage(auth_handler):
    """Show authenticated homepage with user dashboard."""
    
    user_info = auth_handler.get_user_info()
    
    # Welcome header
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #00C851 0%, #007E33 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    ">
        <h1 style="
            font-size: 2.5rem;
            margin: 0;
            font-weight: 700;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        ">👋 Welcome back, {user_info.get('name', 'User')}!</h1>
        <p style="
            font-size: 1.2rem;
            margin: 0.5rem 0 0 0;
            opacity: 0.95;
        ">Ready to continue your machine learning journey?</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick actions
    st.markdown("### 🚀 Quick Start")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📁 Upload Data", use_container_width=True, type="primary"):
            st.session_state.current_step = "upload"
            st.rerun()
        st.markdown("**Start Fresh**  \nUpload a new dataset and begin building")
    
    with col2:
        if st.session_state.get('data') is not None:
            if st.button("🔍 Continue Analysis", use_container_width=True):
                current_step = st.session_state.get('current_step', 'upload')
                if current_step == 'upload' and st.session_state.get('target_column'):
                    st.session_state.current_step = 'explore'
                st.rerun()
            st.markdown("**Resume Work**  \nContinue where you left off")
        else:
            st.button("🔍 Continue Analysis", disabled=True, use_container_width=True)
            st.markdown("**Resume Work**  \n*Upload data first*")
    
    with col3:
        if st.session_state.get('trained_model') is not None:
            if st.button("🧠 Model Insights", use_container_width=True):
                st.session_state.current_step = "xai"
                st.rerun()
            st.markdown("**Deep Dive**  \nExplore model explainability")
        else:
            st.button("🧠 Model Insights", disabled=True, use_container_width=True)
            st.markdown("**Deep Dive**  \n*Train a model first*")
    
    st.markdown("---")
    
    # Pipeline status
    st.markdown("### 📊 Your ML Pipeline Status")
    
    pipeline_steps = [
        ("📁", "Data Upload", st.session_state.get('data') is not None),
        ("🔍", "Data Exploration", st.session_state.get('target_column') is not None),
        ("⚙️", "Preprocessing", st.session_state.get('preview_data') is not None),
        ("🎯", "Model Training", st.session_state.get('trained_model') is not None),
        ("📊", "Model Evaluation", st.session_state.get('trained_model') is not None),
        ("🔮", "Predictions", st.session_state.get('trained_model') is not None),
        ("🧠", "XAI Analysis", st.session_state.get('trained_model') is not None)
    ]
    
    cols = st.columns(len(pipeline_steps))
    for i, (icon, name, completed) in enumerate(pipeline_steps):
        with cols[i]:
            if completed:
                st.markdown(f"""
                <div style="
                    background: #d4edda;
                    border: 2px solid #c3e6cb;
                    border-radius: 10px;
                    padding: 1rem;
                    text-align: center;
                    color: #155724;
                ">
                    <div style="font-size: 2rem;">{icon}</div>
                    <div style="font-weight: bold; margin-top: 0.5rem;">{name}</div>
                    <div style="color: #28a745;">✅ Complete</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="
                    background: #f8f9fa;
                    border: 2px solid #dee2e6;
                    border-radius: 10px;
                    padding: 1rem;
                    text-align: center;
                    color: #6c757d;
                ">
                    <div style="font-size: 2rem; opacity: 0.5;">{icon}</div>
                    <div style="font-weight: bold; margin-top: 0.5rem;">{name}</div>
                    <div style="color: #6c757d;">⏳ Pending</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Recent activity or tips
    if st.session_state.get('trained_model'):
        st.markdown("### 💡 Next Steps Recommendation")
        st.info("""
        🎉 **Congratulations!** You have a trained model. Here's what you can do next:
        - 🧠 **Explore XAI Analysis** to understand how your model makes decisions
        - 🔮 **Make Predictions** on new data
        - 💾 **Save Your Model** for future use
        - 📊 **Analyze Model Performance** in detail
        """)
    else:
        st.markdown("### 💡 Getting Started Tips")
        st.info("""
        🚀 **New to XploreML?** Here's how to get started:
        1. **Upload your dataset** (CSV, Excel, or other formats)
        2. **Explore your data** with interactive visualizations
        3. **Train a model** with our lightning-fast algorithms
        4. **Evaluate performance** and make predictions
        5. **Understand your model** with explainable AI features
        """)
    
    # Show user profile in sidebar
    auth_handler.show_user_profile()