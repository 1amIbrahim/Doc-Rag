import streamlit as st
from ktem.streamlit_app import StreamlitBaseApp
from ktem.db.models import User, engine
from ktem.embeddings.ui_st import EmbeddingManagement
from libs.ktem.ktem.index.ui_st import IndexManagement
from ktem.llms.ui_st import LLMManagement
from ktem.rerankings.ui_st import RerankingManagement
from sqlmodel import Session, select

from .user_st import UserManagement


class ResourcesTab(StreamlitBaseApp):
    def __init__(self, app):
        super().__init__(app)
        self._app = app
        
    def render(self):
        """Render the Resources tab UI"""

        # Create tabs
        tab_titles = [
            "Index Collections",
            "LLMs",
            "Embeddings",
            "Rerankings",
        ]
        if self._app.f_user_management:
            tab_titles.append("Users")

        tabs = st.tabs(tab_titles)

        # Index Collections tab
        with tabs[0]:
            self.index_management = IndexManagement(self._app)

        # LLMs tab
        with tabs[1]:
            self.llm_management = LLMManagement()

        # Embeddings tab
        with tabs[2]:
            self.emb_management = EmbeddingManagement(self._app)

        # Rerankings tab
        with tabs[3]:
            self.rerank_management = RerankingManagement()

        # Users tab (only if user management is enabled)
        if self._app.f_user_management:
            with tabs[4]:
                if not self._check_admin_status():
                    st.warning("You don't have permission to access this section")
                    st.stop()
                self.user_management = UserManagement(self._app)

    def _check_admin_status(self):
        """Check if current user is admin"""
        if not hasattr(self._app, 'user_id') or not self._app.user_id:
            return False

        with Session(engine) as session:
            user = session.exec(
                select(User).where(User.id == self._app.user_id)
            ).first()

        return user and user.admin
