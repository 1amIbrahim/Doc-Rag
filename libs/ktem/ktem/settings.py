from typing import Any

from pydantic import BaseModel, Field


class SettingItem(BaseModel):
    """Represent a setting item

    Args:
        name: the name of the setting item
        value: the default value of the setting item
        choices: the list of choices of the setting item, if any
        metadata: the metadata of the setting item
        component: the expected UI component to render the setting
    """

    name: str
    value: Any
    choices: list = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    component: str = "text"
    special_type: str = ""


class BaseSettingGroup(BaseModel):
    settings: dict[str, "SettingItem"] = Field(default_factory=dict)
    options: dict[str, "BaseSettingGroup"] = Field(default_factory=dict)

    def _get_options(self) -> dict:
        return {}

    def finalize(self):
        """Finalize the setting group"""

    def flatten(self) -> dict:
        """Render the setting group into value"""
        output = {}
        for key, value in self.settings.items():
            output[key] = value.value

        output.update({f"options.{k}": v for k, v in self._get_options().items()})

        return output

    def get_setting_item(self, path: str) -> SettingItem:
        """Get the item based on dot notation"""
        path = path.strip(".")
        if "." not in path:
            return self.settings[path]

        key, sub_path = path.split(".", 1)
        if key != "options":
            raise ValueError(f"Invalid key {path}. Should starts with `options.*`")

        option_id, sub_path = sub_path.split(".", 1)
        option = self.options[option_id]
        return option.get_setting_item(sub_path)

    def __bool__(self):
        return bool(self.settings) or bool(self.options)


class SettingReasoningGroup(BaseSettingGroup):
    def _get_options(self) -> dict:
        output = {}
        for ex_name, ex_setting in self.options.items():
            for key, value in ex_setting.flatten().items():
                output[f"{ex_name}.{key}"] = value

        return output

    def finalize(self):
        """Finalize the setting"""
        options = list(self.options.keys())
        if options:
            self.settings["use"].choices = [(x, x) for x in options]
            self.settings["use"].value = options[0]


class SettingIndexOption(BaseSettingGroup):
    """Temporarily keep it here to see if we need this setting template
    for the index component
    """

    indexing: BaseSettingGroup
    retrieval: BaseSettingGroup

    def flatten(self) -> dict:
        """Render the setting group into value"""
        output = {}
        for key, value in self.indexing.flatten():
            output[f"indexing.{key}"] = value

        for key, value in self.retrieval.flatten():
            output[f"retrieval.{key}"] = value

        return output

    def get_setting_item(self, path: str) -> SettingItem:
        """Get the item based on dot notation"""
        path = path.strip(".")

        key, sub_path = path.split(".", 1)
        if key not in ["indexing", "retrieval"]:
            raise ValueError(
                f"Invalid key {path}. Should starts with `indexing.*` or `retrieval.*`"
            )

        value = getattr(self, key)
        return value.get_setting_item(sub_path)


class SettingIndexGroup(BaseSettingGroup):
    def _get_options(self) -> dict:
        output = {}
        for name, setting in self.options.items():
            for key, value in setting.flatten().items():
                output[f"{name}.{key}"] = value

        return output


class SettingGroup(BaseModel):
    application: BaseSettingGroup = Field(default_factory=BaseSettingGroup)
    index: SettingIndexGroup = Field(default_factory=SettingIndexGroup)
    reasoning: SettingReasoningGroup = Field(default_factory=SettingReasoningGroup)

    import streamlit as st

def render_setting_item(setting_item, value):
    """
    Renders a single setting item based on its type and value.
    
    Args:
        setting_item: The setting item object containing its metadata.
        value: The current value for the setting.
    
    Returns:
        The Streamlit widget used to render the setting item.
    """
    component_type = setting_item.component

    # Rendering based on the component type
    if component_type == "text":
        return st.text_input(setting_item.name, value=value, key=setting_item.name)
    
    elif component_type == "number":
        return st.number_input(setting_item.name, value=value, key=setting_item.name)
    
    elif component_type == "boolean":
        return st.checkbox(setting_item.name, value=value, key=setting_item.name)
    
    elif component_type == "select":
        return st.selectbox(setting_item.name, options=setting_item.choices, index=setting_item.choices.index(value) if value in setting_item.choices else 0, key=setting_item.name)
    
    elif component_type == "multiselect":
        return st.multiselect(setting_item.name, options=setting_item.choices, default=value, key=setting_item.name)
    
    elif component_type == "slider":
        return st.slider(setting_item.name, min_value=setting_item.metadata.get("min", 0), max_value=setting_item.metadata.get("max", 100), value=value, key=setting_item.name)
    
    elif component_type == "password":
        return st.text_input(setting_item.name, value=value, type="password", key=setting_item.name)

    else:
        st.warning(f"Unsupported component type: {component_type}")
        return None

    
    def flatten(self) -> dict:
        """Render the setting group into value"""
        output = {}
        for key, value in self.application.flatten().items():
            output[f"application.{key}"] = value

        for key, value in self.index.flatten().items():
            output[f"index.{key}"] = value

        for key, value in self.reasoning.flatten().items():
            output[f"reasoning.{key}"] = value

        return output

    def get_setting_item(self, path: str) -> SettingItem:
        """Get the item based on dot notation"""
        path = path.strip(".")

        key, sub_path = path.split(".", 1)
        if key not in ["application", "index", "reasoning"]:
            raise ValueError(
                f"Invalid key {path}. Should starts with `indexing.*` or `retrieval.*`"
            )

        value = getattr(self, key)
        return value.get_setting_item(sub_path)
