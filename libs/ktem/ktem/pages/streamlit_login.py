import hashlib
import streamlit as st
from sqlmodel import Session, select
from ktem.db.models import User, engine
from ktem.pages.resources.user import create_user
from theflow.settings import settings as flowsettings
from ktem.app import BasePage

class LoginPage(BasePage):
    """Streamlit version of the Login Page with Remember Me functionality"""

    public_events = ["onSignIn"]

    def __init__(self, app):
        super().__init__(app)
        self.user_id = None
        self.on_building_ui()

    def on_building_ui(self):
        """Prepare UI structure"""
        pass

    def render(self):
        st.title(f"Welcome to {self._app.app_name}!")

        if "logged_in" not in st.session_state:
            st.session_state.logged_in = False

        self.check_auto_login()

        if not st.session_state.logged_in:
            usn = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            remember_me = st.checkbox("Remember Me", value=False)

            login_clicked = st.button("Login")

            if login_clicked:
                user_id = self.login(usn, pwd)

                if user_id:
                    st.success("Logged in successfully!")
                    st.session_state.user_id = user_id
                    st.session_state.logged_in = True

                    # Save login info if remember me
                    if remember_me:
                        # Append params to URL (if remember me)
                        st.rerun()

                    self.fire_public_event("onSignIn", user_id)
                else:
                    st.error("Invalid username or password.")
        else:
            st.success(f"Logged in as {self.get_username(st.session_state.user_id)}")
            if st.button("Logout"):
                self.logout()

    def login(self, usn, pwd):
        if not usn or not pwd:
            return None

        hashed_password = hashlib.sha256(pwd.encode()).hexdigest()

        with Session(engine) as session:
            stmt = select(User).where(
                User.username_lower == usn.lower().strip(),
                User.password == hashed_password,
            )
            result = session.exec(stmt).first()
            if result:
                return result.id
            else:
                return None

    def check_auto_login(self):
        """Auto-login if username/password present in query params"""
        if not st.session_state.logged_in:
            params = st.query_params
            usn = params.get("username", [None])[0]
            pwd = params.get("password", [None])[0]

            if usn and pwd:
                user_id = self.login(usn, pwd)
                if user_id:
                    st.session_state.user_id = user_id
                    st.session_state.logged_in = True
                    self.fire_public_event("onSignIn", user_id)
                    st.experimental_rerun()

    def logout(self):
        """Logs the user out."""
        st.session_state.user_id = None
        st.session_state.logged_in = False
        st.experimental_set_query_params()  # clear saved username/password
        self.fire_public_event("onSignOut", None)
        st.experimental_rerun()

    def get_username(self, user_id):
        """Get username from the database"""
        with Session(engine) as session:
            stmt = select(User).where(User.id == user_id)
            result = session.exec(stmt).first()
            if result:
                return result.username
            else:
                return "Unknown User"

    def fire_public_event(self, event_name, user_id):
        """Helper to manually trigger public events"""
        events = self._app.get_event(event_name)
        for event in events:
            fn = event["fn"]
            fn(user_id)
