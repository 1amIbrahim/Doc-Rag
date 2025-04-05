import os
from pathlib import Path
import pluggy
from ktem import extension_protocol
from ktem.assets import KotaemonTheme, PDFJS_PREBUILT_DIR
from ktem.components import reasonings
from ktem.exceptions import HookAlreadyDeclared, HookNotDeclared
from ktem.index import IndexManager
from ktem.settings import BaseSettingGroup, SettingGroup, SettingReasoningGroup
from theflow.settings import settings
from theflow.utils.modules import import_dotted_string
import streamlit as st
BASE_PATH = os.environ.get("GR_FILE_ROOT_PATH", "")

class BaseApp:
    """The main app of Kotaemon using Streamlit"""

    def __init__(self):
        self.dev_mode = getattr(settings, "KH_MODE", "") == "dev"
        self.app_name = getattr(settings, "KH_APP_NAME", "Kotaemon")
        self.app_version = getattr(settings, "KH_APP_VERSION", "")
        self.f_user_management = getattr(settings, "KH_FEATURE_USER_MANAGEMENT", False)
        self._theme = KotaemonTheme()

        dir_assets = Path(__file__).parent / "assets"
        self._favicon = str(dir_assets / "img" / "favicon.svg")

        self.default_settings = SettingGroup(
            application=BaseSettingGroup(settings=settings.SETTINGS_APP),
            reasoning=SettingReasoningGroup(settings=settings.SETTINGS_REASONING),
        )
        
        self._callbacks = {}
        self._events = {}

        self.register_extensions()
        self.register_reasonings()
        self.initialize_indices()

        self.default_settings.reasoning.finalize()
        self.default_settings.index.finalize()

        if "settings_state" not in st.session_state:
            st.session_state.settings_state = self.default_settings.flatten()
        self.setting_state = st.session_state.settings_state
        if "user_id" not in st.session_state:
            st.session_state.user_id = "default" if not self.f_user_management else None
        self.user_id = st.session_state.user_id
        
        
    def initialize_indices(self):
        """Create the index manager, start indices, and register to app settings"""
        self.index_manager = IndexManager(self)
        self.index_manager.on_application_startup()

        for index in self.index_manager.indices:
            options = index.get_user_settings()
            self.default_settings.index.options[index.id] = BaseSettingGroup(
                settings=options
            )

    def register_reasonings(self):
        """Register the reasoning components from app settings"""
        if getattr(settings, "KH_REASONINGS", None) is None:
            return

        for value in settings.KH_REASONINGS:
            reasoning_cls = import_dotted_string(value, safe=False)
            rid = reasoning_cls.get_info()["id"]
            reasonings[rid] = reasoning_cls
            options = reasoning_cls().get_user_settings()
            self.default_settings.reasoning.options[rid] = BaseSettingGroup(
                settings=options
            )

    def register_extensions(self):
        """Register installed extensions"""
        self.exman = pluggy.PluginManager("ktem")
        self.exman.add_hookspecs(extension_protocol)
        self.exman.load_setuptools_entrypoints("ktem")

        extension_declarations = self.exman.hook.ktem_declare_extensions()
        for extension_declaration in extension_declarations:
            functionality = extension_declaration["functionality"]

            if "reasoning" in functionality:
                for rid, rdec in functionality["reasoning"].items():
                    unique_rid = f"{extension_declaration['id']}/{rid}"
                    self.default_settings.reasoning.options[unique_rid] = BaseSettingGroup(
                        settings=rdec["settings"],
                    )

    def declare_event(self, name: str):
        """Declare an event for the app"""
        if name in self._events:
            raise HookAlreadyDeclared(f"Hook {name} is already declared")
        self._events[name] = []

    def subscribe_event(self, name: str, definition: dict):
        """Register a hook for the app"""
        if name not in self._events:
            raise HookNotDeclared(f"Hook {name} is not declared")
        self._events[name].append(definition)

    def get_event(self, name) -> list[dict]:
        if name not in self._events:
            raise HookNotDeclared(f"Hook {name} is not declared")
        return self._events[name]


class BasePage:
    """Base class for pages in the Kotaemon app using Streamlit"""
    
    public_events: list[str] = []

    def __init__(self, app: BaseApp):
        self._app = app

    def render(self):
        """Render the UI components of the page."""
        pass

    def declare_public_events(self):
        """Declare an event for the app."""
        for event in self.public_events:
            self._app.declare_event(event)

    def subscribe_public_events(self):
        """Subscribe to declared public events."""
        pass

    def register_events(self):
        """Register all events."""
        pass

    def on_app_created(self):
        """Execute actions when the app is created."""
        pass
