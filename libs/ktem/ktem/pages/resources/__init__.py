import streamlit as st
from sqlmodel import Session, select
from ktem.db.models import User, engine

from ktem.index.ui import IndexManagement
from ktem.llms.ui import LLMManagement
from ktem.embeddings.ui import EmbeddingManagement
from ktem.rerankings.ui import RerankingManagement
from .user import UserManagement


class ResourcesTab:
    def __init__(self, app):
        self._app = app
        self.render()

    def render(self):
        st.subheader("Resources")

        tab_options = ["Index Collections", "LLMs", "Embeddings", "Rerankings"]
        if self._app.f_user_management and st.session_state.get("is_admin"):
            tab_options.append("Users")

        selected_tab = st.selectbox("Select Resource Tab", tab_options)

        if selected_tab == "Index Collections":
            IndexManagement(self._app)
        elif selected_tab == "LLMs":
            LLMManagement(self._app)
        elif selected_tab == "Embeddings":
            EmbeddingManagement(self._app)
        elif selected_tab == "Rerankings":
            RerankingManagement(self._app)
        elif selected_tab == "Users":
            if self._app.f_user_management and st.session_state.get("is_admin"):
                UserManagement(self._app)

    def toggle_user_management(self, user_id):
        """Set admin visibility in session state based on user role"""
        with Session(engine) as session:
            user = session.exec(select(User).where(User.id == user_id)).first()
            st.session_state["is_admin"] = bool(user and user.admin)
