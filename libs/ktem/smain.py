import streamlit as st
from decouple import config
from ktem.app import BaseApp
from ktem.pages.chat import ChatPage
from ktem.pages.help import HelpPage
from ktem.pages.resources import ResourcesTab
from ktem.pages.settings import SettingsPage
from ktem.pages.setup import SetupPage
from theflow.settings import settings as flowsettings

KH_DEMO_MODE = getattr(flowsettings, "KH_DEMO_MODE", False)
KH_SSO_ENABLED = getattr(flowsettings, "KH_SSO_ENABLED", False)
KH_ENABLE_FIRST_SETUP = getattr(flowsettings, "KH_ENABLE_FIRST_SETUP", False)
KH_APP_DATA_EXISTS = getattr(flowsettings, "KH_APP_DATA_EXISTS", True)

# Override first setup setting
if config("KH_FIRST_SETUP", default=False, cast=bool):
    KH_APP_DATA_EXISTS = False

class App(BaseApp):
    """The main app of Kotaemon using Streamlit"""

    def process_query(self, query: str) -> str:
        """
        Process a user query by:
          1. Retrieving relevant document context from all indices.
          2. Generating an answer using the reasoning pipeline (via ChatPage).
        """
        aggregated_context = ""
        for index in self.index_manager.indices:
            result = index.search(query)
            aggregated_context += result + "\n"

        if not aggregated_context.strip():
            aggregated_context = "No relevant context found."

        if hasattr(self, "chat_page") and hasattr(self.chat_page, "generate_response"):
            answer = self.chat_page.generate_response(query, aggregated_context)
        else:
            answer = f"Query: {query}\nContext:\n{aggregated_context}\n[Response generation is not implemented]"
        
        return answer

    def ui(self):
        """Render the UI using Streamlit"""
        st.set_page_config(page_title="Kotaemon", page_icon="🤖")
        st.title("Kotaemon - AI Assistant")

        if KH_ENABLE_FIRST_SETUP and not KH_APP_DATA_EXISTS:
            st.warning("Initial setup required.")
            self.setup_page = SetupPage(self)
            self.setup_page.render()
            return
        
        tab_names = ["Chat", "Resources", "Settings", "Help"]
        if self.f_user_management:
            tab_names.insert(0, "Login")
        
        tabs = st.tabs(tab_names)

        tab_index = 0
        if self.f_user_management:
            with tabs[tab_index]:
                from ktem.pages.login import LoginPage
                self.login_page = LoginPage(self)
                self.login_page.render()
            tab_index += 1

        with tabs[tab_index]:
            self.chat_page = ChatPage(self)
            self.chat_page.render()
        tab_index += 1

        if not KH_DEMO_MODE and not KH_SSO_ENABLED:
            with tabs[tab_index]:
                self.resources_page = ResourcesTab(self)
                self.resources_page.render()
            tab_index += 1

        with tabs[tab_index]:
            self.settings_page = SettingsPage(self)
            self.settings_page.render()
        tab_index += 1

        with tabs[tab_index]:
            self.help_page = HelpPage(self)
            self.help_page.render()

if __name__ == "__main__":
    app = App()
    app.ui()
