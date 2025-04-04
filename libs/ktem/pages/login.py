import streamlit as st
import hashlib
from ktem.db.models import User, engine
from sqlmodel import Session, select


class LoginPage:
    """Handles user authentication in the Streamlit app"""

    def __init__(self, app):
        self._app = app  # Reference to the main app

    def render(self):
        """Render the login page UI"""
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            self.login(username, password)

    def login(self, username, password):
        """Authenticate user and set session state"""
        if not username or not password:
            st.error("Username and password are required.")
            return

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        with Session(engine) as session:
            stmt = select(User).where(
                User.username_lower == username.lower().strip(),
                User.password == hashed_password,
            )
            user = session.exec(stmt).first()

            if user:
                st.session_state["user_id"] = user.id
                st.session_state["is_admin"] = user.admin
                st.success(f"Logged in as {'Admin' if user.admin else 'User'}: {username}")
                st.rerun()  # 🔹 Fix: Refresh UI after login
            else:
                st.error("Invalid username or password")

    def logout(self):
        """Logs out the user"""
        st.session_state["user_id"] = None
        st.session_state["is_admin"] = False
        st.success("Logged out")
        st.rerun()  # 🔹 Fix: Refresh UI after logout
