import asyncio
import json
import re
from copy import deepcopy
from typing import Optional
from sqlalchemy import select
import streamlit as st
from decouple import config
from ktem.app import BasePage
from ktem.components import reasonings
from ktem.db.models import Conversation, engine
from ktem.index.file.ui import File
from ktem.reasoning.prompt_optimization.mindmap import MINDMAP_HTML_EXPORT_TEMPLATE
from ktem.reasoning.prompt_optimization.suggest_conversation_name import (
    SuggestConvNamePipeline,
)
from ktem.reasoning.prompt_optimization.suggest_followup_chat import (
    SuggestFollowupQuesPipeline,
)
from plotly.io import from_json
from sqlmodel import Session, select
from theflow.settings import settings as flowsettings
from theflow.utils.modules import import_dotted_string

from kotaemon.base import Document
from kotaemon.indices.ingests.files import KH_DEFAULT_FILE_EXTRACTORS
from kotaemon.indices.qa.utils import strip_think_tag

from ...utils import SUPPORTED_LANGUAGE_MAP, get_file_names_regex, get_urls
from ...utils.commands import WEB_SEARCH_COMMAND
from ...utils.hf_papers import get_recommended_papers
from ...utils.rate_limit import check_rate_limit
from .chat_panel import ChatPanel
from .chat_suggestion import ChatSuggestion
from .common import STATE
from .control import ConversationControl
from .demo_hint import HintPage
from .paper_list import PaperListPage
from .report import ReportIssue

KH_DEMO_MODE = getattr(flowsettings, "KH_DEMO_MODE", False)
KH_SSO_ENABLED = getattr(flowsettings, "KH_SSO_ENABLED", False)
KH_WEB_SEARCH_BACKEND = getattr(flowsettings, "KH_WEB_SEARCH_BACKEND", None)
WebSearch = None
if KH_WEB_SEARCH_BACKEND:
    try:
        WebSearch = import_dotted_string(KH_WEB_SEARCH_BACKEND, safe=False)
    except (ImportError, AttributeError) as e:
        print(f"Error importing {KH_WEB_SEARCH_BACKEND}: {e}")

REASONING_LIMITS = 2 if KH_DEMO_MODE else 10
DEFAULT_SETTING = "(default)"
INFO_PANEL_SCALES = {True: 8, False: 4}
DEFAULT_QUESTION = (
    "What is the summary of this document?"
    if not KH_DEMO_MODE
    else "What is the summary of this paper?"
)

chat_input_focus_js = """
function() {
    let chatInput = document.querySelector("#chat-input textarea");
    chatInput.focus();
}
"""

quick_urls_submit_js = """
function() {
    let urlInput = document.querySelector("#quick-url-demo textarea");
    console.log("URL input:", urlInput);
    urlInput.dispatchEvent(new KeyboardEvent('keypress', {'key': 'Enter'}));
}
"""

recommended_papers_js = """
function() {
    // Get all links and attach click event
    var links = document.querySelectorAll("#related-papers a");

    function submitPaper(event) {
        event.preventDefault();
        var target = event.currentTarget;
        var url = target.getAttribute("href");
        console.log("URL:", url);

        let newChatButton = document.querySelector("#new-conv-button");
        newChatButton.click();

        setTimeout(() => {
            let urlInput = document.querySelector("#quick-url-demo textarea");
            // Fill the URL input
            urlInput.value = url;
            urlInput.dispatchEvent(new Event("input", { bubbles: true }));
            urlInput.dispatchEvent(new KeyboardEvent('keypress', {'key': 'Enter'}));
            }, 500
        );
    }

    for (var i = 0; i < links.length; i++) {
        links[i].onclick = submitPaper;
    }
}
"""

clear_bot_message_selection_js = """
function() {
    var bot_messages = document.querySelectorAll(
        "div#main-chat-bot div.message-row.bot-row"
    );
    bot_messages.forEach(message => {
        message.classList.remove("text_selection");
    });
}
"""

pdfview_js = """
function() {
    setTimeout(fullTextSearch(), 100);

    // Get all links and attach click event
    var links = document.getElementsByClassName("pdf-link");
    for (var i = 0; i < links.length; i++) {
        links[i].onclick = openModal;
    }

    // Get all citation links and attach click event
    var links = document.querySelectorAll("a.citation");
    for (var i = 0; i < links.length; i++) {
        links[i].onclick = scrollToCitation;
    }

    var markmap_div = document.querySelector("div.markmap");
    var mindmap_el_script = document.querySelector('div.markmap script');

    if (mindmap_el_script) {
        markmap_div_html = markmap_div.outerHTML;
    }

    // render the mindmap if the script tag is present
    if (mindmap_el_script) {
        markmap.autoLoader.renderAll();
    }

    setTimeout(() => {
        var mindmap_el = document.querySelector('svg.markmap');

        var text_nodes = document.querySelectorAll("svg.markmap div");
        for (var i = 0; i < text_nodes.length; i++) {
            text_nodes[i].onclick = fillChatInput;
        }

        if (mindmap_el) {
            function on_svg_export(event) {
                html = "{html_template}";
                html = html.replace("{markmap_div}", markmap_div_html);
                spawnDocument(html, {window: "width=1000,height=1000"});
            }

            var link = document.getElementById("mindmap-toggle");
            if (link) {
                link.onclick = function(event) {
                    event.preventDefault(); // Prevent the default link behavior
                    var div = document.querySelector("div.markmap");
                    if (div) {
                        var currentHeight = div.style.height;
                        if (currentHeight === '400px' || (currentHeight === '')) {
                            div.style.height = '650px';
                        } else {
                            div.style.height = '400px'
                        }
                    }
                };
            }

            if (markmap_div_html) {
                var link = document.getElementById("mindmap-export");
                if (link) {
                    link.addEventListener('click', on_svg_export);
                }
            }
        }
    }, 250);

    return [links.length]
}
""".replace(
    "{html_template}",
    MINDMAP_HTML_EXPORT_TEMPLATE.replace("\n", "").replace('"', '\\"'),
)

fetch_api_key_js = """
function(_, __) {
    api_key = getStorage('google_api_key', '');
    console.log('session API key:', api_key);
    return [api_key, _];
}
"""
if not KH_DEMO_MODE:
    PLACEHOLDER_TEXT = (
        "This is the beginning of a new conversation.\n"
        "Start by uploading a file or a web URL. "
        "Visit Files tab for more options (e.g: GraphRAG)."
    )
else:
    PLACEHOLDER_TEXT = (
        "Welcome to Kotaemon Demo. "
        "Start by browsing preloaded conversations to get onboard.\n"
        "Check out Hint section for more tips."
    )

class ChatPage(BasePage):
    def __init__(self, app):
        self._app = app
        self._indices_input = []

        # Initialize session state variables if not already set
        if "preview_links" not in st.session_state:
            st.session_state["preview_links"] = None
        if "reasoning_type" not in st.session_state:
            st.session_state["reasoning_type"] = None
        if "conversation_renamed" not in st.session_state:
            st.session_state["conversation_renamed"] = False
        if "use_suggestion" not in st.session_state:
            st.session_state["use_suggestion"] = getattr(flowsettings, "KH_FEATURE_CHAT_SUGGESTION", False)
        if "info_panel_expanded" not in st.session_state:
            st.session_state["info_panel_expanded"] = True
        if "command_state" not in st.session_state:
            st.session_state["command_state"] = None
        if "user_api_key" not in st.session_state:
            st.session_state["user_api_key"] = ""

        self.on_building_ui()

    def on_building_ui(self):
        # Store initial states in session state
        if "state_chat" not in st.session_state:
            st.session_state["state_chat"] = "STATE"
            st.session_state["state_retrieval_history"] = []
            st.session_state["state_plot_history"] = []
            st.session_state["state_plot_panel"] = None
            st.session_state["first_selector_choices"] = None

        col1, col2, col3 = st.columns([1, 4, 2])  # Layout: Sidebar | Chat Area | Info Panel

        # ---- Conversation Settings Panel ----
        with col1:
            st.markdown("### Conversation Settings")
            self.chat_control = ConversationControl(self._app)

            for index_id, index in enumerate(self._app.index_manager.indices):
                index.selector = None
                index_ui = index.get_selector_component_ui()
                if not index_ui:
                    continue

                 # Need to rerender later within Accordion
                is_first_index = index_id == 0
                index_name = index.name if not KH_DEMO_MODE else "Select from Paper Collection"

                with st.expander(index_name, expanded=is_first_index):
                    index_ui.render()
                    

                    if is_first_index:
                        st.session_state["first_selector_choices"] = index_ui.selector_choices

            # ---- Chat Suggestion ----
            self.chat_suggestion = ChatSuggestion(self._app)

            # ---- Quick Upload Section ----
            if len(self._app.index_manager.indices) > 0:
                quick_upload_label = "Quick Upload" if not KH_DEMO_MODE else "Or input new paper URL"
                with st.expander(quick_upload_label):
                    st.markdown("Upload a file or paste URLs")

                    uploaded_files = st.file_uploader("Upload files", accept_multiple_files=True)
                    pasted_url = st.text_input("Paste URL")

            # ---- Report Issue or Related Papers ----
            if not KH_DEMO_MODE:
                st.button("Report an Issue")
            else:
                with st.expander("Related Papers", expanded=False):
                    st.markdown("Related papers content")

            st.markdown("### Suggested Follow-up Questions")
            self.chat_suggestion.show_suggestions()

            
        # ---- Chat Panel ----
        with col2:
            # Initialize chat history in session state
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []

            chat_container = st.container()

            with chat_container:
                for message in st.session_state.chat_history:
                    role, text = message
                    if role == "user":
                        st.markdown(f"**You:** {text}")
                    else:
                        st.markdown(f"**Bot:** {text}")

            # Input box for chat
            chat_input = st.text_input("Type a message...", placeholder=PLACEHOLDER_TEXT)

            # Submit button
            if st.button("Send"):
                if chat_input:
                    pass

            with st.expander("Chat Settings", expanded=False):
                st.markdown("#### Chat Configuration")
                reasoning_method = st.selectbox("Reasoning Method", self._app.default_settings.reasoning.settings["use"].choices)
                model_type = st.selectbox("Model", self._app.default_settings.reasoning.options["simple"].settings["llm"].choices)
                language = st.selectbox("Language", self._app.default_settings.reasoning.settings["lang"].choices)
                citation = st.selectbox("Citation Highlighting", self._app.default_settings.reasoning.options["simple"].settings["highlight_citation"].choices)

                use_mindmap = st.checkbox("Enable Mindmap", value=True)

        # ---- Information Panel ----
        with col3:
            with st.expander("Information Panel", expanded=True):
                st.markdown("### Info & Visualization")
                st.markdown("Placeholder for information panel")
                st.empty()  # Placeholder for plots or additional UI elements.

        # Follow-up Questions Section
        
    def json_to_plot(self,json_dict: dict | None):
        """Converts JSON data to a Plotly chart and displays it in Streamlit."""
        if json_dict:
            plot = from_json(json_dict)  # Convert JSON to a Plotly figure
            st.plotly_chart(plot, use_container_width=True)  # Display in Streamlit
        else:
            st.write("No plot available.")  # Show a placeholder message


    def on_register_events():
        # Session state initialization
        if "conversation" not in st.session_state:
            st.session_state.conversation = []
        if "user_id" not in st.session_state:
            st.session_state.user_id = "demo_user"
        if "conv_id" not in st.session_state:
            st.session_state.conv_id = None
        if "conv_name" not in st.session_state:
            st.session_state.conv_name = None
        if "first_selector_choices" not in st.session_state:
            st.session_state.first_selector_choices = []

        # Sidebar settings
        with st.sidebar:
            st.header("Chat Settings")
            st.session_state.selected_model = st.selectbox("Model", ["GPT-4", "Llama", "Claude"], index=0)
            st.session_state.language = st.selectbox("Language", ["English", "French", "German"], index=0)
            st.session_state.show_mindmap = st.checkbox("Enable Mindmap", value=True)

        st.title("Chatbot Interface")

        # User input
        user_input = st.text_input("Your Message:", key="chat_input")

        if st.button("Send"):
            if user_input:
                # Prepare chat input for submit_msg
                chat_input_dict = {"text": user_input}

                # Simulated settings object
                settings = {
                    "model": st.session_state.selected_model,
                    "language": st.session_state.language,
                }

                # Call the actual chat handler
                result = submit_msg(
                    chat_input=chat_input_dict,
                    chat_history=st.session_state.conversation,
                    user_id=st.session_state.user_id,
                    settings=settings,
                    conv_id=st.session_state.conv_id,
                    conv_name=st.session_state.conv_name,
                    first_selector_choices=st.session_state.first_selector_choices,
                )

                if result:
                    st.session_state.conversation = result["chat_history"]
                    st.session_state.conv_id = result["new_conv_id"]
                    st.session_state.conv_name = result["new_conv_name"]
                    st.session_state.first_selector_choices = list(set(st.session_state.first_selector_choices + [(url, fid) for url, fid in zip(result.get("file_ids", []), result.get("file_ids", []))]))

        # Display chat history
        st.subheader("Chat History")
        for speaker, text in st.session_state.conversation:
            with st.expander(f"{'User' if speaker == text else 'AI'} says:"):
                st.write(speaker)

        if st.session_state.show_mindmap:
            st.subheader("Mindmap View (Coming Soon)")

        if st.button("New Conversation"):
            st.session_state.conversation = []
            st.session_state.conv_id = None
            st.session_state.conv_name = None
            st.session_state.first_selector_choices = []

    import streamlit as st
    from sqlalchemy import select
    import re

    KH_DEMO_MODE = False  # Set this according to your environment
    DEFAULT_QUESTION = "Summarize the document."
    WEB_SEARCH_COMMAND = "@web_search"

    def get_file_names_regex(input_str):
        """Extract file names from input text using regex pattern @"filename"."""
        pattern = r'@"([^"]+)"'
        matches = re.findall(pattern, input_str)
        input_str = re.sub(pattern, "", input_str).strip()  # Remove matches from text
        return matches, input_str

    def get_urls(input_str):
        """Extract URLs from the input text."""
        pattern = r"https?://\S+"
        matches = re.findall(pattern, input_str)
        input_str = re.sub(pattern, "", input_str).strip()
        return matches, input_str

    def submit_msg(
        chat_input,
        chat_history,
        user_id,
        settings,
        conv_id,
        conv_name,
        first_selector_choices
    ):
        """Submit a message to the chatbot (Streamlit version)."""
        
        if not chat_input:
            st.error("Input is empty")
            return None

        chat_input_text = chat_input.get("text", "")
        file_ids = []
        used_command = None

        first_selector_choices_map = {item[0]: item[1] for item in first_selector_choices}

        file_names, chat_input_text = get_file_names_regex(chat_input_text)

        if WEB_SEARCH_COMMAND in file_names:
            used_command = WEB_SEARCH_COMMAND

        urls, chat_input_text = get_urls(chat_input_text)

        if urls:
            st.write(f"Detected URLs: {urls}")
            file_ids = [f"file_id_{i}" for i, _ in enumerate(urls)]  # Simulated indexing
        elif file_names:
            for file_name in file_names:
                file_id = first_selector_choices_map.get(file_name)
                if file_id:
                    file_ids.append(file_id)

        first_selector_choices.extend(zip(urls, file_ids))

        if not chat_input_text and file_ids:
            chat_input_text = DEFAULT_QUESTION

        if not chat_input_text and not chat_history:
            chat_input_text = DEFAULT_QUESTION

        if chat_input_text:
            chat_history.append((chat_input_text, None))
        else:
            if not chat_history:
                st.error("Empty chat")
                return None

        if not conv_id:
            if not KH_DEMO_MODE:
                with Session(engine) as session:
                    new_conv = Conversation(user_id=user_id)
                    session.add(new_conv)
                    session.commit()
                    session.refresh(new_conv)
                    new_conv_id = new_conv.id
                    new_conv_name = new_conv.name
            else:
                new_conv_id, new_conv_name = None, None
        else:
            new_conv_id = conv_id
            new_conv_name = conv_name

        return {
            "chat_history": chat_history,
            "new_conv_id": new_conv_id,
            "new_conv_name": new_conv_name,
            "file_ids": file_ids,
            "used_command": used_command,
        }

    def get_recommendations(first_selector_choices, file_ids):
        """Get paper recommendations based on the first selected file."""

        first_selector_choices_map = {item[1]: item[0] for item in first_selector_choices}

        file_names = [first_selector_choices_map[file_id] for file_id in file_ids if file_id in first_selector_choices_map]

        if not file_names:
            return ""

        first_file_name = file_names[0].split(".")[0].replace("_", " ")

        recommendations = get_recommended_papers(first_file_name)

        return recommendations

    def toggle_delete(conv_id):
        """Toggle delete button visibility based on conversation ID."""
        if "show_delete" not in st.session_state:
            st.session_state["show_delete"] = True  # Default state

        st.session_state["show_delete"] = False if conv_id else True

    def set_public_conversation(is_public, convo_id):
        """Set a conversation as public or private."""
        if not convo_id:
            st.warning("No conversation selected")
            return

        with Session(engine) as session:
            result = session.exec(select(Conversation).where(Conversation.id == convo_id)).one()
            print(result)
            name = result.name

            if result.is_public != is_public:
                result.is_public = is_public
                session.add(result)
                session.commit()
                st.info(f"Conversation: {name} is now {'public' if is_public else 'private'}.")
                
    def persist_data_source(convo_id, user_id, retrieval_msg, plot_data, retrival_history, plot_history, messages, state, *selecteds):
        """Update the data source in the database."""
        
        if not convo_id:
            st.warning("No conversation selected")
            return retrival_history, plot_history  # Return unchanged history

        if not state["app"].get("regen", False):
            retrival_history.append(retrieval_msg)
            plot_history.append(plot_data)
        else:
            if retrival_history:
                retrival_history[-1] = retrieval_msg
                plot_history[-1] = plot_data

        state["app"]["regen"] = False

        selecteds_ = {str(i): selecteds[i] for i in range(len(selecteds))}

        with Session(engine) as session:
            result = session.exec(select(Conversation).where(Conversation.id == convo_id)).one()
            data_source = deepcopy(result.data_source)
            is_owner = result.user == user_id

            result.data_source = {
                "selected": selecteds_ if is_owner else data_source.get("selected", {}),
                "messages": messages,
                "retrieval_messages": retrival_history,
                "plot_history": plot_history,
                "state": state,
                "likes": deepcopy(data_source.get("likes", [])),
            }
            session.add(result)
            session.commit()

        return retrival_history, plot_history

    def reasoning_changed(reasoning_type):
        """Handle changes in reasoning type."""
        if reasoning_type != DEFAULT_SETTING:
            st.info(f"Reasoning type changed to `{reasoning_type}`")
        return reasoning_type

    def check_and_suggest_name_conv(chat_history):
        """Suggest a conversation name based on chat history."""
        suggest_pipeline = SuggestConvNamePipeline()
        new_name = ""
        renamed = False

        if len(chat_history) == 1:
            suggested_name = suggest_pipeline(chat_history).text
            suggested_name = re.sub(r'["\']', "", suggested_name)[:40]
            new_name = suggested_name
            renamed = True

        return new_name, renamed

    def suggest_chat_conv(settings, session_language, chat_history, use_suggestion):
        """Suggest follow-up questions based on chat history."""
        
        target_language = session_language if session_language != DEFAULT_SETTING else settings.get("reasoning.lang", "en")

        if use_suggestion:
            suggest_pipeline = SuggestFollowupQuesPipeline()
            suggest_pipeline.lang = target_language
            suggested_questions = [["Example Question 1"], ["Example Question 2"]]

            if len(chat_history) >= 1:
                suggested_resp = suggest_pipeline(chat_history).text
                match = re.search(r"\[(.*?)\]", re.sub("\n", "", suggested_resp))
                if match:
                    try:
                        suggested_questions = [[q] for q in json.loads(match.group())]
                    except Exception:
                        pass

            return True, suggested_questions

        return False, []

