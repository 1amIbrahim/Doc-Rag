import streamlit as st
from sqlmodel import Session, select
from ktem.db.models import Settings, User, engine
from ktem.components import reasonings
from hashlib import sha256

class SettingsPageStreamlit:
    def __init__(self, app):
        self.app = app
        self.default_settings = app.default_settings

        if "user_id" not in st.session_state:
            st.session_state.user_id = "default"

        if "settings" not in st.session_state:
            st.session_state.settings = self.default_settings.flatten()

    def render(self):
        st.title("Settings")

        with st.expander("General Settings"):
            self.render_setting_group(self.default_settings.application.settings, "application")

        with st.expander("Retrieval Settings"):
            for index_id, group in self.default_settings.index.options.items():
                with st.container():
                    st.markdown(f"#### Index: {index_id}")
                    self.render_setting_group(group.settings, f"index.options.{index_id}")

        with st.expander("Reasoning Settings"):
            self.render_setting_group(self.default_settings.reasoning.settings, "reasoning")
            reasoning_choice = st.session_state.settings.get("reasoning.use", "")
            if reasoning_choice in self.default_settings.reasoning.options:
                st.markdown("#### Reasoning-specific Options")
                specific_group = self.default_settings.reasoning.options[reasoning_choice]
                self.render_setting_group(specific_group.settings, f"reasoning.options.{reasoning_choice}")

        if not getattr(self.app, "f_user_management", False):
            if st.button("Save Settings"):
                self.save_settings()
                st.success("Settings saved")

        if getattr(self.app, "f_user_management", False):
            with st.expander("User Settings"):
                self.render_user_settings()

    def render_setting_group(self, group, prefix):
        for name, setting in group.items():
            key = f"{prefix}.{name}"
            current_value = st.session_state.settings.get(key, setting.value)

            if setting.component == "text":
                st.session_state.settings[key] = st.text_input(setting.name, value=current_value)
            elif setting.component == "number":
                st.session_state.settings[key] = st.number_input(setting.name, value=current_value)
            elif setting.component == "checkbox":
                st.session_state.settings[key] = st.checkbox(setting.name, value=current_value)
            elif setting.component in ["dropdown", "radio"]:
                options = setting.choices
                if setting.component == "dropdown":
                    st.session_state.settings[key] = st.selectbox(setting.name, options, index=options.index(current_value))
                else:
                    st.session_state.settings[key] = st.radio(setting.name, options, index=options.index(current_value))
            elif setting.component == "checkboxgroup":
                st.session_state.settings[key] = st.multiselect(setting.name, options=setting.choices, default=current_value)
            else:
                st.warning(f"Unknown setting component: {setting.component}")

    def render_user_settings(self):
        user_id = st.session_state.user_id
        with Session(engine) as session:
            user = session.exec(select(User).where(User.id == user_id)).first()
            username = user.username if user else "Unknown"

        st.markdown(f"**Current User:** {username}")

        new_pass = st.text_input("New Password", type="password")
        confirm_pass = st.text_input("Confirm Password", type="password")

        if st.button("Change Password"):
            if new_pass != confirm_pass:
                st.error("Passwords do not match")
            else:
                self.change_password(user_id, new_pass)

    def change_password(self, user_id, new_password):
        hashed = sha256(new_password.encode()).hexdigest()
        with Session(engine) as session:
            user = session.exec(select(User).where(User.id == user_id)).first()
            if user:
                user.password = hashed
                session.add(user)
                session.commit()
                st.success("Password changed successfully")
            else:
                st.error("User not found")

    def save_settings(self):
        user_id = st.session_state.user_id
        settings_dict = st.session_state.settings

        with Session(engine) as session:
            record = session.exec(select(Settings).where(Settings.user == user_id)).first()
            if not record:
                record = Settings(user=user_id)

            record.setting = settings_dict
            session.add(record)
            session.commit()
