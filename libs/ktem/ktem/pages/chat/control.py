import logging
import os
from copy import deepcopy

import streamlit as st
from ktem.app import BasePage
from ktem.db.models import Conversation, User, engine
from sqlmodel import Session, or_, select

import flowsettings

from ...utils.conversation import sync_retrieval_n_message
from .chat_suggestion import ChatSuggestion
from .common import STATE

logger = logging.getLogger(__name__)

KH_DEMO_MODE = getattr(flowsettings, "KH_DEMO_MODE", False)
KH_SSO_ENABLED = getattr(flowsettings, "KH_SSO_ENABLED", False)

class ConversationControl(BasePage):
    """Manage conversation in Streamlit"""

    def __init__(self, app):
        self._app = app
        self.on_building_ui()

    def on_building_ui(self):
        """Build UI for conversation management in Streamlit."""
        
        with st.sidebar:
            st.header("Conversations" if not KH_DEMO_MODE else "Kotaemon Papers")

            # Dark Mode Toggle (Requires JavaScript)
            if st.button("Toggle Dark Mode"):
                st.markdown("<script>document.body.classList.toggle('dark');</script>", unsafe_allow_html=True)

            # Expand Buttons (Handled via CSS or Custom JS in Streamlit)
            st.markdown("---")

            # Conversation Dropdown
            st.subheader("Chat Sessions")
            user_id = st.session_state.get("user_id")  # 🔹 Fix: Get user_id from session state
            if not user_id:
                st.error("You need to log in to access the chat.")
                return
            conversation_list = self.load_chat_history(user_id) 
            selected_conv = st.selectbox("Select a conversation", conversation_list, index=0 if conversation_list else None)

            # New/Delete/Rename Buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            if KH_DEMO_MODE:
                if st.button("New Chat", key="new_chat_button"):
                    self.new_conv(self._app.user_id)
            else:
                with col1:
                    if st.button("Rename"):
                        new_name = st.text_input("Enter new name:", key="rename_input")
                        if st.button("Save Rename"):
                            self.rename_conv(selected_conv, new_name, True, self._app.user_id)
                with col2:
                    if st.button("Delete", key="delete_button"):
                        self.delete_conv(selected_conv, self._app.user_id)
                with col3:
                    if st.button("New", key="new_button"):
                        self.new_conv(self._app.user_id)

            # Chat Suggestion & Public Checkbox
            suggest_chat = st.checkbox("Suggest chat", value=False, key="suggest_chat_checkbox", disabled=KH_DEMO_MODE)
            share_conv = st.checkbox("Share this conversation", value=False, key="share_checkbox", disabled=KH_DEMO_MODE or KH_SSO_ENABLED)

            if KH_DEMO_MODE:
                st.button("Sign-in to create new chat", key="sign_in_button")
                st.button("Sign-out", key="sign_out_button", disabled=True)

    def load_chat_history(self, user_id):
        """Load user's chat history"""
        can_see_public = False
        with Session(engine) as session:
            user = session.exec(select(User).where(User.id == user_id)).one_or_none()
            if user and flowsettings.KH_USER_CAN_SEE_PUBLIC:
                can_see_public = user.username == flowsettings.KH_USER_CAN_SEE_PUBLIC
            else:
                can_see_public = True

        options = []
        with Session(engine) as session:
            statement = select(Conversation).where(
                or_(Conversation.user == user_id, Conversation.is_public) if can_see_public else (Conversation.user == user_id)
            ).order_by(Conversation.is_public.desc(), Conversation.date_created.desc())

            results = session.exec(statement).all()
            for result in results:
                options.append(result.name)
        return options

    def new_conv(self, user_id):
        """Create a new conversation"""
        if not user_id:
            st.warning("Please sign in first (Settings → User Settings)")
            return
        with Session(engine) as session:
            new_conv = Conversation(user=user_id)
            session.add(new_conv)
            session.commit()
        st.success("New conversation created.")
        st.experimental_rerun()

    def delete_conv(self, conversation_name, user_id):
        """Delete selected conversation"""
        if not conversation_name:
            st.warning("No conversation selected.")
            return
        if not user_id:
            st.warning("Please sign in first (Settings → User Settings)")
            return
        with Session(engine) as session:
            conversation = session.exec(select(Conversation).where(Conversation.name == conversation_name)).one_or_none()
            if conversation:
                session.delete(conversation)
                session.commit()
                st.success("Conversation deleted.")
                st.experimental_rerun()

    def rename_conv(self, conversation_name, new_name, is_renamed, user_id):
        """Rename selected conversation"""
        if not is_renamed or KH_DEMO_MODE or not user_id or not conversation_name:
            return
        errors = self.is_conv_name_valid(new_name)
        if errors:
            st.warning(errors)
            return

        with Session(engine) as session:
            conversation = session.exec(select(Conversation).where(Conversation.name == conversation_name)).one_or_none()
            if conversation:
                conversation.name = new_name
                session.add(conversation)
                session.commit()
                st.success("Conversation renamed.")
                st.rerun()

    def is_conv_name_valid(self, name):
        """Check if conversation name is valid"""
        errors = []
        if len(name) == 0:
            errors.append("Name cannot be empty")
        elif len(name) > 40:
            errors.append("Name cannot be longer than 40 characters")
        return "; ".join(errors)

    def select_conv(self, conversation_name, user_id):
        """Retrieve conversation details when selected"""
        with Session(engine) as session:
            conversation = session.exec(select(Conversation).where(Conversation.name == conversation_name)).one_or_none()
            if not conversation:
                return None, "", [], [], "", None, [], [], False, STATE, []

            selected = conversation.data_source.get("selected", {}) if user_id == conversation.user else {}
            chats = conversation.data_source.get("messages", [])
            chat_suggestions = conversation.data_source.get("chat_suggestions", [[each] for each in ChatSuggestion.CHAT_SAMPLES])
            retrieval_history = conversation.data_source.get("retrieval_messages", [])
            plot_history = conversation.data_source.get("plot_history", [])

            retrieval_history = sync_retrieval_n_message(chats, retrieval_history)
            info_panel = retrieval_history[-1] if retrieval_history else "<h5><b>No evidence found.</b></h5>"
            plot_data = plot_history[-1] if plot_history else None

            return (
                conversation.id, conversation.name, chats, chat_suggestions, info_panel, plot_data, retrieval_history,
                plot_history, conversation.is_public, STATE, selected
            )
