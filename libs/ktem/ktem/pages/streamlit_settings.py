import hashlib
import streamlit as st
from ktem.app import BasePage
from ktem.components import reasonings
from ktem.db.models import Settings, User, engine
from sqlmodel import Session, select
from theflow.settings import settings as flowsettings

KH_SSO_ENABLED = getattr(flowsettings, "KH_SSO_ENABLED", False)

def render_setting_item(setting_item, value, full_key_path=None):
    # Generate a unique Streamlit key per widget to prevent duplicate element errors
    key = full_key_path if full_key_path else f"{setting_item.name}_{setting_item.component}"
    kwargs = {
        "label": setting_item.name,
        "key": key,
    }

    if setting_item.component == "text":
        return st.text_input(**kwargs, value=value)

    elif setting_item.component == "number":
        return st.number_input(**kwargs, value=value)

    elif setting_item.component == "checkbox":
        return st.checkbox(**kwargs, value=value)

    elif setting_item.component == "dropdown":
        if value not in setting_item.choices:
            st.warning(f"⚠️ '{value}' is not a valid option for '{setting_item.name}'. Using default.")
            index = 0
        else:
            index = setting_item.choices.index(value)
        return st.selectbox(**kwargs, options=setting_item.choices, index=index)

    elif setting_item.component == "radio":
        if value not in setting_item.choices:
            st.warning(f"⚠️ '{value}' is not a valid option for '{setting_item.name}'. Using default.")
            index = 0
        else:
            index = setting_item.choices.index(value)
        return st.radio(**kwargs, options=setting_item.choices, index=index)

    elif setting_item.component == "checkboxgroup":
        if not isinstance(value, list):
            value = []
        default = [v for v in value if v in setting_item.choices]
        return st.multiselect(**kwargs, options=setting_item.choices, default=default)

    else:
        raise ValueError(f"Unknown component {setting_item.component}")


class SettingsPage(BasePage):
    public_events = ["onSignOut"]

    def __init__(self, app):
        self._app = app
        self._settings_state = st.session_state.settings
        self._user_id = app.user_id
        self._default_settings = app.default_settings
        self._settings_dict = self._default_settings.flatten()
        self._settings_keys = list(self._settings_dict.keys())
        self._components = {}
        self._reasoning_mode = {}
        self._llms = []
        self._embeddings = []

        self._render_app_tab = False
        if not KH_SSO_ENABLED and self._default_settings.application.settings:
            self._render_app_tab = True

        self._render_index_tab = False
        if not KH_SSO_ENABLED:
            if self._default_settings.index.settings:
                self._render_index_tab = True
            else:
                for sig in self._default_settings.index.options.values():
                    if sig.settings:
                        self._render_index_tab = True
                        break

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
        st.title("Settings")
        if self._app.f_user_management:
            with st.expander("User Settings"):
                self.user_tab()

        if self._render_app_tab:
            with st.expander("General Settings"):
                self.app_tab()

        if self._render_index_tab:
            with st.expander("Retrieval Settings"):
                self.index_tab()

        if self._render_reasoning_tab:
            with st.expander("Reasoning Settings"):
                self.reasoning_tab()

        if not KH_SSO_ENABLED:
            if st.button("Save & Close"):
                setting = self.save_setting(self._user_id, *self.components())
                st.success("Settings Saved")

    def on_subscribe_public_events(self):
        pass

    def on_register_events(self):
        pass

    def user_tab(self):
        st.markdown("### User Info")
        st.write(f"Current User ID: {self._user_id}")

        if KH_SSO_ENABLED:
            st.button("Logout")
        else:
            new_pw = st.text_input("New password", type="password")
            confirm_pw = st.text_input("Confirm password", type="password")
            if st.button("Change Password"):
                self.change_password(self._user_id, new_pw, confirm_pw)
            if st.button("Sign Out"):
                self._user_id = None
                st.success("Signed Out")

    def change_password(self, user_id, password, password_confirm):
        from ktem.pages.resources.user import validate_password

        errors = validate_password(password, password_confirm)
        if errors:
            st.warning(errors)
            return

        with Session(engine) as session:
            statement = select(User).where(User.id == user_id)
            result = session.exec(statement).all()
            if result:
                user = result[0]
                hashed_password = hashlib.sha256(password.encode()).hexdigest()
                user.password = hashed_password
                session.add(user)
                session.commit()
                st.success("Password changed")
            else:
                st.warning("User not found")

    def app_tab(self):
        for n, si in self._default_settings.application.settings.items():
            value = si.value
            full_key = f"application.{n}"
            obj = render_setting_item(si, value, full_key_path=full_key)
            self._components[full_key] = obj

    def index_tab(self):
        id2name = {k: v.name for k, v in self._app.index_manager.info().items()}
        for pn, sig in self._default_settings.index.options.items():
            st.markdown(f"### {id2name.get(pn, f'<id {pn}>')} settings")
            for n, si in sig.settings.items():
                value = si.value
                full_key = f"index.options.{pn}.{n}"
                obj = render_setting_item(si, value, full_key_path=full_key)
                self._components[full_key] = obj

    def reasoning_tab(self):
        st.markdown("### General Reasoning Settings")
        for n, si in self._default_settings.reasoning.settings.items():
            if n == "use":
                continue
            full_key = f"reasoning.{n}"
            obj = render_setting_item(si, si.value, full_key_path=full_key)
            self._components[full_key] = obj

        st.markdown("### Reasoning Modes")
        use_setting = self._default_settings.reasoning.settings["use"]
        use_key = "reasoning.use"
        use_mode = render_setting_item(use_setting, use_setting.value, full_key_path=use_key)
        self._components[use_key] = use_mode

        selected_mode = use_mode
        for pn, sig in self._default_settings.reasoning.options.items():
            if pn == selected_mode:
                with st.expander(f"Reasoning Mode: {pn}", expanded=True):
                    for n, si in sig.settings.items():
                        value = si.value
                        full_key = f"reasoning.options.{pn}.{n}"
                        obj = render_setting_item(si, value, full_key_path=full_key)
                        self._components[full_key] = obj

    def change_reasoning_mode(self, value):
        pass

    def load_setting(self, user_id=None):
        settings = self._settings_dict
        with Session(engine) as session:
            statement = select(Settings).where(Settings.user == user_id)
            result = session.exec(statement).all()
            if result:
                settings = result[0].setting

        output = [settings]
        output += tuple(settings[name] for name in self.component_names())
        return output

    def save_setting(self, user_id: int, *args):
        setting = {key: value for key, value in zip(self.component_names(), args)}
        if user_id is None:
            st.warning("Need to login before saving settings")
            return setting

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

        return setting

    def components(self) -> list:
        output = []
        for name in self._settings_keys:
            output.append(self._components[name])
        return output

    def component_names(self):
        return self._settings_keys

    def _on_app_created(self):
        pass
