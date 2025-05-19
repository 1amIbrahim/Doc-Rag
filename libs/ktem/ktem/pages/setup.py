import json
import os
import time
import requests
from decouple import config
import streamlit as st
from theflow.settings import settings as flowsettings

KH_OLLAMA_URL = getattr(flowsettings, "KH_OLLAMA_URL", "http://localhost:11434/v1/")
DEFAULT_OLLAMA_URL = KH_OLLAMA_URL.replace("v1", "api").rstrip("/")

class SetupPage:
    def __init__(self, app_name: str):
        self.app_name = app_name
        self.log_content = ""

        self.radio_model_value = st.session_state.get("radio_model_value", "cohere")
        self.cohere_api_key = st.session_state.get("cohere_api_key", "")
        self.openai_api_key = st.session_state.get("openai_api_key", "")
        self.google_api_key = st.session_state.get("google_api_key", "")
        self.ollama_model_name = st.session_state.get("ollama_model_name", config("LOCAL_MODEL", default="qwen2.5:7b"))
        self.ollama_emb_model_name = st.session_state.get("ollama_emb_model_name", config("LOCAL_MODEL_EMBEDDINGS", default="nomic-embed-text"))

        self.log_placeholder = None
        self.status_text = None
        self.progress_bar = None

    def pull_model(self, name: str, stream: bool = True):
        payload = {"name": name}
        headers = {"Content-Type": "application/json"}
        response = requests.post(DEFAULT_OLLAMA_URL + "/pull", json=payload, headers=headers, stream=stream)
        response.raise_for_status()
        if stream:
            for line in response.iter_lines():
                if line:
                    data = json.loads(line.decode("utf-8"))
                    yield data
                    if data.get("status") == "success":
                        break
        else:
            return response.json()

    def setup_ui(self):
        st.title(f"Welcome to {self.app_name} first setup!")

        # Ensure session state variables
        st.session_state.setdefault("radio_model_value", "cohere")
        st.session_state.setdefault("setup_log", "")
        st.session_state.setdefault("setup_complete", False)

        # Provider selection
        st.session_state.radio_model_value = st.radio(
            "Select your model provider",
            options=["cohere", "openai", "ollama", "google"],
            index=0,
            format_func=lambda x: {
                "cohere": "Cohere API (*free registration*) - recommended",
                "openai": "OpenAI API (for GPT-based models)",
                "ollama": "Local LLM (for completely *private RAG*)",
                "google": "Google API (*free registration*)"
            }[x],
            help="Note: You can change this later. If you are not sure, go with the first option."
        )

        provider = st.session_state.radio_model_value

        # Dynamic input fields
        if provider == "cohere":
            st.markdown("#### Cohere API Key\n(register at https://dashboard.cohere.com/api-keys)")
            st.text_input("Cohere API Key", key="cohere_api_key", label_visibility="collapsed")

        elif provider == "openai":
            st.markdown("#### OpenAI API Key\n(create at https://platform.openai.com/api-keys)")
            st.text_input("OpenAI API Key", key="openai_api_key", label_visibility="collapsed")

        elif provider == "google":
            st.markdown("#### Google API Key\n(register at https://aistudio.google.com/app/apikey)")
            st.text_input("Google API Key", key="google_api_key", label_visibility="collapsed")

        elif provider == "ollama":
            st.markdown("#### Setup Ollama\nDownload from https://ollama.com/.")
            st.text_input("LLM model name", key="ollama_model_name", value=self.ollama_model_name)
            st.text_input("Embedding model name", key="ollama_emb_model_name", value=self.ollama_emb_model_name)

        self.log_placeholder = st.empty()
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Proceed", type="primary"):
                st.session_state.setup_complete = False
                self.run_setup()

        with col2:
            if st.button("I am an advanced user. Skip this.", type="secondary"):
                st.session_state.setup_complete = True
                st.rerun()

        if st.session_state.setup_log:
            self.log_placeholder.markdown(st.session_state.setup_log, unsafe_allow_html=True)

        return st.session_state.setup_complete

    def run_setup(self):
        provider = st.session_state.radio_model_value
        self.status_text = st.empty()
        self.progress_bar = st.progress(0)

        if provider == "cohere" and st.session_state.cohere_api_key:
            self.log("Setting up Cohere models...", steps=3)

        elif provider == "openai" and st.session_state.openai_api_key:
            self.log("Setting up OpenAI models...", steps=2)

        elif provider == "google" and st.session_state.google_api_key:
            self.log("Setting up Google models...", steps=2)

        elif provider == "ollama":
            self.log("Setting up Ollama models...")
            for i, name in enumerate([st.session_state.ollama_emb_model_name, st.session_state.ollama_model_name], 1):
                self.log(f"Downloading model `{name}` from Ollama...")
                for p in range(0, 101, 10):
                    time.sleep(0.1)
                    self.progress_bar.progress(p)
                    if p % 30 == 0:
                        self.log(f"Download progress: {p}%")

        self.progress_bar.progress(100)
        self.log("<mark style='background: green; color: white'>- Setup completed successfully!</mark>")
        st.session_state.setup_complete = True
        st.rerun()

    def log(self, message, steps=None):
        self.log_content += f"- {message}<br>"
        st.session_state.setup_log = self.log_content
        if self.status_text:
            self.status_text.markdown(self.log_content, unsafe_allow_html=True)
        if steps:
            for i in range(1, steps + 1):
                time.sleep(0.5)
                self.progress_bar.progress(int((i / steps) * 100))
                self.log(f"Completed step {i}/{steps}")

def update_default_settings(radio_model_value, default_settings):
    default_settings["index.options.1.reranking_llm"] = radio_model_value
    if radio_model_value == "ollama":
        default_settings["index.options.1.use_llm_reranking"] = False
    return default_settings

# Usage
if __name__ == "__main__":
    st.set_page_config(page_title="First Setup", layout="wide")
    page = SetupPage("My App")
    if page.setup_ui():
        st.success("Setup completed successfully!")
        st.balloons()
