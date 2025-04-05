import streamlit as st
import requests
import json
from decouple import config
from ktem.embeddings.manager import embedding_models_manager as embeddings
from ktem.llms.manager import llms
from ktem.rerankings.manager import reranking_models_manager as rerankers
from theflow.settings import settings as flowsettings

KH_OLLAMA_URL = getattr(flowsettings, "KH_OLLAMA_URL", "http://localhost:11434/v1/")
DEFAULT_OLLAMA_URL = KH_OLLAMA_URL.replace("v1", "api").rstrip("/")


def pull_model(name: str):
    payload = {"name": name}
    headers = {"Content-Type": "application/json"}
    response = requests.post(DEFAULT_OLLAMA_URL + "/pull", json=payload, headers=headers, stream=True)
    response.raise_for_status()

    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode("utf-8"))
            yield data
            if data.get("status") == "success":
                break


class SetupPage:
    def __init__(self, app=None):
        self._app = app
        self.settings_state = {} if app is None else app.settings_state

    def render(self):
        st.title("Welcome to Doc-RAG First Setup")

        provider_options = {
            "cohere": "Cohere API (*free registration*) - recommended",
            "google": "Google API (*free registration*)",
            "openai": "OpenAI API (for GPT-based models)",
            "ollama": "Local LLM (for completely *private RAG*)",
        }

        model_key = st.radio(
            "Select your model provider",
            list(provider_options.values()),
            index=0
        )

        selected_model = [k for k, v in provider_options.items() if v == model_key][0]

        api_keys = {}

        if selected_model == "cohere":
            api_keys["cohere_api_key"] = st.text_input("Cohere API Key", type="password")
        elif selected_model == "google":
            api_keys["google_api_key"] = st.text_input("Google API Key", type="password")
        elif selected_model == "openai":
            api_keys["openai_api_key"] = st.text_input("OpenAI API Key", type="password")
        elif selected_model == "ollama":
            api_keys["ollama_model_name"] = st.text_input("LLM model name", value=config("LOCAL_MODEL", default="qwen2.5:7b"))
            api_keys["ollama_emb_model_name"] = st.text_input("Embedding model name", value=config("LOCAL_MODEL_EMBEDDINGS", default="nomic-embed-text"))

        if st.button("Proceed"):
            with st.status("Setting up models...", expanded=True) as status:
                try:
                    self.update_model(selected_model, **api_keys)
                    self.update_default_settings(selected_model)
                    status.update(label="Setup completed successfully!", state="complete")
                except Exception as e:
                    st.error(f"Setup failed: {e}")
                    status.update(label="Setup failed", state="error")

    def update_model(self, selected_model, **kwargs):
        if selected_model == "cohere":
            key = kwargs.get("cohere_api_key")
            if key:
                llms.update("cohere", {
                    "__type__": "kotaemon.llms.chats.LCCohereChat",
                    "model_name": "command-r-plus-08-2024",
                    "api_key": key,
                }, default=True)
                embeddings.update("cohere", {
                    "__type__": "kotaemon.embeddings.LCCohereEmbeddings",
                    "model": "embed-multilingual-v3.0",
                    "cohere_api_key": key,
                    "user_agent": "default",
                }, default=True)
                rerankers.update("cohere", {
                    "__type__": "kotaemon.rerankings.CohereReranking",
                    "model_name": "rerank-multilingual-v2.0",
                    "cohere_api_key": key,
                }, default=True)

        elif selected_model == "google":
            key = kwargs.get("google_api_key")
            if key:
                llms.update("google", {
                    "__type__": "kotaemon.llms.chats.LCGeminiChat",
                    "model_name": "gemini-1.5-flash",
                    "api_key": key,
                }, default=True)
                embeddings.update("google", {
                    "__type__": "kotaemon.embeddings.LCGoogleEmbeddings",
                    "model": "models/text-embedding-004",
                    "google_api_key": key,
                }, default=True)

        elif selected_model == "openai":
            key = kwargs.get("openai_api_key")
            if key:
                llms.update("openai", {
                    "__type__": "kotaemon.llms.ChatOpenAI",
                    "base_url": "https://api.openai.com/v1",
                    "model": "gpt-4o",
                    "api_key": key,
                    "timeout": 20,
                }, default=True)
                embeddings.update("openai", {
                    "__type__": "kotaemon.embeddings.OpenAIEmbeddings",
                    "base_url": "https://api.openai.com/v1",
                    "model": "text-embedding-3-large",
                    "api_key": key,
                    "timeout": 10,
                    "context_length": 8191,
                }, default=True)

        elif selected_model == "ollama":
            llm_model_name = kwargs.get("ollama_model_name")
            emb_model_name = kwargs.get("ollama_emb_model_name")

            llms.update("ollama", {
                "__type__": "kotaemon.llms.ChatOpenAI",
                "base_url": KH_OLLAMA_URL,
                "model": llm_model_name,
                "api_key": "ollama",
            }, default=True)
            embeddings.update("ollama", {
                "__type__": "kotaemon.embeddings.OpenAIEmbeddings",
                "base_url": KH_OLLAMA_URL,
                "model": emb_model_name,
                "api_key": "ollama",
            }, default=True)

            for model in [emb_model_name, llm_model_name]:
                st.write(f"Downloading model `{model}` from Ollama...")
                for resp in pull_model(model):
                    st.write(resp.get("status", "Waiting..."))

        # Validate models
        st.write(f"Testing LLM model: {selected_model}")
        try:
            llm = llms.get(selected_model)
            _ = llm("Hi")
            st.success("LLM model connected successfully.")
        except Exception as e:
            raise Exception(f"LLM connection failed: {e}")

        st.write(f"Testing Embedding model: {selected_model}")
        try:
            emb = embeddings.get(selected_model)
            _ = emb("Hi")
            st.success("Embedding model connected successfully.")
        except Exception as e:
            raise Exception(f"Embedding connection failed: {e}")

    def update_default_settings(self, selected_model):
        if self.settings_state is None:
            return

        self.settings_state["index.options.1.reranking_llm"] = selected_model
        if selected_model == "ollama":
            self.settings_state["index.options.1.use_llm_reranking"] = False

