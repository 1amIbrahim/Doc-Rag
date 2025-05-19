import sys
import os

import warnings

# Suppress non-critical warnings
warnings.filterwarnings("ignore", message="Could not download mistral tokenizer")
warnings.filterwarnings("ignore", message="GraphRAG dependencies not installed")
warnings.filterwarnings("ignore", message="Nano-GraphRAG dependencies not installed")

# Add libs and current directory to Python path
=======
os.environ["LLAMA_INDEX_CACHE_DIR"] = "/tmp/llama_index_cache"
os.environ["NLTK_DATA"] = "/tmp/nltk_data"
# Add libs to Python path

sys.path.insert(0, os.path.abspath("libs"))
sys.path.insert(0, os.path.abspath("."))

import streamlit as st
from theflow.settings import settings as flowsettings
from libs.ktem.ktem.streamlit_main import App

try:
    import graphrag
    import nano_graphrag
except ImportError:
    pass  # Silently ignore if these are optional

# ENV SETUP
KH_APP_DATA_DIR = getattr(flowsettings, "KH_APP_DATA_DIR", ".")
KH_GRADIO_SHARE = getattr(flowsettings, "KH_GRADIO_SHARE", False)

GRADIO_TEMP_DIR = os.getenv("GRADIO_TEMP_DIR")
if GRADIO_TEMP_DIR is None:
    GRADIO_TEMP_DIR = os.path.join(KH_APP_DATA_DIR, "gradio_tmp")
    os.environ["GRADIO_TEMP_DIR"] = GRADIO_TEMP_DIR

# Initialize app without any Streamlit commands first
app = App()

app.run()

