# app.py - Main application controller
import streamlit as st
from web import main as web_main
from login import auth_page, authenticate_user
from front import main as front_main
import sys
import os

# Add the directory containing your modules to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set page config (this will apply to all pages)
st.set_page_config(
    page_title="IntelliRetrieve",
    page_icon="🔒",
    layout="centered"
)

# Initialize session state for authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'show_login' not in st.session_state:
    st.session_state.show_login = False
if 'show_signup' not in st.session_state:
    st.session_state.show_signup = False

# Main app router
def main():
    # Check authentication status first
    if st.session_state.authenticated:
        front_main()  # Show the chat interface if authenticated
    elif st.session_state.show_login or st.session_state.show_signup:
        auth_page()  # Show login/signup page if triggered
    else:
        web_main()  # Show the main landing page by default

# Handle navigation from web.py to login.py
def navigate_to_login():
    st.session_state.show_login = True
    st.session_state.show_signup = False
    st.rerun()

# Handle successful authentication
def handle_successful_login():
    st.session_state.authenticated = True
    st.session_state.show_login = False
    st.session_state.show_signup = False
    st.rerun()

# Handle logout from front.py
def handle_logout():
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.show_login = False
    st.session_state.show_signup = False
    st.rerun()

# Add these navigation functions to session state so other files can access them
if 'navigation' not in st.session_state:
    st.session_state.navigation = {
        'navigate_to_login': navigate_to_login,
        'handle_successful_login': handle_successful_login,
        'handle_logout': handle_logout
    }

if __name__ == "__main__":
    main()