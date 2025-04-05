import streamlit as st
from ktem.app import BasePage
from theflow.settings import settings as flowsettings

KH_DEMO_MODE = getattr(flowsettings, "KH_DEMO_MODE", False)

# Placeholder text based on demo mode
if not KH_DEMO_MODE:
    PLACEHOLDER_TEXT = (
        "This is the beginning of a new conversation.\n"
        "Start by uploading a file or a web URL. "
        "Visit Files tab for more options (e.g: GraphRAG)."
    )
else:
    PLACEHOLDER_TEXT = (
        "Welcome to Kotaemon Demo. "
        "Start by browsing preloaded conversations to get onboard.\n"
        "Check out Hint section for more tips."
    )

class ChatPanel(BasePage):
    def __init__(self, app):
        self._app = app
        self.on_building_ui()

    def on_building_ui(self):
        """Builds the chat interface using Streamlit"""

        # Initialize chat history in session state
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        chat_container = st.container()

        with chat_container:
            for message in st.session_state.chat_history:
                role, text = message
                if role == "user":
                    st.markdown(f"**You:** {text}")
                else:
                    st.markdown(f"**Bot:** {text}")

        # Input box for chat
        chat_input = st.text_input("Type a message...", placeholder=PLACEHOLDER_TEXT)

        # Submit button
        if st.button("Send"):
            if chat_input:
                self.submit_msg(chat_input)

    def submit_msg(self, chat_input):
        """Handles sending a message to the chatbot"""
        # Append user message
        st.session_state.chat_history.append(("user", chat_input))
        # Simulate bot response (Replace this with an actual response from the AI model)
        
        
       
        st.rerun()
