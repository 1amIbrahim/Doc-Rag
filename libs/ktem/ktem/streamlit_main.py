import streamlit as st
from decouple import config
from ktem.streamlit_app import StreamlitBaseApp
from ktem.pages.chat.streamlit_chat import ChatPageStreamlit
from ktem.pages.help import HelpPage
from ktem.pages.resources import ResourcesTab
from ktem.pages.streamlit_settings import SettingsPage
from ktem.pages.setup import SetupPage
from ktem.pages.login import LoginPage
from theflow.settings import settings as flowsettings

# Feature flags
KH_DEMO_MODE = getattr(flowsettings, "KH_DEMO_MODE", False)
KH_SSO_ENABLED = getattr(flowsettings, "KH_SSO_ENABLED", False)
KH_ENABLE_FIRST_SETUP = getattr(flowsettings, "KH_ENABLE_FIRST_SETUP", False)
KH_APP_DATA_EXISTS = getattr(flowsettings, "KH_APP_DATA_EXISTS", True)

# Override via .env
if config("KH_FIRST_SETUP", default=False, cast=bool):
    KH_APP_DATA_EXISTS = False


def should_show_first_setup():
    return not KH_DEMO_MODE and not KH_APP_DATA_EXISTS


class App(StreamlitBaseApp):
    def ui(self):
        print("...................HELLO THIS UI IS RUNNING..............")
        self._tabs = {}

        # Step 1: First-time setup
        if KH_ENABLE_FIRST_SETUP and should_show_first_setup():
            st.session_state.show_tabs = False
            SetupPage(self).render()
            return

        # Step 2: Define all tabs
        tabs = ["Welcome", "Chat", "Resources", "Settings", "Help"]
        tab_map = {
            "Welcome": LoginPage(self),
            "Chat": ChatPageStreamlit(self),
            "Resources": ResourcesTab(self),
            "Settings": SettingsPage(self),
            "Help": HelpPage(self),
        }

        # Step 3: Sidebar Navigation
        selected_tab = st.sidebar.radio("Navigation", tabs)

        # Step 4: Login control
        if self.f_user_management and not self.user_id:
            if selected_tab != "Welcome":
                st.warning("⚠️ Please log in to access this page.")
                return
            else:
                # If on Welcome tab and not logged in
                tab_map["Welcome"].render()
                return

        # Step 5: Render only selected tab (no overlap)
        if selected_tab == "Files" and isinstance(tab_map[selected_tab], dict):
            subtab_names = list(tab_map[selected_tab].keys())
            selected_subtab = st.selectbox("Choose Index", subtab_names, key="selected_sub_index")
            tab_map[selected_tab][selected_subtab].render()
        else:
            tab_map[selected_tab].render()

    def on_subscribe_public_events(self):
        if self.f_user_management:
            from ktem.db.engine import engine
            from ktem.db.models import User
            from sqlmodel import Session, select

            def toggle_login_visibility(user_id):
                if not user_id:
                    st.session_state.show_tabs = False
                    st.experimental_rerun()

                with Session(engine) as session:
                    user = session.exec(select(User).where(User.id == user_id)).first()

                is_admin = user.admin if user else False
                st.session_state.is_admin = is_admin
                st.session_state.show_tabs = True
                st.experimental_rerun()

            self.register_event("onSignIn", toggle_login_visibility)
            self.register_event("onSignOut", lambda uid: toggle_login_visibility(None))

        if KH_ENABLE_FIRST_SETUP:
            def handle_first_setup_complete():
                st.session_state.show_tabs = True
                st.experimental_rerun()

            self.register_event("onFirstSetupComplete", handle_first_setup_complete)

    def _on_app_created(self):
        if KH_ENABLE_FIRST_SETUP:
            st.session_state.show_tabs = not should_show_first_setup()
