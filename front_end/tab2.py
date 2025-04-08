import streamlit as st
from datetime import datetime
import pandas as pd

# Set page configuration
st.set_page_config(
    page_title="Chat Files Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS for styling
st.markdown("""
<style>
    /* General styling */
    .stApp {
        background-color: #1e1e1e;
        color: #ffffff;
    }
    .header {
        font-size: 28px !important;
        font-weight: bold;
        color: #4CAF50;
        margin-bottom: 10px;
    }
    .subheader {
        font-size: 20px !important;
        font-weight: bold;
        color: #ffffff;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    .menu-item {
        display: inline-block;
        margin-right: 20px;
        font-weight: bold;
        color: #4CAF50;
        cursor: pointer;
        transition: color 0.3s;
    }
    .menu-item:hover {
        color: #ffffff;
    }
    .version {
        position: fixed;
        bottom: 10px;
        right: 10px;
        color: #888;
        font-size: 12px;
    }
    .table-header {
        display: grid;
        grid-template-columns: 1fr 3fr 2fr 1fr;
        font-weight: bold;
        padding: 10px 0;
        background-color: #2a2a2a;
        border-bottom: 2px solid #4CAF50;
        color: #ffffff;
    }
    .table-row {
        display: grid;
        grid-template-columns: 1fr 3fr 2fr 1fr;
        padding: 10px 0;
        border-bottom: 1px solid #444;
        transition: background-color 0.3s;
    }
    .table-row:hover {
        background-color: #333;
    }
    .action-button {
        background-color: #4CAF50 !important;
        color: white !important;
        border: none !important;
        border-radius: 5px !important;
        padding: 5px 15px !important;
        transition: background-color 0.3s;
    }
    .action-button:hover {
        background-color: #45a049 !important;
    }
    .sidebar .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .stTextInput>div>input {
        background-color: #2a2a2a;
        color: #ffffff;
        border: 1px solid #444;
        border-radius: 5px;
    }
    .stFileUploader>div {
        background-color: #2a2a2a;
        border: 1px solid #444;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar for navigation and additional features
with st.sidebar:
    st.title("Chat Files Dashboard")
    st.markdown("An open-source tool for managing and chatting with your files.")

    # Navigation menu
    nav_option = st.selectbox("Navigate", ["Dashboard", "Chat", "Files", "Settings", "Help"])

    if nav_option == "Dashboard":
        st.write("You are viewing the Dashboard.")
    elif nav_option == "Chat":
        st.write("Switch to Chat mode.")
    elif nav_option == "Files":
        st.write("Manage your files here.")
    elif nav_option == "Settings":
        st.write("Adjust settings.")
    elif nav_option == "Help":
        st.write("Get help here.")

    # File upload in sidebar
    st.subheader("Upload Files")
    uploaded_file = st.file_uploader("Upload a file", type=["pdf", "txt", "docx"])
    if uploaded_file:
        st.success(f"Uploaded: {uploaded_file.name}")

# Current time display
current_time = datetime.now().strftime("%H:%M.%f")[:11]
st.markdown(f'<div class="header">{current_time}</div>', unsafe_allow_html=True)

# Main title
st.markdown('<div class="subheader">Chat Files Dashboard</div>', unsafe_allow_html=True)

# Top menu bar
st.markdown("""
<div>
    <span class="menu-item">Resources</span>
    <span class="menu-item">Settings</span>
    <span class="menu-item">Help</span>
</div>
""", unsafe_allow_html=True)

# Secondary menu bar with tabs
st.markdown('<div class="subheader">Manage Collections</div>', unsafe_allow_html=True)
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Index Collections", "LLMs", "Embeddings", "Reconising", "Users"])

with tab1:
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 8])
    with col1:
        if st.button("View", key="view_btn", help="View selected collection"):
            st.write("Viewing selected collection...")
    with col2:
        if st.button("Add", key="add_btn", help="Add a new collection"):
            st.session_state.show_add_form = True

    # Add new collection form
    if "show_add_form" in st.session_state and st.session_state.show_add_form:
        with st.form("add_collection_form"):
            new_id = st.number_input("ID", min_value=1, step=1)
            new_name = st.text_input("Name")
            new_index_type = st.selectbox("Index Type", ["FileIndex", "GraphM6Index", "LightM6Index"])
            submit = st.form_submit_button("Submit")
            if submit:
                st.session_state.collections.append({
                    "id": new_id,
                    "name": new_name,
                    "Index Type": new_index_type
                })
                st.session_state.show_add_form = False
                st.success("Collection added successfully!")

    # Initialize session state for collections
    if "collections" not in st.session_state:
        st.session_state.collections = [
            {"id": 1, "name": "File Collection", "Index Type": "FileIndex"},
            {"id": 2, "name": "GraphM6 Collection", "Index Type": "GraphM6Index"},
            {"id": 3, "name": "LightM6 Collection", "Index Type": "LightM6Index"}
        ]

    # Table implementation using DataFrame
    st.markdown("""
    <div class="table-header">
        <div>id</div>
        <div>name</div>
        <div>Index Type</div>
        <div>Actions</div>
    </div>
    """, unsafe_allow_html=True)

    for idx, row in enumerate(st.session_state.collections):
        st.markdown(f"""
        <div class="table-row">
            <div>{row['id']}</div>
            <div>{row['name']}</div>
            <div>{row['Index Type']}</div>
            <div>
                <button class="action-button" onclick="alert('Edit functionality coming soon!')">Edit</button>
                <button class="action-button" style="background-color: #ff4444; margin-left: 5px;" onclick="alert('Delete functionality coming soon!')">Delete</button>
            </div>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.write("LLMs tab: Manage your language models here.")
    model_name = st.text_input("Add a new LLM")
    if st.button("Add LLM"):
        if model_name:
            st.success(f"Added LLM: {model_name}")

with tab3:
    st.write("Embeddings tab: Configure embeddings for your files.")
    embedding_type = st.selectbox("Select Embedding Type", ["BERT", "RoBERTa", "DistilBERT"])
    if st.button("Apply Embedding"):
        st.success(f"Applied {embedding_type} embedding.")

with tab4:
    st.write("Reconising tab: Placeholder for reconising configurations.")

with tab5:
    st.write("Users tab: Manage users and permissions.")
    user_name = st.text_input("Add a new user")
    if st.button("Add User"):
        if user_name:
            st.success(f"Added user: {user_name}")

# Version number at bottom right
st.markdown('<div class="version">version: 0.1.0.2</div>', unsafe_allow_html=True)