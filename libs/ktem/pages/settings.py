import hashlib
import streamlit as st
from ktem.app import BasePage
from ktem.components import reasonings
from ktem.db.models import Settings, User, engine
from sqlmodel import Session, select
from theflow.settings import settings as flowsettings

KH_SSO_ENABLED = getattr(flowsettings, "KH_SSO_ENABLED", False)

signout_js = """
function(u, c, pw, pwc) {
    removeFromStorage('username');
    removeFromStorage('password');
    return [u, c, pw, pwc];
}
"""

class SettingsPage(BasePage):
    """Responsible for allowing the users to customize the application"""

    public_events = ["onSignOut"]

    def __init__(self, app):
        """Initiate the page and render the UI"""
        self._app = app

        self._settings_state = st.session_state['settings_state']
        self._user_id = app.user_id
        self._default_settings = app.default_settings
        self._settings_dict = self._default_settings.flatten()
        self._settings_keys = list(self._settings_dict.keys())

        self._components = {}
        self._reasoning_mode = {}

        # store llms and embeddings components
        self._llms = []
        self._embeddings = []

        # render application page if there are application settings
        self._render_app_tab = False

        if not KH_SSO_ENABLED and self._default_settings.application.settings:
            self._render_app_tab = True

        # render index page if there are index settings (general and/or specific)
        self._render_index_tab = False

        if not KH_SSO_ENABLED:
            if self._default_settings.index.settings:
                self._render_index_tab = True
            else:
                for sig in self._default_settings.index.options.values():
                    if sig.settings:
                        self._render_index_tab = True
                        break

        # render reasoning page if there are reasoning settings
        self._render_reasoning_tab = False

        if not KH_SSO_ENABLED:
            if len(self._default_settings.reasoning.settings) > 1:
                self._render_reasoning_tab = True
            else:
                for sig in self._default_settings.reasoning.options.values():
                    if sig.settings:
                        self._render_reasoning_tab = True
                        break

        self.on_building_ui()

    def on_building_ui(self):
        if not KH_SSO_ENABLED:
            self.setting_save_btn = st.button(
                "Save & Close", key="save-setting-btn", on_click=self.save_setting
            )

        if self._app.f_user_management:
            with st.expander("User settings"):
                self.user_tab()

        self.app_tab()
        self.index_tab()
        self.reasoning_tab()
    def save_setting(self):
        user_id = self._user_id  # Ensure you have access to the user_id
        setting = self._settings_state
        if user_id is None:
            st.warning("Need to login before saving settings")
            return

        with Session(engine) as session:
            statement = select(Settings).where(Settings.user == user_id)
            try:
                user_setting = session.exec(statement).one()
            except Exception:
                user_setting = Settings()
                user_setting.user = user_id
            user_setting.setting = setting
            session.add(user_setting)
            session.commit()

        st.success("Settings saved")

    def on_subscribe_public_events(self):
        if self._app.f_user_management:
            self._app.subscribe_event(
                name="onSignIn",
                definition={
                    "fn": self.load_setting,
                    "inputs": self._user_id,
                    "outputs": [self._settings_state] + self.components(),
                    "show_progress": "hidden",
                },
            )

            def get_name(user_id):
                name = "Current user: "
                if user_id:
                    with Session(engine) as session:
                        statement = select(User).where(User.id == user_id)
                        result = session.exec(statement).all()
                        if result:
                            return name + result[0].username
                return name + "___"

            self._app.subscribe_event(
                name="onSignIn",
                definition={
                    "fn": get_name,
                    "inputs": self._user_id,
                    "outputs": [self.current_name],
                    "show_progress": "hidden",
                },
            )

    def on_register_events(self):
        if not KH_SSO_ENABLED:
            self.setting_save_btn.on_click(self.save_setting)

        if self._app.f_user_management and not KH_SSO_ENABLED:
            self.password_change_btn.on_click(self.change_password)
            self.signout.on_click(self.signout_function)

    def user_tab(self):
        # user management
        self.current_name = st.markdown("Current user: ___")

        if KH_SSO_ENABLED:
            import gradiologin as grlogin
            self.sso_signout = grlogin.LogoutButton("Logout")
        else:
            self.signout = st.button("Logout", key="logout_button")

            self.password_change = st.text_input(
                "New password", type="password", key="password_change"
            )
            self.password_change_confirm = st.text_input(
                "Confirm password", type="password", key="password_change_confirm"
            )
            self.password_change_btn = st.button("Change password", key="password_change_btn")

    def change_password(self, user_id, password, password_confirm):
        from ktem.pages.resources.user import validate_password

        errors = validate_password(password, password_confirm)
        if errors:
            st.warning(errors)
            return password, password_confirm

        with Session(engine) as session:
            statement = select(User).where(User.id == user_id)
            result = session.exec(statement).all()
            if result:
                user = result[0]
                hashed_password = hashlib.sha256(password.encode()).hexdigest()
                user.password = hashed_password
                session.add(user)
                session.commit()
                st.info("Password changed")
            else:
                st.warning("User not found")

        return "", ""

    def app_tab(self):
        if self._render_app_tab:
            with st.expander("General"):
                for n, si in self._default_settings.application.settings.items():
                    obj = self.render_setting_item(si, si.value)
                    self._components[f"application.{n}"] = obj
                    if si.special_type == "llm":
                        self._llms.append(obj)
                    if si.special_type == "embedding":
                        self._embeddings.append(obj)

    def index_tab(self):
        id2name = {k: v.name for k, v in self._app.index_manager.info().items()}
        if self._render_index_tab:  # Only render if the tab should be visible
            with st.expander("Retrieval settings"):
                for pn, sig in self._default_settings.index.options.items():
                    name = id2name.get(pn, f"<id {pn}>")
                    st.markdown(f"### {name}")  # Adding a header instead of nesting expanders
                    for n, si in sig.settings.items():
                        obj = self.render_setting_item(si, si.value)
                        self._components[f"index.options.{pn}.{n}"] = obj
                        if si.special_type == "llm":
                            self._llms.append(obj)
                        if si.special_type == "embedding":
                            self._embeddings.append(obj)

    def reasoning_tab(self):
        if self._render_reasoning_tab:  # Only render if the tab should be visible
            with st.expander("Reasoning settings"):
                for n, si in self._default_settings.reasoning.settings.items():
                    if n == "use":
                        continue
                    obj = self.render_setting_item(si, si.value)
                    self._components[f"reasoning.{n}"] = obj
                    if si.special_type == "llm":
                        self._llms.append(obj)
                    if si.special_type == "embedding":
                        self._embeddings.append(obj)

                st.markdown("### Reasoning-specific settings")
                self._components["reasoning.use"] = self.render_setting_item(
                    self._default_settings.reasoning.settings["use"],
                    self._default_settings.reasoning.settings["use"].value,
                )

                # Instead of nesting, display each reasoning option sequentially
                for idx, (pn, sig) in enumerate(self._default_settings.reasoning.options.items()):
                    st.markdown(f"### {pn}")
                    reasoning = reasonings.get(pn, None)
                    if reasoning is None:
                        st.markdown("**Name**: Description")
                    else:
                        info = reasoning.get_info()
                        st.markdown(f"**{info['name']}**: {info['description']}")
                    for n, si in sig.settings.items():
                        obj = self.render_setting_item(si, si.value)
                        self._components[f"reasoning.options.{pn}.{n}"] = obj
                        if si.special_type == "llm":
                            self._llms.append(obj)
                        if si.special_type == "embedding":
                            self._embeddings.append(obj)

    def render_setting_item(self, setting_item, value, unique_id=None):
        """
        Renders a single setting item based on its type and value.
        """
        component_type = setting_item.component

        # Ensure a truly unique key
        key = f"{setting_item.name}_{unique_id}" if unique_id else f"{setting_item.name}_{id(setting_item)}"

        if component_type == "text":
            return st.text_input(setting_item.name, value=value, key=key)
        
        elif component_type == "number":
            return st.number_input(setting_item.name, value=value, key=key)
        
        elif component_type == "boolean":
            return st.checkbox(setting_item.name, value=value, key=key)
        
        elif component_type == "select":
            return st.selectbox(setting_item.name, options=setting_item.choices, 
                                index=setting_item.choices.index(value) if value in setting_item.choices else 0, key=key)
        
        elif component_type == "multiselect":
            return st.multiselect(setting_item.name, options=setting_item.choices, default=value, key=key)
        
        elif component_type == "slider":
            return st.slider(setting_item.name, min_value=setting_item.metadata.get("min", 0), 
                            max_value=setting_item.metadata.get("max", 100), value=value, key=key)
        
        elif component_type == "password":
            return st.text_input(setting_item.name, value=value, type="password", key=key)

        else:
            st.warning(f"Unsupported component type: {component_type}")
            return None
