import hashlib
import pandas as pd
import streamlit as st
from ktem.app import BasePage
from ktem.db.models import User, engine
from sqlmodel import Session, select
from theflow.settings import settings as flowsettings

USERNAME_RULE = """**Username rule:**

- Username is case-insensitive
- Username must be at least 3 characters long
- Username must be at most 32 characters long
- Username must contain only alphanumeric characters and underscores
"""

PASSWORD_RULE = """**Password rule:**

- Password must be at least 8 characters long
- Password must contain at least one uppercase letter
- Password must contain at least one lowercase letter
- Password must contain at least one digit
- Password must contain at least one special character from the following:
    ^ $ * . [ ] { } ( ) ? - " ! @ # % & / \\ , > < ' : ; | _ ~  + =
"""

def validate_username(usn):
    """Validate that whether username is valid

    Args:
        usn (str): Username
    """
    errors = []
    if len(usn) < 3:
        errors.append("Username must be at least 3 characters long")

    if len(usn) > 32:
        errors.append("Username must be at most 32 characters long")

    if not usn.replace("_", "").isalnum():
        errors.append(
            "Username must contain only alphanumeric characters and underscores"
        )

    return "; ".join(errors)


def validate_password(pwd, pwd_cnf):
    """Validate that whether password is valid

    - Password must be at least 8 characters long
    - Password must contain at least one uppercase letter
    - Password must contain at least one lowercase letter
    - Password must contain at least one digit
    - Password must contain at least one special character from the following:
        ^ $ * . [ ] { } ( ) ? - " ! @ # % & / \\ , > < ' : ; | _ ~  + =

    Args:
        pwd (str): Password
        pwd_cnf (str): Confirm password

    Returns:
        str: Error message if password is not valid
    """
    errors = []
    if pwd != pwd_cnf:
        errors.append("Password does not match")

    if len(pwd) < 8:
        errors.append("Password must be at least 8 characters long")

    if not any(c.isupper() for c in pwd):
        errors.append("Password must contain at least one uppercase letter")

    if not any(c.islower() for c in pwd):
        errors.append("Password must contain at least one lowercase letter")

    if not any(c.isdigit() for c in pwd):
        errors.append("Password must contain at least one digit")

    special_chars = "^$*.[]{}()?-\"!@#%&/\\,><':;|_~+="
    if not any(c in special_chars for c in pwd):
        errors.append(
            "Password must contain at least one special character from the "
            f"following: {special_chars}"
        )

    if errors:
        return "; ".join(errors)

    return ""


def create_user(usn, pwd, user_id=None, is_admin=True) -> bool:
    with Session(engine) as session:
        statement = select(User).where(User.username_lower == usn.lower())
        result = session.exec(statement).all()
        if result:
            print(f'User "{usn}" already exists')
            return False

        else:
            hashed_password = hashlib.sha256(pwd.encode()).hexdigest()
            user = User(
                id=user_id,
                username=usn,
                username_lower=usn.lower(),
                password=hashed_password,
                admin=is_admin,
            )
            session.add(user)
            session.commit()

            return True


class UserManagement:
    def __init__(self, app):
        self._app = app
        self.on_building_ui()
        if hasattr(flowsettings, "KH_FEATURE_USER_MANAGEMENT_ADMIN") and hasattr(
            flowsettings, "KH_FEATURE_USER_MANAGEMENT_PASSWORD"
        ):
            usn = flowsettings.KH_FEATURE_USER_MANAGEMENT_ADMIN
            pwd = flowsettings.KH_FEATURE_USER_MANAGEMENT_PASSWORD

            is_created = create_user(usn, pwd)
            if is_created:
                st.info(f'User "{usn}" created successfully')

    def on_building_ui(self):
        with st.expander("User list"):
            self.state_user_list = None
            self.user_list = st.dataframe(
                pd.DataFrame(columns=["id", "name", "admin"]),
                use_container_width=True
            )


            self._selected_panel = st.container()
            self.selected_user_id = None
            self.usn_edit = st.text_input("Username")
            self.pwd_edit = st.text_input("Change password", type="password")
            self.pwd_cnf_edit = st.text_input("Confirm change password", type="password")
            self.admin_edit = st.checkbox("Admin")

            self._selected_panel_btn = st.container()
            self.btn_edit_save = st.button("Save")
            self.btn_delete = st.button("Delete")
            self.btn_delete_yes = st.button("Confirm delete", key="confirm_delete", disabled=True)
            self.btn_delete_no = st.button("Cancel", key="cancel_delete", disabled=True)
            self.btn_close = st.button("Close")

        with st.expander("Create user"):
            self.usn_new = st.text_input("Username")
            self.pwd_new = st.text_input("Password", type="password")
            self.pwd_cnf_new = st.text_input("Confirm password", type="password")
            st.markdown(USERNAME_RULE)
            st.markdown(PASSWORD_RULE)
            self.btn_new = st.button("Create user")

    def on_register_events(self):
        self.btn_new.on_click(self.create_user)

    def on_subscribe_public_events(self):
        pass

    def create_user(self, usn, pwd, pwd_cnf):
        errors = validate_username(usn)
        if errors:
            st.warning(errors)
            return

        errors = validate_password(pwd, pwd_cnf)
        if errors:
            st.warning(errors)
            return

        with Session(engine) as session:
            statement = select(User).where(User.username_lower == usn.lower())
            result = session.exec(statement).all()
            if result:
                st.warning(f'Username "{usn}" already exists')
                return

            hashed_password = hashlib.sha256(pwd.encode()).hexdigest()
            user = User(
                username=usn, username_lower=usn.lower(), password=hashed_password
            )
            session.add(user)
            session.commit()
            st.info(f'User "{usn}" created successfully')

    def list_users(self, user_id):
        if user_id is None:
            return [], pd.DataFrame.from_records(
                [{"id": "-", "username": "-", "admin": "-"}]
            )

        with Session(engine) as session:
            statement = select(User).where(User.id == user_id)
            user = session.exec(statement).one()
            if not user.admin:
                return [], pd.DataFrame.from_records(
                    [{"id": "-", "username": "-", "admin": "-"}]
                )

            statement = select(User)
            results = [
                {"id": user.id, "username": user.username, "admin": user.admin}
                for user in session.exec(statement).all()
            ]
            if results:
                user_list = pd.DataFrame.from_records(results)
            else:
                user_list = pd.DataFrame.from_records(
                    [{"id": "-", "username": "-", "admin": "-"}]
                )

        return results, user_list

    def select_user(self, user_list, ev):
        if ev.value == "-" and ev.index[0] == 0:
            st.info("No user is loaded. Please refresh the user list")
            return -1

        if not ev.selected:
            return -1

        return user_list["id"][ev.index[0]]

    def on_selected_user_change(self, selected_user_id):
        if selected_user_id == -1:
            _selected_panel = st.empty()
            _selected_panel_btn = st.empty()
            btn_delete = st.empty()
            btn_delete_yes = st.empty()
            btn_delete_no = st.empty()
            usn_edit = ""
            pwd_edit = ""
            pwd_cnf_edit = ""
            admin_edit = False
        else:
            _selected_panel = st.empty()
            _selected_panel_btn = st.empty()
            btn_delete = st.empty()
            btn_delete_yes = st.empty()
            btn_delete_no = st.empty()

            with Session(engine) as session:
                statement = select(User).where(User.id == selected_user_id)
                user = session.exec(statement).one()

            usn_edit = user.username
            pwd_edit = ""
            pwd_cnf_edit = ""
            admin_edit = user.admin

        return (
            _selected_panel,
            _selected_panel_btn,
            btn_delete,
            btn_delete_yes,
            btn_delete_no,
            usn_edit,
            pwd_edit,
            pwd_cnf_edit,
            admin_edit,
        )

    def on_btn_delete_click(self, selected_user_id):
        if selected_user_id is None:
            st.warning("No user is selected")
            return

        st.empty()
        self.btn_delete_yes = st.button("Confirm delete", key="confirm_delete")
        self.btn_delete_no = st.button("Cancel", key="cancel_delete")

    def save_user(self, selected_user_id, usn, pwd, pwd_cnf, admin):
        errors = validate_username(usn)
        if errors:
            st.warning(errors)
            return

        if pwd:
            errors = validate_password(pwd, pwd_cnf)
            if errors:
                st.warning(errors)
                return

        with Session(engine) as session:
            statement = select(User).where(User.id == selected_user_id)
            user = session.exec(statement).one()
            user.username = usn
            user.username_lower = usn.lower()
            user.admin = admin
            if pwd:
                user.password = hashlib.sha256(pwd.encode()).hexdigest()
            session.commit()
            st.info(f'User "{usn}" updated successfully')

    def delete_user(self, current_user, selected_user_id):
        if current_user == selected_user_id:
            st.warning("You cannot delete yourself")
            return

        with Session(engine) as session:
            statement = select(User).where(User.id == selected_user_id)
            user = session.exec(statement).one()
            session.delete(user)
            session.commit()
            st.info(f'User "{user.username}" deleted successfully')
