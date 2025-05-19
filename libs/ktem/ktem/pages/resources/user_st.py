import hashlib
import streamlit as st
import pandas as pd
from ktem.streamlit_app import StreamlitBaseApp
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
- Password must contain at least one special character from:
  ^ $ * . [ ] { } ( ) ? - " ! @ # % & / \\ , > < ' : ; | _ ~ + =
"""

class UserManagement(StreamlitBaseApp):
    def __init__(self, app):
        self._app = app
        self._selected_user_id = -1
        self._delete_confirm = False
        
        # Create default admin user if configured
        if hasattr(flowsettings, "KH_FEATURE_USER_MANAGEMENT_ADMIN") and hasattr(
            flowsettings, "KH_FEATURE_USER_MANAGEMENT_PASSWORD"
        ):
            usn = flowsettings.KH_FEATURE_USER_MANAGEMENT_ADMIN
            pwd = flowsettings.KH_FEATURE_USER_MANAGEMENT_PASSWORD
            if create_user(usn, pwd):
                st.success(f'User "{usn}" created successfully')

    def on_building_ui(self):
        tab1, tab2 = st.tabs(["User List", "Create User"])
        
        with tab1:
            self._render_user_list()
            
        with tab2:
            self._render_create_user()

    def _render_user_list(self):
        users_df = self._get_users_df()
        
        if users_df.empty:
            st.warning("No users found or you don't have permission")
            return
            
        st.dataframe(
            users_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": None,  # Hide ID column
                "username": "Username",
                "admin": "Admin"
            }
        )
        
        if st.button("Refresh List"):
            st.rerun()
            
        selected_user = st.selectbox(
            "Select a user to edit",
            options=[None] + users_df['username'].tolist()
        )
        
        if selected_user:
            self._render_user_edit(selected_user, users_df)

    def _render_user_edit(self, username, users_df):
        user_id = users_df[users_df['username'] == username]['id'].values[0]
        with Session(engine) as session:
            user = session.exec(select(User).where(User.id == user_id)).one()
            
        with st.form(f"edit_user_{user_id}"):
            usn = st.text_input("Username", value=user.username)
            pwd = st.text_input("Change Password", type="password")
            pwd_cnf = st.text_input("Confirm Password", type="password")
            is_admin = st.checkbox("Admin", value=user.admin)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Save"):
                    self._save_user(user_id, usn, pwd, pwd_cnf, is_admin)
            with col2:
                if st.form_submit_button("Delete"):
                    self._delete_confirm = True
                    
        if self._delete_confirm:
            st.warning("Are you sure you want to delete this user?")
            if st.button("Confirm Delete"):
                self._delete_user(user_id)
                self._delete_confirm = False
                st.rerun()
            if st.button("Cancel"):
                self._delete_confirm = False
                st.rerun()

    def _render_create_user(self):
        with st.form("create_user"):
            st.markdown(USERNAME_RULE)
            st.markdown(PASSWORD_RULE)
            
            usn = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            pwd_cnf = st.text_input("Confirm Password", type="password")
            is_admin = st.checkbox("Admin", value=False)
            
            if st.form_submit_button("Create User"):
                errors = validate_username(usn)
                if errors:
                    st.error(errors)
                    return
                    
                errors = validate_password(pwd, pwd_cnf)
                if errors:
                    st.error(errors)
                    return
                    
                if create_user(usn, pwd, is_admin=is_admin):
                    st.success(f'User "{usn}" created successfully')
                    st.rerun()

    def _get_users_df(self):
        if not hasattr(self._app, 'user_id') or not self._app.user_id:
            return pd.DataFrame(columns=["id", "username", "admin"])
            
        with Session(engine) as session:
            current_user = session.exec(select(User).where(User.id == self._app.user_id)).first()
            if not current_user or not current_user.admin:
                return pd.DataFrame(columns=["id", "username", "admin"])
                
            users = session.exec(select(User)).all()
            return pd.DataFrame([
                {"id": u.id, "username": u.username, "admin": u.admin} 
                for u in users
            ])

    def _save_user(self, user_id, usn, pwd, pwd_cnf, is_admin):
        errors = validate_username(usn)
        if errors:
            st.error(errors)
            return
            
        if pwd:
            errors = validate_password(pwd, pwd_cnf)
            if errors:
                st.error(errors)
                return
                
        with Session(engine) as session:
            user = session.exec(select(User).where(User.id == user_id)).one()
            user.username = usn
            user.username_lower = usn.lower()
            user.admin = is_admin
            if pwd:
                user.password = hashlib.sha256(pwd.encode()).hexdigest()
            session.commit()
            st.success(f'User "{usn}" updated successfully')
            st.rerun()

    def _delete_user(self, user_id):
        if self._app.user_id == user_id:
            st.error("You cannot delete yourself")
            return
            
        with Session(engine) as session:
            user = session.exec(select(User).where(User.id == user_id)).one()
            session.delete(user)
            session.commit()
            st.success(f'User "{user.username}" deleted successfully')

# Keep these utility functions outside the class
def validate_username(usn):
    """Same as original implementation"""
    errors = []
    if len(usn) < 3:
        errors.append("Username must be at least 3 characters long")
    if len(usn) > 32:
        errors.append("Username must be at most 32 characters long")
    if not usn.replace("_", "").isalnum():
        errors.append("Username must contain only alphanumeric characters and underscores")
    return "; ".join(errors)

def validate_password(pwd, pwd_cnf):
    """Same as original implementation"""
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
        errors.append(f"Password must contain at least one special character from: {special_chars}")
    return "; ".join(errors)

def create_user(usn, pwd, user_id=None, is_admin=True):
    with Session(engine) as session:
        existing_user = session.exec(select(User).where(User.username_lower == usn.lower())).first()
        if existing_user:
            st.error(f'User "{usn}" already exists. Please choose a different username.')
            return False
        print(f"Creating user: {usn}")  # Debugging line
        hashed_password = hashlib.sha256(pwd.encode()).hexdigest()
        new_user = User(
            id=user_id,
            username=usn,
            username_lower=usn.lower(),
            password=hashed_password,
            admin=is_admin,
        )
        session.add(new_user)
        session.commit()
        st.success(f'User "{usn}" has been successfully created.')
        return True
