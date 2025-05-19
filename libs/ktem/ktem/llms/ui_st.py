import streamlit as st
import pandas as pd
import yaml
import copy

from ktem.utils.file import YAMLNoDateSafeLoader
from theflow.utils.modules import deserialize
from .manager import llms

def format_description(cls):
    params = cls.describe()["params"]
    params_lines = ["| Name | Type | Description |", "| --- | --- | --- |"]
    for key, value in params.items():
        if isinstance(value["auto_callback"], str):
            continue
        params_lines.append(f"| {key} | {value['type']} | {value['help']} |")
    return f"{cls.__doc__}\n\n" + "\n".join(params_lines)

class LLMManagement:
    def __init__(self):
        self.spec_desc_default = (
            "# Spec description\n\nSelect an LLM to view the spec description."
        )
        self.initialize_session_state()
        self.render()

    def initialize_session_state(self):
        if 'selected_llm_name' not in st.session_state:
            st.session_state.selected_llm_name = ""
        if 'show_delete_confirm' not in st.session_state:
            st.session_state.show_delete_confirm = False
        if 'connection_logs' not in st.session_state:
            st.session_state.connection_logs = ""

    def render(self):
        
        tab1, tab2 = st.tabs(["View", "Add"])
        
        with tab1:
            self.render_view_tab()
        
        with tab2:
            self.render_add_tab()

    def render_view_tab(self):
        llm_list = self.list_llms()
        
        if not llm_list.empty:
            st.dataframe(
                llm_list,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "name": "Name",
                    "vendor": "Vendor",
                    "default": "Default"
                }
            )
            
            # Get selected row
            selected_indices = st.session_state.get('llm_table_selected_indices', [])
            if selected_indices:
                selected_llm_name = llm_list.iloc[selected_indices[0]]['name']
                if selected_llm_name != st.session_state.selected_llm_name:
                    st.session_state.selected_llm_name = selected_llm_name
                    st.session_state.show_delete_confirm = False
                    st.rerun()
        else:
            st.info("No LLMs available. Please add an LLM first.")
        
        if st.session_state.selected_llm_name:
            self.render_selected_llm_panel()

    def render_selected_llm_panel(self):
        info = copy.deepcopy(llms.info()[st.session_state.selected_llm_name])
        vendor_str = info["spec"].pop("__type__", "-").split(".")[-1]
        vendor = llms.vendors()[vendor_str]
        
        with st.expander(f"Editing: {st.session_state.selected_llm_name}", expanded=True):
            col1, col2 = st.columns([2, 3])
            
            with col1:
                edit_default = st.checkbox(
                    "Set default",
                    value=info["default"],
                    help="Set this LLM as default. If no default is set, a random LLM will be used."
                )
                
                edit_spec = st.text_area(
                    "Specification",
                    value=yaml.dump(info["spec"]),
                    height=300,
                    help="Specification of the LLM in YAML format"
                )
                
                with st.expander("Test connection", expanded=False):
                    st.markdown(st.session_state.connection_logs, unsafe_allow_html=True)
                    if st.button("Test Connection"):
                        self.check_connection(st.session_state.selected_llm_name, edit_spec)
                
                col1a, col1b, col1c = st.columns([1, 1, 1])
                with col1a:
                    if st.button("Save", type="primary"):
                        self.save_llm(st.session_state.selected_llm_name, edit_default, edit_spec)
                        st.rerun()
                with col1b:
                    if not st.session_state.show_delete_confirm:
                        if st.button("Delete", type="secondary"):
                            st.session_state.show_delete_confirm = True
                            st.rerun()
                    else:
                        if st.button("Confirm Delete", type="primary"):
                            self.delete_llm(st.session_state.selected_llm_name)
                            st.session_state.selected_llm_name = ""
                            st.session_state.show_delete_confirm = False
                            st.rerun()
                        if st.button("Cancel", type="secondary"):
                            st.session_state.show_delete_confirm = False
                            st.rerun()
                with col1c:
                    if st.button("Close"):
                        st.session_state.selected_llm_name = ""
                        st.rerun()
            
            with col2:
                st.markdown(format_description(vendor))

    def render_add_tab(self):
        col1, col2 = st.columns([2, 3])
        
        with col1:
            name = st.text_input(
                "LLM name",
                help="Must be unique. The name will be used to identify the LLM."
            )
            
            vendor_choices = list(llms.vendors().keys())
            llm_choice = st.selectbox(
                "LLM vendors",
                options=vendor_choices,
                help="Choose the vendor for the LLM. Each vendor has different specification."
            )
            
            vendor = llms.vendors()[llm_choice]
            required_params = {}
            desc = vendor.describe()
            for key, value in desc["params"].items():
                if value.get("required", False):
                    required_params[key] = None
            
            spec = st.text_area(
                "Specification",
                value=yaml.dump(required_params),
                height=300,
                help="Specification of the LLM in YAML format"
            )
            
            default = st.checkbox(
                "Set default",
                help="Set this LLM as default. This default LLM will be used by default across the application."
            )
            
            if st.button("Add LLM", type="primary"):
                self.create_llm(name, llm_choice, spec, default)
                st.rerun()
        
        with col2:
            if llm_choice:
                st.markdown(format_description(vendor))
            else:
                st.markdown(self.spec_desc_default)

    def create_llm(self, name, choices, spec, default):
        try:
            spec = yaml.load(spec, Loader=YAMLNoDateSafeLoader)
            spec["__type__"] = (
                llms.vendors()[choices].__module__
                + "."
                + llms.vendors()[choices].__qualname__
            )

            llms.add(name, spec=spec, default=default)
            st.success(f"LLM {name} created successfully")
        except Exception as e:
            st.error(f"Failed to create LLM {name}: {e}")

    def list_llms(self):
        items = []
        for item in llms.info().values():
            record = {}
            record["name"] = item["name"]
            record["vendor"] = item["spec"].get("__type__", "-").split(".")[-1]
            record["default"] = item["default"]
            items.append(record)

        if items:
            return pd.DataFrame.from_records(items)
        else:
            return pd.DataFrame(columns=["name", "vendor", "default"])

    def check_connection(self, selected_llm_name, selected_spec):
        log_content = ""

        try:
            log_content += f"- Testing model: {selected_llm_name}<br>"
            st.session_state.connection_logs = log_content
            st.rerun()

            # Parse content & init model
            info = copy.deepcopy(llms.info()[selected_llm_name])

            # Parse content & create dummy embedding
            spec = yaml.load(selected_spec, Loader=YAMLNoDateSafeLoader)
            info["spec"].update(spec)

            llm = deserialize(info["spec"], safe=False)

            if llm is None:
                raise Exception(f"Can not found model: {selected_llm_name}")

            log_content += "- Sending a message `Hi`<br>"
            st.session_state.connection_logs = log_content
            st.rerun()
            
            respond = llm("Hi")

            log_content += (
                f"<mark style='background: green; color: white'>- Connection success. "
                f"Got response:\n {respond}</mark><br>"
            )
            st.session_state.connection_logs = log_content
            st.rerun()

            st.success(f"LLM {selected_llm_name} connect successfully")
        except Exception as e:
            log_content += (
                f"<mark style='color: yellow; background: red'>- Connection failed. "
                f"Got error:\n {e}</mark>"
            )
            st.session_state.connection_logs = log_content
            st.rerun()

    def save_llm(self, selected_llm_name, default, spec):
        try:
            spec = yaml.load(spec, Loader=YAMLNoDateSafeLoader)
            spec["__type__"] = llms.info()[selected_llm_name]["spec"]["__type__"]
            llms.update(selected_llm_name, spec=spec, default=default)
            st.success(f"LLM {selected_llm_name} saved successfully")
        except Exception as e:
            st.error(f"Failed to save LLM {selected_llm_name}: {e}")

    def delete_llm(self, selected_llm_name):
        try:
            llms.delete(selected_llm_name)
            st.success(f"LLM {selected_llm_name} deleted successfully")
        except Exception as e:
            st.error(f"Failed to delete LLM {selected_llm_name}: {e}")