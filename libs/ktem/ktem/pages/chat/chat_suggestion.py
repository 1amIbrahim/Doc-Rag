import streamlit as st
from ktem.app import BasePage
from theflow.settings import settings as flowsettings


class ChatSuggestion(BasePage):
    CHAT_SAMPLES = getattr(
        flowsettings,
        "KH_FEATURE_CHAT_SUGGESTION_SAMPLES",
        [
            "Summarize this document",
            "Generate a FAQ for this document",
            "Identify the main highlights in bullet points",
        ],
    )

    def __init__(self, app):
        self._app = app
        self.on_building_ui()

    def on_building_ui(self):
        st.session_state.setdefault("chat_samples", self.CHAT_SAMPLES)

        if getattr(flowsettings, "KH_FEATURE_CHAT_SUGGESTION", False):
            with st.expander("Chat Suggestion", expanded=True):
                self.show_suggestions()

    def show_suggestions(self):
        st.markdown("### Suggested Questions")
        for sample in self.CHAT_SAMPLES:
            if st.button(sample):
                st.session_state["selected_example"] = sample
                st.toast(f"Selected: {sample}")

    def get_selected_example(self):
        return st.session_state.get("selected_example", "")
