import os
from pathlib import Path

import streamlit as st
from ktem.assets import PDFJS_PREBUILT_DIR
from ktem.index import IndexManager
from ktem.settings import BaseSettingGroup, SettingGroup, SettingReasoningGroup
from theflow.settings import settings
from theflow.utils.modules import import_dotted_string


class StreamlitBaseApp:
    def __init__(self):
        self.dev_mode = getattr(settings, "KH_MODE", "") == "dev"
        self.app_name = getattr(settings, "KH_APP_NAME", "Kotaemon")
        self.app_version = getattr(settings, "KH_APP_VERSION", "")
        self.f_user_management = getattr(settings, "KH_FEATURE_USER_MANAGEMENT", False)

        self._load_assets()

        self.default_settings = SettingGroup(
            application=BaseSettingGroup(settings=settings.SETTINGS_APP),
            reasoning=SettingReasoningGroup(settings=settings.SETTINGS_REASONING),
        )

        self.register_reasonings()
        self.initialize_indices()

        self.default_settings.reasoning.finalize()
        self.default_settings.index.finalize()
        
        st.session_state.user_id = "default"
        
        st.session_state.settings = self.default_settings.flatten()
        self.setting_state = st.session_state.settings
        self.user_id =st.session_state.user_id 
        print(st.session_state.user_id)
        
    def _load_assets(self):
        dir_assets = Path(__file__).parent / "assets"
        self._favicon = str(dir_assets / "img" / "favicon.svg")

        self._css = (dir_assets / "css" / "main.css").read_text()
        self._js = (dir_assets / "js" / "main.js").read_text().replace("KH_APP_VERSION", self.app_version)

        pdf_js_dist_dir = str(PDFJS_PREBUILT_DIR).replace("\\", "\\\\")
        self._pdf_view_js = (dir_assets / "js" / "pdf_viewer.js").read_text(encoding="utf-8")
        self._pdf_view_js = self._pdf_view_js.replace("PDFJS_PREBUILT_DIR", pdf_js_dist_dir).replace("GR_FILE_ROOT_PATH", os.environ.get("GR_FILE_ROOT_PATH", ""))

        self._svg_js = (dir_assets / "js" / "svg-pan-zoom.min.js").read_text()

    def initialize_indices(self):
        self.index_manager = IndexManager(self)
        self.index_manager.on_application_startup()

        for index in self.index_manager.indices:
            options = index.get_user_settings()
            self.default_settings.index.options[index.id] = BaseSettingGroup(settings=options)

    def register_reasonings(self):
        if getattr(settings, "KH_REASONINGS", None) is None:
            return

        from ktem.components import reasonings
        for value in settings.KH_REASONINGS:
            reasoning_cls = import_dotted_string(value, safe=False)
            rid = reasoning_cls.get_info()["id"]
            reasonings[rid] = reasoning_cls
            options = reasoning_cls().get_user_settings()
            self.default_settings.reasoning.options[rid] = BaseSettingGroup(settings=options)

    def inject_assets(self):
        st.markdown(f"<style>{self._css}</style>", unsafe_allow_html=True)
        st.markdown(f"<script>{self._js}</script>", unsafe_allow_html=True)
        st.markdown(f"<script>{self._pdf_view_js}</script>", unsafe_allow_html=True)
        st.markdown(f"<script>{self._svg_js}</script>", unsafe_allow_html=True)

    def ui(self):
        raise NotImplementedError("Subclasses should implement the UI.")

    def run(self):
        st.set_page_config(page_title=self.app_name, page_icon=self._favicon,layout='wide')
        self.inject_assets()
        self.ui()

import streamlit as st
from typing import Optional, List, Union
from abc import ABC, abstractmethod

class BasePage(ABC):
    """The logic of the Streamlit app (adapted from Kotaemon)"""
    
    public_events: List[str] = []
    
    def __init__(self, app):
        self._app = app
        self._initialized = False
    
    @abstractmethod
    def on_building_ui(self):
        """Build the UI of the app"""
        pass
    
    @abstractmethod
    def on_subscribe_public_events(self):
        """Subscribe to the declared public event of the app"""
        pass
    
    @abstractmethod
    def on_register_events(self):
        """Register all events to the app"""
        pass
    
    def _on_app_created(self):
        """Called when the app is created"""
        pass
    
    def as_streamlit_component(self) -> Optional[Union[st.delta_generator.DeltaGenerator, 
                                                    List[st.delta_generator.DeltaGenerator]]]:
        """Return the Streamlit components responsible for events"""
        return None
    
    def render(self):
        """Render all components in the page"""
        if not self._initialized:
            self.on_building_ui()
            self._initialized = True
            
        # In Streamlit, rendering happens automatically when components are created
        # This method serves as a placeholder for the original functionality
        for value in self.__dict__.values():
            if isinstance(value, BasePage):
                value.render()
    
    def unrender(self):
        """Streamlit doesn't have an exact equivalent of unrender"""
        # In Streamlit, we can clear components by controlling what gets rendered
        # This would be handled by conditional rendering in the main app
        for value in self.__dict__.values():
            if isinstance(value, BasePage):
                value.unrender()
    
    def declare_public_events(self):
        """Declare an event for the app"""
        for event in self.public_events:
            self._app.declare_event(event)

        for value in self.__dict__.values():
            if isinstance(value, BasePage):
                value.declare_public_events()
    
    def subscribe_public_events(self):
        """Subscribe to an event"""
        self.on_subscribe_public_events()
        for value in self.__dict__.values():
            if isinstance(value, BasePage):
                value.subscribe_public_events()
    
    def register_events(self):
        """Register all events"""
        self.on_register_events()
        for value in self.__dict__.values():
            if isinstance(value, BasePage):
                value.register_events()
    
    def on_app_created(self):
        """Execute on app created callbacks"""
        self._on_app_created()
        for value in self.__dict__.values():
            if isinstance(value, BasePage):
                value.on_app_created()