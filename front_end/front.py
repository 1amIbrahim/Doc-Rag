import streamlit as st
from streamlit_chat import message
import random
import time
import datetime
import base64
# Set page configuration
st.set_page_config(
    page_title="AI Chat Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Custom CSS for professional styling with dark mode support
st.markdown("""
<style>
    :root {
        --primary-color: #2979FF;
        --secondary-color: #E3E6EC;
        --accent-color: #FF3B3B;
        --text-color: #000000;  /* Changed to pure black for light mode */
        --light-text: #F5F5F5;
        --dark-bg: #121212;
        --chatbox-color: #FFFFFF;
        --tools-bg: #F1F5F9;
        --border-color: rgba(0, 0, 0, 0.1);
    }

    [data-theme="dark"] {
        --secondary-color: #1a1a2e;
        --text-color: #f0f2f6;
        --dark-bg: #0e0e1a;
        --chatbox-color: #1E1E1E;
        --tools-bg: #1E1E1E;
        --border-color: rgba(255, 255, 255, 0.1);
    }

    /* Main container for three-panel layout */
    .main-app-container {
        display: flex;
        height: calc(100vh - 2rem);
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
    }

    .left-sidebar {
        width: 280px;
        height: 100%;
        background-color: var(--dark-bg);
        color: var(--light-text);
        overflow-y: auto;
        padding: 1rem;
        border-right: 1px solid var(--border-color);
        flex-shrink: 0;
    }

    .main-content-area {
        flex: 1;
        height: 100%;
        overflow-y: auto;
        padding: 1.5rem;
        background-color: var(--secondary-color);
    }

    .right-sidebar {
        width: 300px;
        height: 100%;
        background-color: var(--tools-bg);
        overflow-y: auto;
        padding: 1rem;
        flex-shrink: 0;
        border-left: 1px solid var(--border-color);
    }

    .stApp {
        background-color: var(--secondary-color);
        transition: all 0.3s;
    }

    /* Apply text color to all text elements */
    body, .stTextInput>div>div>input, .st-bb, .st-at, .st-ae, .st-af, .st-ag, .stMarkdown, 
    .stAlert, .stNotification, .subheader, .timestamp, .file-history-item,
    .chat-container, .bot-message, .stTextArea>div>div>textarea {
        color: var(--text-color) !important;
    }

    .chat-container {
        background-color: var(--chatbox-color);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        height: 65vh;
        overflow-y: auto;
        margin-bottom: 1rem;
        transition: all 0.3s;
    }

    .stTextInput>div>div>input {
        border-radius: 20px;
        padding: 10px 15px;
        background-color: var(--chatbox-color);
        caret-color: var(--text-color);
    }

    .header {
        color: var(--primary-color);
        margin-bottom: 0.5rem;
    }

    .subheader {
        opacity: 0.8;
        font-size: 0.9rem;
    }

    .chat-input-container {
        display: flex;
        gap: 10px;
    }

    .chat-input {
        flex-grow: 1;
    }

    .send-button {
        align-self: flex-end;
    }

    .file-uploader {
        margin-bottom: 1rem;
    }

    .history-item {
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s;
        color: var(--light-text);
    }

    .history-item:hover {
        background-color: rgba(79, 139, 249, 0.1);
    }

    .active-chat {
        background-color: rgba(79, 139, 249, 0.2);
        font-weight: 500;
    }

    .timestamp {
        font-size: 0.7rem;
        opacity: 0.6;
        margin-top: 2px;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 8px 8px 0 0;
        transition: all 0.2s;
        color: var(--text-color);
    }

    .stTabs [aria-selected="true"] {
        background-color: var(--primary-color);
        color: white !important;
    }

    .stTabs [aria-selected="false"] {
        background-color: var(--secondary-color);
    }

    /* Tool sections */
    .tool-section {
        margin-bottom: 1.5rem;
        padding: 1.25rem;
        background-color: var(--chatbox-color);
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid var(--border-color);
    }

    /* Notes textarea */
    .notes-textarea {
        width: 100%;
        min-height: 200px;
        padding: 0.75rem;
        border-radius: 8px;
        border: 1px solid var(--border-color);
        font-family: inherit;
        background-color: var(--chatbox-color);
        color: var(--text-color);
    }

    /* Message styling */
    .user-message {
        background-color: var(--primary-color);
        color: white !important;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }

    .bot-message {
        background-color: var(--chatbox-color);
        border: 1px solid var(--border-color);
        margin-right: auto;
        border-bottom-left-radius: 4px;
    }

    /* Fix for graphviz */
    .stGraphviz {
        width: 100% !important;
    }

    /* Hide the default scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }

    ::-webkit-scrollbar-track {
        background: var(--secondary-color);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--primary-color);
        border-radius: 3px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'history' not in st.session_state:
    st.session_state['history'] = []

if 'current_chat' not in st.session_state:
    st.session_state['current_chat'] = None

if 'chat_sessions' not in st.session_state:
    st.session_state['chat_sessions'] = []

if 'uploaded_files_history' not in st.session_state:
    st.session_state['uploaded_files_history'] = []

if 'dark_mode' not in st.session_state:
    st.session_state['dark_mode'] = False

if 'active_tool' not in st.session_state:
    st.session_state['active_tool'] = "graph"

if 'quick_notes' not in st.session_state:
    st.session_state['quick_notes'] = ""

# Sample bot responses
BOT_RESPONSES = [
    "I've analyzed your query and here's what I found...",
    "Based on my knowledge, I can provide the following information...",
    "Thank you for your question. Here's a detailed response...",
    "After considering your request, I recommend the following approach...",
    "I understand you're asking about this topic. Here are the key points...",
    "That's an excellent question. Here's what my analysis shows...",
    "I've processed your input and generated this response for you...",
    "Here's a comprehensive answer to your inquiry..."
]


def new_chat_session():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    session_id = f"chat_{len(st.session_state['chat_sessions']) + 1}{timestamp.replace(' ', '')}"
    st.session_state['chat_sessions'].append({
        'id': session_id,
        'title': f"Chat {len(st.session_state['chat_sessions']) + 1}",
        'timestamp': timestamp,
        'messages': []
    })
    st.session_state['current_chat'] = session_id
    st.session_state['history'] = []
    # Maintain dark mode when creating new chat
    if st.session_state['dark_mode']:
        toggle_dark_mode(force_dark=True)


def toggle_dark_mode(force_dark=None):
    if force_dark is not None:
        st.session_state['dark_mode'] = force_dark
    else:
        st.session_state['dark_mode'] = not st.session_state['dark_mode']

    if st.session_state['dark_mode']:
        st.markdown("""
        <style>
            :root {
                --text-color: #f0f2f6;
                --secondary-color: #1a1a2e;
                --dark-bg: #0e0e1a;
                --chatbox-color: #1E1E1E;
                --tools-bg: #1E1E1E;
                --border-color: rgba(255, 255, 255, 0.1);
            }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
            :root {
                --text-color: #000000;
                --secondary-color: #E3E6EC;
                --chatbox-color: #FFFFFF;
                --tools-bg: #F1F5F9;
                --border-color: rgba(0, 0, 0, 0.1);
            }
        </style>
        """, unsafe_allow_html=True)


def generate_entity_graph():
    # Create a simple entity relationship graph using DOT language
    dot = """
    digraph {
        node [shape=box, style="rounded", fontname="Arial"];
        edge [arrowhead=vee];
        rankdir=LR;

        "AI" -> "Machine Learning"
        "AI" -> "Data Science"
        "Machine Learning" -> "Neural Networks"
        "Machine Learning" -> "Data Science"
        "Data Science" -> "Python"
    }
    """
    return dot


# Main layout structure using columns instead of raw HTML
col1, col2, col3 = st.columns([0.8, 1.5, 0.8], gap="medium")

# Left sidebar content
with col1:
    st.markdown("""
    <style>
        [data-testid="stVerticalBlock"] {
            padding-right: 1rem;
            width: 100% !important;
        }
    </style>
    """, unsafe_allow_html=True)

    st.title("Chat Sessions")

    if st.button("➕ New Chat", use_container_width=True):
        new_chat_session()

    st.markdown("---")
    st.subheader("Chat History")

    for i, session in enumerate(st.session_state['chat_sessions']):
        is_active = session['id'] == st.session_state.get('current_chat')
        st.markdown(
            f"""
            <div class="history-item {'active-chat' if is_active else ''}" onclick="alert('Clicked {session['id']}')">
                <div>{session['title']}</div>
                <div class="timestamp">{session['timestamp']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.subheader("Upload Options")

    upload_tab, url_tab, history_tab = st.tabs(["📁 Upload", "🌐 Paste URL", "🗂 History"])

    with upload_tab:
        uploaded_files = st.file_uploader(
            "Upload documents for analysis",
            type=['pdf', 'txt', 'docx', 'pptx', 'xlsx'],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        if uploaded_files:
            for uploaded_file in uploaded_files:
                st.success(f"📄 {uploaded_file.name} uploaded successfully")
                st.session_state['uploaded_files_history'].append({
                    'name': uploaded_file.name,
                    'type': uploaded_file.type,
                    'size': f"{uploaded_file.size / 1024:.1f} KB",
                    'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                })

    with url_tab:
        url = st.text_input(
            "Enter document URL",
            placeholder="https://example.com/document.pdf",
            label_visibility="collapsed"
        )
        if st.button("Process URL", use_container_width=True):
            if url:
                try:
                    if url.startswith(('http://', 'https://')):
                        st.success(f"🌐 URL submitted successfully: {url}")
                        st.session_state['uploaded_files_history'].append({
                            'name': url,
                            'type': 'URL',
                            'size': 'N/A',
                            'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                    else:
                        st.error("Please enter a valid URL starting with http:// or https://")
                except Exception as e:
                    st.error(f"Error processing URL: {str(e)}")
            else:
                st.warning("Please enter a URL first")

    with history_tab:
        if not st.session_state['uploaded_files_history']:
            st.info("No files or URLs uploaded yet")
        else:
            for file in reversed(st.session_state['uploaded_files_history']):
                st.markdown(
                    f"""
                    <div class="file-history-item">
                        <strong>{file['name']}</strong><br>
                        <small>Type: {file['type']} | Size: {file['size']} | {file['date']}</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

# Main chat content
with col2:
    st.markdown("""
    <style>
        [data-testid="stVerticalBlock"] {
            width: 100% !important;
            max-width: 100% !important;
            padding: 0 1rem;
        }
        .stTextInput>div>div>input {
            width: 100% !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Dark mode toggle button
    col1, col2 = st.columns([10, 1])
    with col1:
        st.markdown(f"<h1 class='header'>AI Assistant</h1>", unsafe_allow_html=True)
        st.markdown("<p class='subheader'>Ask questions, get insights, and analyze documents</p>",
                    unsafe_allow_html=True)

    with col2:
        if st.button("🌙" if not st.session_state['dark_mode'] else "☀", key="dark_mode_toggle"):
            toggle_dark_mode()

    # Chat container
    with st.container():
        st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

        if st.session_state['current_chat']:
            current_session = next(
                (s for s in st.session_state['chat_sessions']
                 if s['id'] == st.session_state['current_chat']),
                None
            )

            if current_session:
                for i, chat in enumerate(current_session['messages']):
                    if chat['is_user']:
                        message(
                            chat['message'],
                            is_user=True,
                            key=f"user_{i}",
                            avatar_style="identicon",
                            seed="user"
                        )
                    else:
                        message(
                            chat['message'],
                            key=f"bot_{i}",
                            avatar_style="bottts",
                            seed="bot"
                        )

        st.markdown("</div>", unsafe_allow_html=True)

    # Chat input with send button
    input_col, btn_col = st.columns([6, 1])
    with input_col:
        user_input = st.text_input(
            "Type your message...",
            key="input",
            label_visibility="collapsed",
            placeholder="Ask me anything..."
        )
    with btn_col:
        send_button = st.button("⬆", use_container_width=True)

    if (user_input and send_button) or (user_input and st.session_state.input):
        if st.session_state['current_chat']:
            current_session = next(
                (s for s in st.session_state['chat_sessions']
                 if s['id'] == st.session_state['current_chat']),
                None
            )

            if current_session:
                current_session['messages'].append({
                    'message': user_input,
                    'is_user': True,
                    'timestamp': datetime.datetime.now().strftime("%H:%M")
                })

                with st.spinner("Analyzing your query..."):
                    time.sleep(random.uniform(0.7, 1.8))

                    bot_response = random.choice(BOT_RESPONSES)
                    current_session['messages'].append({
                        'message': bot_response,
                        'is_user': False,
                        'timestamp': datetime.datetime.now().strftime("%H:%M")
                    })

                    if len(current_session['messages']) == 2:
                        first_msg = current_session['messages'][0]['message']
                        current_session['title'] = first_msg[:30] + ("..." if len(first_msg) > 30 else "")

                    st.experimental_rerun()
        else:
            new_chat_session()
            st.experimental_rerun()

# Right sidebar tools
with col3:
    st.markdown("""
    <style>
        [data-testid="stVerticalBlock"] {
            padding-left: 1rem;
            width: 100% !important;
        }
        .stDownloadButton, .stButton>button {
            width: 100% !important;
        }
    </style>
    """, unsafe_allow_html=True)
    st.title("Tools")

    # Tool selection tabs
    graph_tab, notes_tab = st.tabs(["Graph", "Quick Notes"])

    with graph_tab:
        st.session_state['active_tool'] = "graph"
        st.markdown("<div class='tool-section'>", unsafe_allow_html=True)
        st.subheader("Entity Relationship Graph")

        # Display the graph
        st.graphviz_chart(generate_entity_graph(), use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with notes_tab:
        st.markdown("<div class='tool-section'>", unsafe_allow_html=True)
        st.subheader("Quick Notes")

        notes = st.text_area(
            "Type your notes here...",
            value=st.session_state.quick_notes,
            height=200,
            key="notes_textarea",
            label_visibility="collapsed"
        )
        st.session_state.quick_notes = notes

        # Save/download buttons - now full width
        if st.button("Save Notes", key="save_notes", use_container_width=True):
            st.success("Notes saved in session!")

        st.download_button(
            label="Download Notes",
            data=notes.encode('utf-8'),
            file_name="quick_notes.txt",
            mime="text/plain",
            use_container_width=True
        )

        st.markdown("</div>", unsafe_allow_html=True)