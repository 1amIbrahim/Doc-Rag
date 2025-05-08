import streamlit as st
from decouple import config
from ktem.streamlit_app import StreamlitBaseApp
from ktem.pages.chat.streamlit_chat import ChatPageStreamlit
from ktem.pages.help import HelpPage
from ktem.pages.resources import ResourcesTab
from ktem.pages.streamlit_settings import SettingsPageStreamlit
from ktem.pages.setup import SetupPage
from theflow.settings import settings as flowsettings

KH_DEMO_MODE = getattr(flowsettings, "KH_DEMO_MODE", False)
KH_SSO_ENABLED = getattr(flowsettings, "KH_SSO_ENABLED", False)
KH_ENABLE_FIRST_SETUP = getattr(flowsettings, "KH_ENABLE_FIRST_SETUP", False)
KH_APP_DATA_EXISTS = getattr(flowsettings, "KH_APP_DATA_EXISTS", True)

# override first setup setting
if config("KH_FIRST_SETUP", default=False, cast=bool):
    KH_APP_DATA_EXISTS = False


def should_show_first_setup():
    return not KH_DEMO_MODE and not KH_APP_DATA_EXISTS


class App(StreamlitBaseApp):
    def ui(self):
        """Render the UI"""
        self._tabs = {}
        self.user_id = st.session_state.user_id
        print(self.user_id)
        # Handle first setup
        if KH_ENABLE_FIRST_SETUP and should_show_first_setup():
            print("__SetupPage()__")
            st.session_state.show_tabs = False
            SetupPage(self).render()
            return

        st.session_state.show_tabs = True

        tabs = ["Chat"]
        tab_map = {"Chat": ChatPageStreamlit(self)}

        if self.f_user_management:
            print("__LoginPage__")
            from ktem.pages.streamlit_login import LoginPage
            tabs.insert(0, "Welcome")
            tab_map["Welcome"] = LoginPage(self)

        #if not self.f_user_management and not KH_DEMO_MODE:
        if len(self.index_manager.indices) == 1:
            index = self.index_manager.indices[0]
            tabs.append(index.name)
            tab_map[index.name] = index.get_index_page_ui()
        elif len(self.index_manager.indices) > 1:
            tabs.append("Files")
            tab_map["Files"] = {i.name: i.get_index_page_ui() for i in self.index_manager.indices}

        if not KH_DEMO_MODE:
            if not KH_SSO_ENABLED:
                
                tabs.append("Resources")
                tab_map["Resources"] = ResourcesTab(self)
            tabs.append("Settings")
            tab_map["Settings"] = SettingsPageStreamlit(self)

        tabs.append("Help")
        tab_map["Help"] = HelpPage(self)

        selected_tab = st.sidebar.radio("Navigation", tabs)

        if selected_tab == "Files" and isinstance(tab_map[selected_tab], dict):
            subtab_names = list(tab_map[selected_tab].keys())
            selected_subtab = st.selectbox("Choose Index", subtab_names, key="selected_sub_index")

            # Render the selected index UI inside a Streamlit container
            with st.container():
                st.markdown(f"### 📁 {selected_subtab}")
                selected_index_ui = tab_map[selected_tab][selected_subtab]

                if hasattr(selected_index_ui, "render_ui"):
                    selected_index_ui.render_ui()
                elif callable(selected_index_ui):
                    selected_index_ui()
                else:
                    st.warning("Unsupported index UI component.")


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
            if should_show_first_setup():
                st.session_state.show_tabs = False
            else:
                st.session_state.show_tabs = True
