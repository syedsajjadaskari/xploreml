"""
XploreML - Main Application with Authentication Integration
Updated to work with homepage and Google OAuth
"""

import streamlit as st
import yaml
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import authentication system
try:
    from utils.auth_utils import (
        SessionManager, show_authentication_status, require_authentication,
        check_feature_access, handle_oauth_callback
    )
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    logger.warning("Authentication system not available")

# Import custom modules with error handling
try:
    from src.data_handler import DataHandler
    from src.visualizer import Visualizer
    from src.predictor import Predictor
    
    # Import fast trainers
    from src.fast_model_trainer import FastModelTrainer
    from src.hybrid_trainer import HybridFastTrainer
    FAST_TRAINING_AVAILABLE = True

except ImportError as e:
    st.error(f"❌ Error importing core modules: {e}")
    st.stop()

# Import page modules with error handling
try:
    # Import updated pages
    from pages.upload_page import page_data_upload
    from pages.exploration_page import page_data_exploration
    from pages.preprocessing_page import page_preprocessing
    from pages.fast_training_page import page_fast_training
    from pages.evaluation_page import page_model_evaluation_enhanced
    from pages.prediction_page import page_predictions
    
    # Import new XAI page
    from pages.xai_explainability_page import page_model_explainability
    XAI_PAGE_AVAILABLE = True

except ImportError as e:
    st.error(f"❌ Error importing page modules: {e}")
    XAI_PAGE_AVAILABLE = False
    st.stop()

# Import utilities with error handling
try:
    from utils.config_loader import load_config
    from utils.session_manager import initialize_session_state
    from utils.navigation import show_progress_indicator, create_sidebar
    from utils.model_utils import get_saved_models, save_model, load_saved_model
except ImportError as e:
    st.error(f"❌ Error importing utility modules: {e}")
    st.stop()

def check_authentication():
    """Check authentication and handle redirects."""
    
    if not AUTH_AVAILABLE:
        # No authentication system - allow access
        return True
    
    # Handle OAuth callback if present
    if handle_oauth_callback():
        return True
    
    # Check existing session
    session_manager = SessionManager()
    if session_manager.is_session_valid():
        return True
    
    # Not authenticated - redirect to homepage
    st.error("🔐 Authentication required. Redirecting to homepage...")
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h3>Please sign in to continue</h3>
        <p>You'll be redirected to the homepage to sign in.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🏠 Go to Homepage", type="primary"):
        st.session_state.show_main_app = False
        st.rerun()
    
    st.stop()

def show_feature_restriction(feature_name: str, required_permission: str):
    """Show feature restriction message based on user permissions."""
    
    if not check_feature_access(required_permission):
        if st.session_state.get('guest_mode'):
            st.warning(f"🔒 **{feature_name}** requires authentication. Guest users have limited access.")
        elif st.session_state.get('demo_mode'):
            st.info(f"ℹ️ **{feature_name}** is limited in demo mode. Sign in for full access.")
        else:
            st.error(f"❌ **{feature_name}** requires higher permission level.")
        return True
    return False

def main():
    """Main application function with authentication integration."""
    try:
        # Check authentication first
        if not check_authentication():
            return
        
        # Load configuration
        config = load_config()
        
        # Initialize session state
        initialize_session_state()
        
        # Initialize components
        data_handler = DataHandler(config)
        visualizer = Visualizer(config)
        predictor = Predictor(config)
        
        # Show authentication status in sidebar
        if AUTH_AVAILABLE:
            show_authentication_status()
        
        # Create sidebar navigation (now includes XAI)
        create_sidebar(None)
        
        # Main content area with XploreML branding
        _show_main_header()
        
        # Show user welcome message
        _show_user_welcome()
        
        # Progress indicator (now includes XAI step)
        show_progress_indicator(st.session_state.current_step)
        
        # Route to appropriate page
        current_step = st.session_state.current_step
        
        # Validate step
        from utils.session_manager import validate_step, can_access_step
        
        if not validate_step(current_step):
            st.error(f"Invalid step: {current_step}")
            st.session_state.current_step = "upload"
            st.rerun()
        
        if not can_access_step(current_step):
            st.warning(f"Cannot access {current_step} yet. Complete previous steps first.")
            # Redirect to appropriate step
            if st.session_state.data is None:
                st.session_state.current_step = "upload"
            elif st.session_state.target_column is None:
                st.session_state.current_step = "explore"
            elif st.session_state.trained_model is None:
                st.session_state.current_step = "train"
            st.rerun()
        
        # Route to pages with permission checks
        if current_step == "upload":
            if show_feature_restriction("Data Upload", "upload_data"):
                _show_sample_data_alternative()
            else:
                page_data_upload(data_handler)
            
        elif current_step == "explore":
            page_data_exploration(visualizer)
            
        elif current_step == "preprocess":
            page_preprocessing(data_handler)
            
        elif current_step == "train":
            page_fast_training(data_handler)
                
        elif current_step == "evaluate":
            page_model_evaluation_enhanced(visualizer)
            
        elif current_step == "predict":
            page_predictions(predictor)
            
        elif current_step == "xai":
            if XAI_PAGE_AVAILABLE:
                if show_feature_restriction("XAI Analysis", "advanced_features"):
                    _show_xai_demo()
                else:
                    page_model_explainability()
            else:
                st.error("❌ XAI page not available. Check imports.")
                st.session_state.current_step = "predict"
                st.rerun()
            
        else:
            st.error(f"Unknown step: {current_step}")
            st.write("**Available steps:** upload, explore, preprocess, train, evaluate, predict, xai")
            st.session_state.current_step = "upload"
            if st.button("🔄 Reset to Upload"):
                st.rerun()
            
    except Exception as e:
        st.error(f"❌ Application error: {str(e)}")
        logger.error(f"Application error: {e}")
        
        # Show debug info in expander
        with st.expander("🔧 Debug Information"):
            st.code(str(e))
            st.write("**Current session state:**")
            debug_info = {
                'current_step': st.session_state.get('current_step', 'unknown'),
                'has_data': st.session_state.get('data') is not None,
                'has_target': st.session_state.get('target_column') is not None,
                'has_model': st.session_state.get('trained_model') is not None,
                'authenticated': st.session_state.get('authenticated', False),
                'demo_mode': st.session_state.get('demo_mode', False),
                'xai_available': XAI_PAGE_AVAILABLE
            }
            st.json(debug_info)

def _show_main_header():
    """Show XploreML branded main header with user context."""
    
    # Get user info for personalization
    user_name = "User"
    if AUTH_AVAILABLE:
        try:
            from utils.auth_utils import SessionManager
            session_manager = SessionManager()
            user_info = session_manager.get_user_info()
            user_name = user_info.get('name', 'User').split()[0]  # First name only
        except:
            pass
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    ">
        <h1 style="
            font-size: 3.5rem;
            margin: 0;
            font-weight: 700;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        ">🚀 XploreML</h1>
        <h3 style="
            font-size: 1.4rem;
            margin: 0.5rem 0 0 0;
            font-weight: 300;
            opacity: 0.95;
        ">Welcome back, {user_name}! Let's build something amazing.</h3>
    </div>
    """, unsafe_allow_html=True)

def _show_user_welcome():
    """Show personalized welcome message based on user status."""
    
    if not AUTH_AVAILABLE:
        return
    
    try:
        from utils.auth_utils import SessionManager
        session_manager = SessionManager()
        
        if session_manager.is_demo_mode():
            st.info("🎮 **Demo Mode**: You're using XploreML in demo mode. Sign in for full access to all features!")
        elif st.session_state.get('guest_mode'):
            st.warning("👤 **Guest Access**: Limited features available. Sign in to unlock the full potential of XploreML!")
        else:
            # Show user achievements or progress
            _show_user_progress()
            
    except Exception as e:
        logger.warning(f"Error showing user welcome: {e}")

def _show_user_progress():
    """Show user's progress and achievements."""
    
    try:
        # Calculate progress
        progress_items = [
            ("Data uploaded", st.session_state.get('data') is not None),
            ("Target selected", st.session_state.get('target_column') is not None),
            ("Model trained", st.session_state.get('trained_model') is not None),
            ("Results analyzed", st.session_state.get('trained_model') is not None),
        ]
        
        completed = sum(1 for _, done in progress_items if done)
        total = len(progress_items)
        progress_pct = (completed / total) * 100
        
        if progress_pct > 0:
            st.success(f"🎯 **Progress**: {completed}/{total} steps completed ({progress_pct:.0f}%)")
            
            if completed == total:
                st.balloons()
                st.markdown("🏆 **Congratulations!** You've completed the full ML pipeline!")
        
    except Exception as e:
        logger.warning(f"Error showing user progress: {e}")

def _show_sample_data_alternative():
    """Show sample data option when upload is restricted."""
    
    st.markdown("### 🎲 Sample Data Available")
    st.info("Upload is restricted in your current access level, but you can explore with sample datasets!")
    
    sample_datasets = {
        "Titanic Survival": "Predict passenger survival (Classification)",
        "Boston Housing": "Predict house prices (Regression)", 
        "Iris Flowers": "Classify flower species (Classification)",
        "Wine Quality": "Predict wine ratings (Regression)"
    }
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_dataset = st.selectbox(
            "Choose a sample dataset:",
            list(sample_datasets.keys()),
            help="Explore XploreML with these curated datasets"
        )
        
        if selected_dataset:
            st.info(f"📖 {sample_datasets[selected_dataset]}")
    
    with col2:
        if st.button("📊 Load Sample Data", type="primary", use_container_width=True):
            try:
                # Load sample data through data handler
                from src.data_handler import DataHandler
                data_handler = DataHandler({})
                
                dataset_map = {
                    "Titanic Survival": "titanic",
                    "Boston Housing": "boston",
                    "Iris Flowers": "iris", 
                    "Wine Quality": "wine"
                }
                
                dataset_name = dataset_map.get(selected_dataset, "titanic")
                data = data_handler.load_sample_data(dataset_name)
                
                if data is not None:
                    st.session_state.data = data
                    
                    # Auto-set target based on dataset
                    target_map = {
                        "titanic": "Survived",
                        "boston": "medv", 
                        "iris": "species",
                        "wine": "quality"
                    }
                    
                    target_col = target_map.get(dataset_name)
                    if target_col and target_col in data.columns:
                        st.session_state.target_column = target_col
                        st.session_state.problem_type = data_handler.detect_problem_type(data, target_col)
                    
                    st.success(f"✅ {selected_dataset} dataset loaded!")
                    st.rerun()
                else:
                    st.error("❌ Failed to load sample dataset")
                    
            except Exception as e:
                st.error(f"❌ Error loading sample data: {str(e)}")
    
    # Show upgrade prompt
    st.markdown("---")
    st.markdown("### 🚀 Want to upload your own data?")
    
    upgrade_col1, upgrade_col2 = st.columns(2)
    
    with upgrade_col1:
        st.markdown("**Sign in for full access:**")
        st.markdown("- 📁 Upload your own datasets")
        st.markdown("- 💾 Save and manage models")
        st.markdown("- 📊 Export results and reports")
        st.markdown("- 🧠 Advanced XAI analysis")
    
    with upgrade_col2:
        if st.button("🔑 Sign In Now", type="primary", use_container_width=True):
            st.session_state.show_main_app = False
            st.rerun()

def _show_xai_demo():
    """Show XAI demo when advanced features are restricted."""
    
    st.markdown("### 🧠 XAI Analysis Demo")
    st.info("Advanced XAI features require full authentication. Here's what you're missing:")
    
    demo_col1, demo_col2 = st.columns(2)
    
    with demo_col1:
        st.markdown("""
        **🌍 Global Analysis:**
        - Model-wide feature importance
        - Performance breakdown by features
        - Decision boundary visualization
        - Bias detection and analysis
        
        **🎯 Local Explanations:**
        - Individual prediction explanations
        - LIME/SHAP analysis
        - Feature contribution breakdown
        - What-if scenario analysis
        """)
    
    with demo_col2:
        st.markdown("""
        **📊 Advanced Features:**
        - Partial dependence plots
        - Feature interaction analysis
        - Model comparison explanations
        - Surrogate model generation
        
        **🔍 Model Debugging:**
        - Error analysis by features
        - Prediction confidence analysis
        - Model behavior insights
        - Performance optimization tips
        """)
    
    # Show a sample XAI visualization
    st.markdown("#### 📈 Sample XAI Output")
    
    import plotly.graph_objects as go
    import numpy as np
    
    # Create sample feature importance chart
    features = ['Income', 'Age', 'Education', 'Experience', 'Location']
    importance = [0.35, 0.25, 0.20, 0.15, 0.05]
    
    fig = go.Figure(data=go.Bar(
        x=importance,
        y=features,
        orientation='h',
        marker_color=['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57']
    ))
    
    fig.update_layout(
        title="Sample Feature Importance Analysis",
        xaxis_title="Importance Score",
        height=300,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.success("🚀 **This is just a sample!** Sign in to analyze your own models with full XAI capabilities.")
    
    if st.button("🔓 Unlock Full XAI Analysis", type="primary", use_container_width=True):
        st.session_state.show_main_app = False
        st.rerun()

def _show_pipeline_overview():
    """Show enhanced pipeline overview with user permissions."""
    with st.expander("🔍 XploreML Pipeline Overview"):
        
        # Get user permissions
        permissions = {}
        if AUTH_AVAILABLE:
            try:
                from utils.auth_utils import get_user_permissions
                permissions = get_user_permissions()
            except:
                permissions = {}
        
        steps_status = {
            "📁 Data Upload": (
                st.session_state.data is not None,
                permissions.get('upload_data', True)
            ),
            "🔍 Data Exploration": (
                st.session_state.target_column is not None,
                True
            ),
            "⚙️ Preprocessing": (
                st.session_state.get('preview_data') is not None,
                True
            ),
            "🎯 Model Training": (
                st.session_state.trained_model is not None,
                True
            ),
            "📊 Model Evaluation": (
                st.session_state.trained_model is not None,
                True
            ),
            "🔮 Predictions": (
                st.session_state.trained_model is not None,
                True
            ),
            "🧠 XAI Analysis": (
                st.session_state.trained_model is not None and XAI_PAGE_AVAILABLE,
                permissions.get('advanced_features', True)
            )
        }
        
        cols = st.columns(len(steps_status))
        for i, (step, (completed, allowed)) in enumerate(steps_status.items()):
            with cols[i]:
                if not allowed:
                    st.error(f"🔒 {step}")
                elif completed:
                    st.success(f"✅ {step}")
                else:
                    st.info(f"⏳ {step}")
        
        # Show next recommended action with permissions
        if st.session_state.data is None:
            if permissions.get('upload_data', True):
                st.info("👆 **Next:** Upload your dataset to begin your XploreML journey")
            else:
                st.info("👆 **Next:** Try sample data to explore XploreML features")
        elif st.session_state.target_column is None:
            st.info("👆 **Next:** Explore data and select target column")
        elif st.session_state.trained_model is None:
            st.info("👆 **Next:** Train a machine learning model with XploreML")
        elif st.session_state.current_step != "xai":
            st.success("🎉 **XploreML Pipeline Complete!** Try XAI analysis to understand your model")

def _show_permission_status():
    """Show current user's permission status."""
    
    if not AUTH_AVAILABLE:
        return
    
    try:
        from utils.auth_utils import get_user_permissions, SessionManager
        
        permissions = get_user_permissions()
        session_manager = SessionManager()
        
        with st.expander("🔑 Access Level & Permissions"):
            
            # Show user mode
            if st.session_state.get('guest_mode'):
                st.markdown("**👤 Guest Mode** - Limited access")
            elif session_manager.is_demo_mode():
                st.markdown("**🎮 Demo Mode** - Most features available")
            else:
                st.markdown("**🔐 Full Access** - All features available")
            
            # Show specific permissions
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Available Features:**")
                for feature, allowed in permissions.items():
                    icon = "✅" if allowed else "❌"
                    feature_name = feature.replace('_', ' ').title()
                    st.markdown(f"{icon} {feature_name}")
            
            with col2:
                st.markdown("**Upgrade Benefits:**")
                if not all(permissions.values()):
                    st.markdown("- 🔓 Unlock all features")
                    st.markdown("- 📁 Upload unlimited data")
                    st.markdown("- 💾 Save models permanently")
                    st.markdown("- 🧠 Advanced XAI analysis")
                    
                    if st.button("⬆️ Upgrade Access", type="primary", use_container_width=True):
                        st.session_state.show_main_app = False
                        st.rerun()
                else:
                    st.success("🎉 You have full access!")
                    
    except Exception as e:
        logger.warning(f"Error showing permission status: {e}")

if __name__ == "__main__":
    # Check if we should show main app or redirect to homepage
    if st.session_state.get('show_main_app', True):
        # Run main application
        main()
        
        # Show additional information
        _show_pipeline_overview()
        _show_permission_status()
        
        # Footer with authentication info
        st.markdown("---")
        
        footer_col1, footer_col2 = st.columns([3, 1])
        
        with footer_col1:
            st.markdown("""
            <div style="text-align: center; padding: 1rem; color: #666;">
                <p>🚀 <strong>XploreML</strong> - Learn, Experiment, and Discover Machine Learning without Code</p>
                <p>Made with ❤️ for the Data Science Community | Version 2.0.0</p>
            </div>
            """, unsafe_allow_html=True)
        
        with footer_col2:
            if AUTH_AVAILABLE:
                if st.button("🏠 Homepage", use_container_width=True):
                    st.session_state.show_main_app = False
                    st.rerun()
    
    else:
        # Redirect to homepage
        st.markdown("""
        <script>
        window.location.href = '/';
        </script>
        """, unsafe_allow_html=True)
        
        st.info("Redirecting to homepage...")
        
        if st.button("🏠 Go to Homepage", type="primary"):
            st.session_state.show_main_app = False
            st.rerun()