import streamlit as st
import re


def validate_password(password):
    """Check if password meets security requirements"""
    if len(password) < 8:
        return "Password must be at least 8 characters long"
    if not re.search("[A-Z]", password):
        return "Password must contain at least one uppercase letter"
    if not re.search("[a-z]", password):
        return "Password must contain at least one lowercase letter"
    if not re.search("[0-9]", password):
        return "Password must contain at least one digit"
    if not re.search("[!@#$%^&*(),.?\":{}|<>]", password):
        return "Password must contain at least one special character"
    return None


def main():
    # Set page configuration with favicon
    st.set_page_config(
        page_title="Unit - Admin Panel",
        page_icon="⚙️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for better styling
    st.markdown("""
    <style>
        .header-style {
            font-size: 2.5rem;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 1.5rem;
        }
        .subheader-style {
            font-size: 1.5rem;
            font-weight: 600;
            color: #34495e;
            margin-bottom: 1rem;
        }
        .success-box {
            background-color: #e8f5e9;
            border-left: 5px solid #2e7d32;
            padding: 1rem;
            margin: 1rem 0;
        }
        .error-box {
            background-color: #ffebee;
            border-left: 5px solid #c62828;
            padding: 1rem;
            margin: 1rem 0;
        }
        .info-box {
            background-color: #e3f2fd;
            border-left: 5px solid #1565c0;
            padding: 1rem;
            margin: 1rem 0;
        }
        .custom-primary-button {
            background-color: #4CAF50 !important;
            color: white !important;
            border: none !important;
            padding: 0.5rem 1rem !important;
            text-align: center !important;
            text-decoration: none !important;
            display: inline-block !important;
            font-size: 16px !important;
            margin: 4px 2px !important;
            cursor: pointer !important;
            border-radius: 4px !important;
            width: 100% !important;
        }
        .custom-primary-button:hover {
            background-color: #45a049 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Main header with custom style
    st.markdown('<div class="header-style">Unit</div>', unsafe_allow_html=True)

    # User settings section with expandable container
    with st.expander("🔧 User Settings", expanded=True):
        st.markdown('<div class="subheader-style">User Settings</div>', unsafe_allow_html=True)

        # Create tabs for different setting categories
        tab1, tab2 = st.tabs(["Retrieval Settings", "Reasoning Settings"])

        with tab1:
            col1, col2 = st.columns([3, 1])
            with col1:
                retrieval_option = st.selectbox(
                    "Retrieval Mode",
                    ["Basic", "Advanced", "Custom"],
                    index=1,
                    help="Select your preferred retrieval method"
                )
            with col2:
                st.write("")  # Spacer
                retrieval_cache = st.checkbox("Enable caching", value=True)

            if retrieval_option == "Custom":
                st.slider("Custom retrieval depth", 1, 10, 5)
                st.checkbox("Enable fuzzy matching")
                st.checkbox("Enable semantic search")

        with tab2:
            reasoning_option = st.selectbox(
                "Reasoning Level",
                ["Simple", "Detailed", "Expert"],
                index=1,
                help="Select your preferred reasoning depth"
            )

            if reasoning_option == "Expert":
                st.checkbox("Enable multi-hop reasoning")
                st.checkbox("Show reasoning steps")
                st.number_input("Maximum reasoning steps", min_value=1, max_value=20, value=5)

    # Server management section
    st.divider()
    with st.container():
        st.markdown('<div class="subheader-style">Server Management</div>', unsafe_allow_html=True)

        server_col1, server_col2 = st.columns([1, 3])
        with server_col1:
            # Initialize session state for server_status if not exists
            if 'server_status' not in st.session_state:
                st.session_state.server_status = "Online"

            server_status = st.selectbox(
                "Server 6 Status",
                ["Online", "Maintenance", "Offline"],
                index=["Online", "Maintenance", "Offline"].index(st.session_state.server_status),
                key="server_status_select"
            )
            # Update session state when selectbox changes
            st.session_state.server_status = server_status

        with server_col2:
            if server_status == "Online":
                st.success("Server is running normally")
                if st.button("🔄 Restart Server", type="secondary"):
                    st.session_state.server_status = "Maintenance"
                    st.rerun()
            elif server_status == "Maintenance":
                st.warning("Server in maintenance mode")
                if st.button("🔼 Bring Online", type="primary"):
                    st.session_state.server_status = "Online"
                    st.rerun()
            else:
                st.error("Server is offline")
                if st.button("⏱️ Start Server", type="primary"):
                    st.session_state.server_status = "Online"
                    st.rerun()

    # User administration section
    st.divider()
    with st.container():
        st.markdown('<div class="subheader-style">User Administration</div>', unsafe_allow_html=True)

        with st.form("password_change_form", clear_on_submit=True):
            st.markdown("**Password Requirements**")
            st.caption("""
            - At least 8 characters long
            - Contains uppercase and lowercase letters
            - Includes at least one number
            - Includes at least one special character
            """)

            current_password = st.text_input("Current Password", type="password", autocomplete="current-password")
            new_password = st.text_input("New Password", type="password", autocomplete="new-password")
            confirm_password = st.text_input("Confirm New Password", type="password", autocomplete="new-password")

            # Fixed the button implementation
            if st.form_submit_button("🔒 Change Password", type="primary"):
                if not current_password:
                    st.error("Please enter your current password")
                elif not new_password or not confirm_password:
                    st.error("Please enter and confirm your new password")
                elif new_password != confirm_password:
                    st.error("New passwords do not match!")
                else:
                    validation_error = validate_password(new_password)
                    if validation_error:
                        st.error(validation_error)
                    else:
                        st.success("Password changed successfully!")
                        st.balloons()

    # Add a save all settings button at the bottom
    st.divider()
    if st.button("💾 Save All Settings", type="primary", use_container_width=True):
        st.toast("All settings saved successfully!", icon="✅")


if __name__ == "__main__":
    main()