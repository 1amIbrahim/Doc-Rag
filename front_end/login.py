import streamlit as st
import streamlit.components.v1 as components

# Set page config first
st.set_page_config(page_title="Intelliretrieve", page_icon="🔒", layout="centered")

# Background image
BACKGROUND_IMAGE = "https://www.ismartcom.com/hubfs/Privacy-age-AI.jpg"

# Custom CSS with page-turn animation
st.markdown(f"""
<style>
    .stApp {{
        background-image: url("{BACKGROUND_IMAGE}");
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
        min-height: 100vh;
    }}

    .auth-container {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 10px;
        padding: 2.5rem;
        margin: 2rem auto;
        max-width: 450px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
        animation: page-turn 0.8s ease-in-out;
        transform-origin: left center;
    }}

    @keyframes page-turn {{
        0% {{
            transform: perspective(1000px) rotateY(-90deg);
            opacity: 0;
        }}
        100% {{
            transform: perspective(1000px) rotateY(0deg);
            opacity: 1;
        }}
    }}

    .social-btn {{
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.75rem 0;
        cursor: pointer;
        transition: all 0.3s;
        font-weight: 500;
        border: none;
        width: 100%;
    }}

    .social-btn:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }}

    .google-btn {{
        background: #DB4437;
        color: white;
    }}

    .facebook-btn {{
        background: #4267B2;
        color: white;
    }}

    .divider {{
        display: flex;
        align-items: center;
        margin: 1.5rem 0;
        color: #666;
    }}

    .divider::before, .divider::after {{
        content: "";
        flex: 1;
        border-bottom: 1px solid #ddd;
    }}

    .divider-text {{
        padding: 0 1rem;
        font-size: 0.9rem;
    }}

    .header {{
        text-align: center;
        margin-bottom: 1.5rem;
        animation: fade-in 1s ease-in-out;
    }}

    .logo {{
        font-size: 2.2rem;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }}

    .tagline {{
        font-size: 1rem;
        color: #666;
    }}

    @keyframes fade-in {{
        0% {{ opacity: 0; transform: translateY(-20px); }}
        100% {{ opacity: 1; transform: translateY(0); }}
    }}

    .welcome-container {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 10px;
        padding: 2rem;
        margin: 2rem auto;
        max-width: 600px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
        animation: page-turn 0.8s ease-in-out;
    }}
</style>
""", unsafe_allow_html=True)

# JavaScript for dynamic page-turn effect on tab switch
PAGE_TURN_SCRIPT = """
<script>
    function applyPageTurn(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.animation = 'none';
            void element.offsetWidth; // Trigger reflow
            element.style.animation = 'page-turn 0.8s ease-in-out';
        }
    }
</script>
"""

# Initialize session state
if 'users_db' not in st.session_state:
    st.session_state.users_db = {
        "admin@intelliretrieve.com": {"password": "admin123", "name": "Admin"},
        "user@intelliretrieve.com": {"password": "user123", "name": "User"}
    }

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'current_user' not in st.session_state:
    st.session_state.current_user = None

if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "Sign In"


def authenticate_user(email, password):
    return st.session_state.users_db.get(email, {}).get("password") == password


def auth_page():
    tab1, tab2 = st.tabs(["Sign In", "Sign Up"])

    # Inject JavaScript for animation control
    components.html(PAGE_TURN_SCRIPT, height=0)

    with tab1:
        with st.container():
            st.markdown("<div class='auth-container' id='signin-container'>", unsafe_allow_html=True)

            # Header
            st.markdown("""
            <div class="header">
                <div class="logo">Intelliretrieve</div>
                <div class="tagline">AI-powered intelligent retrieval</div>
            </div>
            """, unsafe_allow_html=True)

            # Email/Password Form
            email = st.text_input("Email", placeholder="your@email.com", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")

            if st.button("Sign In", type="primary", use_container_width=True):
                if authenticate_user(email, password):
                    st.success("Logged in successfully!")
                    st.session_state.authenticated = True
                    st.session_state.current_user = email
                    st.rerun()
                else:
                    st.error("Invalid email or password")

            # Social Login
            st.markdown("""
            <div class="divider">
                <span class="divider-text">or continue with</span>
            </div>

            <button class="social-btn google-btn" onclick="alert('Google login selected')">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="white" style="margin-right: 10px;">
                    <path d="M12.545 10.239v3.821h5.445c-0.712 2.315-2.647 3.972-5.445 3.972-3.332 0-6.033-2.701-6.033-6.032s2.701-6.032 6.033-6.032c1.498 0 2.866 0.549 3.921 1.453l2.814-2.814c-1.784-1.664-4.153-2.675-6.735-2.675-5.522 0-10 4.477-10 10s4.478 10 10 10c8.396 0 10-7.496 10-10 0-0.671-0.068-1.325-0.182-1.977h-9.818z"/>
                </svg>
                Continue with Google
            </button>

            <button class="social-btn facebook-btn" onclick="alert('Facebook login selected')">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="white" style="margin-right: 10px;">
                    <path d="M22.675 0h-21.35c-.732 0-1.325.593-1.325 1.325v21.351c0 .731.593 1.324 1.325 1.324h11.495v-9.294h-3.128v-3.622h3.128v-2.671c0-3.1 1.893-4.788 4.659-4.788 1.325 0 2.463.099 2.795.143v3.24l-1.918.001c-1.504 0-1.795.715-1.795 1.763v2.313h3.587l-.467 3.622h-3.12v9.293h6.116c.73 0 1.323-.593 1.323-1.325v-21.35c0-.732-.593-1.325-1.325-1.325z"/>
                </svg>
                Continue with Facebook
            </button>
            """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        with st.container():
            st.markdown("<div class='auth-container' id='signup-container'>", unsafe_allow_html=True)

            # Header
            st.markdown("""
            <div class="header">
                <div class="logo">Intelliretrieve</div>
                <div class="tagline">Create your account</div>
            </div>
            """, unsafe_allow_html=True)

            # Registration Form
            name = st.text_input("Full Name", placeholder="Your Name", key="signup_name")
            new_email = st.text_input("Email", placeholder="your@email.com", key="signup_email")
            new_password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")

            if st.button("Sign Up", type="primary", use_container_width=True):
                if not name or not new_email or not new_password:
                    st.error("Please fill in all fields")
                elif new_password != confirm_password:
                    st.error("Passwords don't match")
                elif new_email in st.session_state.users_db:
                    st.error("Email already registered")
                else:
                    st.session_state.users_db[new_email] = {"password": new_password, "name": name}
                    st.success("Account created successfully! Please sign in.")
                    st.session_state.current_tab = "Sign In"
                    st.rerun()

            # Social Sign Up
            st.markdown("""
            <div class="divider">
                <span class="divider-text">or sign up with</span>
            </div>

            <button class="social-btn google-btn" onclick="alert('Google signup selected')">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="white" style="margin-right: 10px;">
                    <path d="M12.545 10.239v3.821h5.445c-0.712 2.315-2.647 3.972-5.445 3.972-3.332 0-6.033-2.701-6.033-6.032s2.701-6.032 6.033-6.032c1.498 0 2.866 0.549 3.921 1.453l2.814-2.814c-1.784-1.664-4.153-2.675-6.735-2.675-5.522 0-10 4.477-10 10s4.478 10 10 10c8.396 0 10-7.496 10-10 0-0.671-0.068-1.325-0.182-1.977h-9.818z"/>
                </svg>
                Sign up with Google
            </button>

            <button class="social-btn facebook-btn" onclick="alert('Facebook signup selected')">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="white" style="margin-right: 10px;">
                    <path d="M22.675 0h-21.35c-.732 0-1.325.593-1.325 1.325v21.351c0 .731.593 1.324 1.325 1.324h11.495v-9.294h-3.128v-3.622h3.128v-2.671c0-3.1 1.893-4.788 4.659-4.788 1.325 0 2.463.099 2.795.143v3.24l-1.918.001c-1.504 0-1.795.715-1.795 1.763v2.313h3.587l-.467 3.622h-3.12v9.293h6.116c.73 0 1.323-.593 1.323-1.325v-21.35c0-.732-.593-1.325-1.325-1.325z"/>
                </svg>
                Sign up with Facebook
            </button>
            """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)


# Main app logic
if not st.session_state.authenticated:
    auth_page()
else:
    with st.container():
        st.markdown("<div class='welcome-container'>", unsafe_allow_html=True)
        st.title(f"Welcome back, {st.session_state.users_db[st.session_state.current_user]['name']}!")
        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.rerun()
        st.write("Your protected content goes here")
        st.markdown("</div>", unsafe_allow_html=True)

# Apply page-turn animation dynamically based on tab or auth state change
if not st.session_state.authenticated:
    components.html(f"""
    <script>
        const currentTab = "{st.session_state.current_tab}";
        if (currentTab === "Sign In") {{
            applyPageTurn('signin-container');
        }} else {{
            applyPageTurn('signup-container');
        }}
    </script>
    """, height=0)