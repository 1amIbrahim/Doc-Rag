import hashlib
import streamlit as st
from ktem.app import BasePage
from ktem.db.models import User, engine
from ktem.pages.resources.user import create_user
from sqlmodel import Session, select


class LoginPage(BasePage):
    public_events = ["onSignIn"]

    def __init__(self, app):
        self._app = app

    def render(self):
        st.title(f"Welcome to {self._app.app_name}!")

        st.markdown("### Please log in to continue.")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user_id = self.login(username, password)
            if user_id:
                self._app.user_id = user_id
                st.session_state.show_tabs = True
                st.success("Login successful")
                self._app.raise_event("onSignIn", user_id)
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")

    def login(self, usn, pwd):
        if not usn or not pwd:
            return None

        hashed_password = hashlib.sha256(pwd.encode()).hexdigest()
        with Session(engine) as session:
            stmt = select(User).where(
                User.username_lower == usn.lower().strip(),
                User.password == hashed_password,
            )
            result = session.exec(stmt).all()
            if result:
                return result[0].id

        return None

    def on_subscribe_public_events(self):
        self._app.subscribe_event(
            name="onSignOut",
            definition={
                "fn": self.logout,
                "inputs": [self._app.user_id],
                "outputs": [],
            },
        )

    def logout(self, user_id):
        self._app.user_id = None
        st.session_state.show_tabs = False
        st.success("Signed out")
        st.experimental_rerun()
# EDITED THIS