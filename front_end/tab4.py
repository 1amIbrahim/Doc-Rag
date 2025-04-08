import streamlit as st

# Set page configuration
st.set_page_config(page_title="Document Chat Tool", layout="wide")

# Sidebar for navigation
with st.sidebar:
    st.title("Document Chat Tool")
    st.markdown("Version: 0.1.0")

    # About section
    st.header("About")
    st.markdown("""
    An open-source tool for chatting with your documents. Built with both end users and developers in mind.

    [Source Code](https://github.com) | [Hi! Space](https://space.com)
    """)

    # Navigation options
    nav_option = st.selectbox("Navigate", ["Chat", "Files", "Resources", "Settings", "Help"])

    if nav_option == "Chat":
        st.write("You are in Chat mode.")
    elif nav_option == "Files":
        st.write("Manage your files here.")
    elif nav_option == "Resources":
        st.write("Check out resources.")
    elif nav_option == "Settings":
        st.write("Adjust settings.")
    elif nav_option == "Help":
        st.write("Get help here.")

# Main content area
st.title("Document Chat Tool")

# User Guide Section
st.header("User Guide")
st.subheader("1. Add your AI models")
st.markdown("Follow the steps below to start chatting with your documents.")

# Tabs for different functionalities
tab1, tab2, tab3, tab4 = st.tabs(["Chat", "Files", "Resources", "Info"])

with tab1:
    st.header("Chat with Your Documents")

    # Placeholder for model selection
    model = st.selectbox("Choose your LLM", ["LLM 1", "LLM 2", "LLM 3"])
    st.write(f"Selected model: {model}")

    # File upload section
    uploaded_file = st.file_uploader("Upload a document", type=["pdf", "txt", "docx"])
    if uploaded_file is not None:
        st.write("File uploaded successfully!")
        st.write(f"File name: {uploaded_file.name}")

    # Chat input and output
    user_input = st.text_area("Ask a question about your document", height=100)
    if st.button("Send"):
        if user_input:
            # Placeholder for chat response (you would integrate an AI model here)
            st.write(f"**You:** {user_input}")
            st.write(
                f"**Bot:** This is a placeholder response. Integrate an AI model to process the document and respond.")

with tab2:
    st.header("Files")
    st.write("List of uploaded files will appear here.")
    if uploaded_file is not None:
        st.write(f"- {uploaded_file.name}")

with tab3:
    st.header("Resources")
    st.markdown("""
    - [Installation Guide](https://github.com)
    - [Developer Guide](https://github.com)
    - [Feedback](https://github.com)
    """)

with tab4:
    st.header("Info")
    st.markdown("Spec Description: This tool allows you to interact with your documents using AI models.")

# Add some styling (optional)
st.markdown("""
<style>
    .stApp {
        background-color: #1e1e1e;
        color: #ffffff;
    }
    .stSidebar {
        background-color: #2a2a2a;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
    }
</style>
""", unsafe_allow_html=True)