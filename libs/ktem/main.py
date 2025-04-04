import streamlit as st
st.set_page_config(layout="wide",page_title="Kotaemon", page_icon="🤖")
from decouple import config
from ktem.app import BaseApp
from ktem.pages.chat import ChatPage
from ktem.pages.help import HelpPage
from ktem.pages.resources import ResourcesTab
from ktem.pages.settings import SettingsPage
from ktem.pages.setup import SetupPage
from theflow.settings import settings as flowsettings
from ktem.pages.login import LoginPage  # Import refactored LoginPage

# Load settings
KH_DEMO_MODE = getattr(flowsettings, "KH_DEMO_MODE", False)
KH_SSO_ENABLED = getattr(flowsettings, "KH_SSO_ENABLED", False)
KH_ENABLE_FIRST_SETUP = getattr(flowsettings, "KH_ENABLE_FIRST_SETUP", False)
KH_APP_DATA_EXISTS = getattr(flowsettings, "KH_APP_DATA_EXISTS", True)

# Override first setup setting
if config("KH_FIRST_SETUP", default=False, cast=bool):
    KH_APP_DATA_EXISTS = False

# ⏩ Function: toggle_first_setup_visibility
def toggle_first_setup_visibility():
    is_first_setup = not KH_DEMO_MODE and not st.session_state.get("KH_APP_DATA_EXISTS", True)
    st.session_state["KH_APP_DATA_EXISTS"] = True
    st.session_state["current_tab"] = "setup" if is_first_setup else "chat"
    return is_first_setup

# ⏩ Function: toggle_login_visibility
def toggle_login_visibility(user_id):
    from ktem.db.engine import engine
    from ktem.db.models import User
    from sqlmodel import Session, select

    if not user_id:
        st.session_state["current_tab"] = "login"
        st.session_state["user_id"] = None
        st.session_state["is_admin"] = False
        return

    with Session(engine) as session:
        user = session.exec(select(User).where(User.id == user_id)).first()
        if user:
            st.session_state["user_id"] = user_id
            st.session_state["is_admin"] = user.admin
            st.session_state["current_tab"] = "chat"
        else:
            st.session_state["user_id"] = None
            st.session_state["is_admin"] = False
            st.session_state["current_tab"] = "login"


class App(BaseApp):
    """Kotaemon AI Assistant - Streamlit Version"""
    def __init__(self):
        super().__init__()  
        self.app_name = "Kotaemon"
        

    def ui(self):
        """Render the UI using Streamlit"""
        st.title("Kotaemon - AI Assistant")

        # Handle first-time setup
        if KH_ENABLE_FIRST_SETUP and not KH_APP_DATA_EXISTS:
            st.warning("Initial setup required.")
            SetupPage(self).render()
            return

        # Show login page if user is not authenticated
        if not st.session_state["user_id"]:
            LoginPage(self).render()  # Use the LoginPage class
            return

        # Logout button
        if st.button("Logout"):
            LoginPage(self).logout()

        # Define tabs
        tab_names = ["Chat", "Resources", "Settings", "Help"]
        
        tabs = st.tabs(tab_names)
        tab_index = 0

        # Chat Tab
        with tabs[tab_index]:
            ChatPage(self)
        tab_index += 1

        # Admin Tab (Visible only for admins)
        
        # Resources Tab
        if not KH_DEMO_MODE and not KH_SSO_ENABLED:
            with tabs[tab_index]:
                resource_tab = ResourcesTab(self)
                resource_tab.toggle_user_management(self.user_id)
            tab_index += 1

        # Settings Tab
        with tabs[tab_index]:
            SettingsPage(self)
        tab_index += 1

        # Help Tab
        with tabs[tab_index]:
            HelpPage(self).render()
    
    def on_subscribe_public_events(self):
        from ktem.db.engine import engine
        from ktem.db.models import User
        from sqlmodel import Session, select

        def toggle_login_visibility_streamlit(user_id):
            if not user_id:
                st.session_state["current_tab"] = "login"
                st.session_state["user_id"] = None
                st.session_state["is_admin"] = False
                return

            with Session(engine) as session:
                user = session.exec(select(User).where(User.id == user_id)).first()
                if not user:
                    st.session_state["current_tab"] = "login"
                    st.session_state["user_id"] = None
                    st.session_state["is_admin"] = False
                    return

                st.session_state["user_id"] = user.id
                st.session_state["is_admin"] = user.admin
                st.session_state["current_tab"] = "chat"


        def on_first_setup_complete():
            if KH_ENABLE_FIRST_SETUP:
                st.session_state["KH_APP_DATA_EXISTS"] = True
                st.session_state["current_tab"] = "chat"

    
    def _on_app_created():
        if KH_ENABLE_FIRST_SETUP:
            toggle_first_setup_visibility()

if __name__ == "__main__":
    app = App()
    app._on_app_created()
    app.ui()

