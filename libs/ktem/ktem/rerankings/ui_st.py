import streamlit as st
import pandas as pd
import yaml
import copy

from ktem.utils.file import YAMLNoDateSafeLoader
from theflow.utils.modules import deserialize
from libs.kotaemon.kotaemon.base import BaseComponent
from .manager import reranking_models_manager

def format_description(cls):
    params = cls.describe()["params"]
    params_lines = ["| Name | Type | Description |", "| --- | --- | --- |"]
    for key, value in params.items():
        if isinstance(value["auto_callback"], str):
            continue
        params_lines.append(f"| {key} | {value['type']} | {value['help']} |")
    return f"{cls.__doc__}\n\n" + "\n".join(params_lines)

class RerankingManagement:
    def __init__(self):
        self.spec_desc_default = (
            "# Spec description\n\nSelect a model to view the spec description."
        )
        self.initialize_session_state()
        self.render()

    def initialize_session_state(self):
        if 'selected_rerank_name' not in st.session_state:
            st.session_state.selected_rerank_name = ""
        if 'show_delete_confirm' not in st.session_state:
            st.session_state.show_delete_confirm = False
        if 'connection_logs' not in st.session_state:
            st.session_state.connection_logs = ""

    def render(self):
        st.title("Reranking Management")
        
        tab1, tab2 = st.tabs(["View", "Add"])
        
        with tab1:
            self.render_view_tab()
        
        with tab2:
            self.render_add_tab()

    def render_view_tab(self):
        rerank_list = self.list_rerankings()
        
        if not rerank_list.empty:
            # Use data editor with selection capability
            edited_df = st.data_editor(
                rerank_list,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "name": "Name",
                    "vendor": "Vendor",
                    "default": "Default"
                },
                key="rerank_editor",
                num_rows="fixed"
            )
            
            if "rerank_editor" in st.session_state:
                selected_rows = st.session_state.rerank_editor.get("selected_rows", [])
                if selected_rows:
                    selected_rerank_name = rerank_list.iloc[selected_rows[0]]['name']
                    if selected_rerank_name != st.session_state.selected_rerank_name:
                        st.session_state.selected_rerank_name = selected_rerank_name
                        st.session_state.show_delete_confirm = False
                        st.rerun()
        else:
            st.info("No reranking models available. Please add one first.")
        
        if st.session_state.selected_rerank_name:
            self.render_selected_rerank_panel()
            
    def render_selected_rerank_panel(self):
        info = copy.deepcopy(reranking_models_manager.info()[st.session_state.selected_rerank_name])
        vendor_str = info["spec"].pop("__type__", "-").split(".")[-1]
        vendor = reranking_models_manager.vendors()[vendor_str]
        
        with st.expander(f"Editing: {st.session_state.selected_rerank_name}", expanded=True):
            col1, col2 = st.columns([2, 3])
            
            with col1:
                edit_default = st.checkbox(
                    "Set default",
                    value=info["default"],
                    help="Set this Reranking model as default. This default Reranking will be used by other components by default if no Reranking is specified."
                )
                
                edit_spec = st.text_area(
                    "Specification",
                    value=yaml.dump(info["spec"]),
                    height=300,
                    help="Specification of the Reranking model in YAML format"
                )
                
                with st.expander("Test connection", expanded=False):
                    st.markdown(st.session_state.connection_logs, unsafe_allow_html=True)
                    if st.button("Test Connection"):
                        self.check_connection(st.session_state.selected_rerank_name, edit_spec)
                
                col1a, col1b, col1c = st.columns([1, 1, 1])
                with col1a:
                    if st.button("Save", type="primary"):
                        self.save_rerank(st.session_state.selected_rerank_name, edit_default, edit_spec)
                        st.rerun()
                with col1b:
                    if not st.session_state.show_delete_confirm:
                        if st.button("Delete", type="secondary"):
                            st.session_state.show_delete_confirm = True
                            st.rerun()
                    else:
                        if st.button("Confirm Delete", type="primary"):
                            self.delete_rerank(st.session_state.selected_rerank_name)
                            st.session_state.selected_rerank_name = ""
                            st.session_state.show_delete_confirm = False
                            st.rerun()
                        if st.button("Cancel", type="secondary"):
                            st.session_state.show_delete_confirm = False
                            st.rerun()
                with col1c:
                    if st.button("Close"):
                        st.session_state.selected_rerank_name = ""
                        st.rerun()
            
            with col2:
                st.markdown(format_description(vendor))

    def render_add_tab(self):
        col1, col2 = st.columns([2, 3])
        
        with col1:
            name = st.text_input(
                "Name",
                help="Must be unique and non-empty. The name will be used to identify the reranking model."
            )
            
            vendor_choices = list(reranking_models_manager.vendors().keys())
            rerank_choice = st.selectbox(
                "Vendors",
                options=vendor_choices,
                help="Choose the vendor of the Reranking model. Each vendor has different specification."
            )
            
            vendor = reranking_models_manager.vendors()[rerank_choice]
            required_params = {}
            desc = vendor.describe()
            for key, value in desc["params"].items():
                if value.get("required", False):
                    required_params[key] = value.get("default", None)
            
            spec = st.text_area(
                "Specification",
                value=yaml.dump(required_params),
                height=300,
                help="Specification of the Reranking model in YAML format."
            )
            
            default = st.checkbox(
                "Set default",
                help="Set this Reranking model as default. This default Reranking will be used by other components by default if no Reranking is specified."
            )
            
            if st.button("Add", type="primary"):
                self.create_rerank(name, rerank_choice, spec, default)
                st.rerun()
        
        with col2:
            if rerank_choice:
                st.markdown(format_description(vendor))
            else:
                st.markdown(self.spec_desc_default)

    def create_rerank(self, name, choices, spec, default):
        try:
            spec = yaml.load(spec, Loader=YAMLNoDateSafeLoader)
            spec["__type__"] = (
                reranking_models_manager.vendors()[choices].__module__
                + "."
                + reranking_models_manager.vendors()[choices].__qualname__
            )

            reranking_models_manager.add(name, spec=spec, default=default)
            st.success(f'Create Reranking model "{name}" successfully')
        except Exception as e:
            st.error(f"Failed to create Reranking model {name}: {e}")

    def list_rerankings(self):
        items = []
        for item in reranking_models_manager.info().values():
            record = {}
            record["name"] = item["name"]
            record["vendor"] = item["spec"].get("__type__", "-").split(".")[-1]
            record["default"] = item["default"]
            items.append(record)

        if items:
            return pd.DataFrame.from_records(items)
        else:
            return pd.DataFrame(columns=["name", "vendor", "default"])

    def check_connection(self, selected_rerank_name, selected_spec):
        log_content = ""

        try:
            log_content += f"- Testing model: {selected_rerank_name}<br>"
            st.session_state.connection_logs = log_content
            st.rerun()

            # Parse content & init model
            info = copy.deepcopy(reranking_models_manager.info()[selected_rerank_name])

            # Parse content & create dummy response
            spec = yaml.load(selected_spec, Loader=YAMLNoDateSafeLoader)
            info["spec"].update(spec)

            rerank = deserialize(info["spec"], safe=False)

            if rerank is None:
                raise Exception(f"Can not found model: {selected_rerank_name}")

            log_content += "- Sending a message ([`Hello`], `Hi`)<br>"
            st.session_state.connection_logs = log_content
            st.rerun()
            
            _ = rerank([BaseComponent(content="Hello")], "Hi")

            log_content += (
                "<mark style='background: green; color: white'>- Connection success. "
                "</mark><br>"
            )
            st.session_state.connection_logs = log_content
            st.rerun()

            st.success(f"Reranking model {selected_rerank_name} connected successfully")
        except Exception as e:
            log_content += (
                f"<mark style='color: yellow; background: red'>- Connection failed. "
                f"Got error:\n {str(e)}</mark>"
            )
            st.session_state.connection_logs = log_content
            st.rerun()

    def save_rerank(self, selected_rerank_name, default, spec):
        try:
            spec = yaml.load(spec, Loader=YAMLNoDateSafeLoader)
            spec["__type__"] = reranking_models_manager.info()[selected_rerank_name]["spec"]["__type__"]
            reranking_models_manager.update(
                selected_rerank_name, spec=spec, default=default
            )
            st.success(f'Save Reranking model "{selected_rerank_name}" successfully')
        except Exception as e:
            st.error(f'Failed to save Reranking model "{selected_rerank_name}": {e}')

    def delete_rerank(self, selected_rerank_name):
        try:
            reranking_models_manager.delete(selected_rerank_name)
            st.success(f'Reranking model "{selected_rerank_name}" deleted successfully')
        except Exception as e:
            st.error(f'Failed to delete Reranking model "{selected_rerank_name}": {e}')