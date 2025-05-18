import sys
import os
os.environ["LLAMA_INDEX_CACHE_DIR"] = "/tmp/llama_index_cache"
os.environ["NLTK_DATA"] = "/tmp/nltk_data"
# Add libs to Python path
sys.path.insert(0, os.path.abspath("libs"))
import streamlit as st
from theflow.settings import settings as flowsettings
from ktem.streamlit_main import App

# ENV SETUP
KH_APP_DATA_DIR = getattr(flowsettings, "KH_APP_DATA_DIR", ".")
KH_GRADIO_SHARE = getattr(flowsettings, "KH_GRADIO_SHARE", False)

GRADIO_TEMP_DIR = os.getenv("GRADIO_TEMP_DIR")
if GRADIO_TEMP_DIR is None:
    GRADIO_TEMP_DIR = os.path.join(KH_APP_DATA_DIR, "gradio_tmp")
    os.environ["GRADIO_TEMP_DIR"] = GRADIO_TEMP_DIR

# INIT APP
app = App()
app.run()

