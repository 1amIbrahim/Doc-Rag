from copy import deepcopy
import streamlit as st
import pandas as pd
import yaml
from ktem.streamlit_app import StreamlitBaseApp
from ktem.utils.file import YAMLNoDateSafeLoader
from theflow.utils.modules import deserialize
from .manager import embedding_models_manager

def format_description(cls):
    params = cls.describe()["params"]
    params_lines = ["| Name | Type | Description |", "| --- | --- | --- |"]
    for key, value in params.items():
        if isinstance(value["auto_callback"], str):
            continue
        params_lines.append(f"| {key} | {value['type']} | {value['help']} |")
    return f"{cls.__doc__}\n\n" + "\n".join(params_lines)

class EmbeddingManagement(StreamlitBaseApp):
    def __init__(self, app):
        self._app = app
        self.spec_desc_default = "# Spec description\n\nSelect a model to view the spec description."
        self._selected_emb_name = None
        self._delete_confirm = False
        self.on_building_ui()

    def on_building_ui(self):
        tab1, tab2 = st.tabs(["View", "Add"])
        
        with tab1:
            self._render_view_tab()
            
        with tab2:
            self._render_add_tab()

    def _render_view_tab(self):
        emb_list = self.list_embeddings()
        
        if emb_list.empty or emb_list.iloc[0]["name"] == "-":
            st.warning("No embedding models available")
            return
            
        st.dataframe(
            emb_list,
            use_container_width=True,
            hide_index=True,
            column_config={
                "name": "Name",
                "vendor": "Vendor",
                "default": "Default"
            }
        )
        
        selected_emb = st.selectbox(
            "Select an embedding model",
            options=[""] + emb_list["name"].tolist(),
            key="selected_embedding"
        )
        
        if selected_emb:
            self._render_embedding_details(selected_emb)

    def _render_embedding_details(self, emb_name):
        info = deepcopy(embedding_models_manager.info()[emb_name])
        vendor_str = info["spec"].pop("__type__", "-").split(".")[-1]
        vendor = embedding_models_manager.vendors()[vendor_str]
        
        with st.expander(f"Edit {emb_name}", expanded=True):
            col1, col2 = st.columns([2, 3])
            
            with col1:
                default = st.checkbox(
                    "Set as default",
                    value=info["default"],
                    help="Set this as the default embedding model"
                )
                
                spec = st.text_area(
                    "Specification (YAML)",
                    value=yaml.dump(info["spec"]),
                    height=300
                )
                
                if st.button("Save Changes"):
                    self.save_emb(emb_name, default, spec)
                    st.rerun()
                    
                if st.button("Delete Model"):
                    self._delete_confirm = True
                    
                if self._delete_confirm:
                    st.warning("Are you sure you want to delete this model?")
                    if st.button("Confirm Delete"):
                        self.delete_emb(emb_name)
                        self._delete_confirm = False
                        st.rerun()
                    if st.button("Cancel"):
                        self._delete_confirm = False
                        st.rerun()
                        
                if st.button("Test Connection"):
                    self._test_connection(emb_name, spec)
            
            with col2:
                st.markdown(format_description(vendor))
                
    def _test_connection(self, emb_name, spec):
        with st.status("Testing connection..."):
            try:
                st.write(f"Testing model: {emb_name}")
                
                info = deepcopy(embedding_models_manager.info()[emb_name])
                spec_data = yaml.load(spec, Loader=YAMLNoDateSafeLoader)
                info["spec"].update(spec_data)
                
                emb = deserialize(info["spec"], safe=False)
                if emb is None:
                    raise Exception(f"Model not found: {emb_name}")
                
                st.write("Sending test message 'Hi'")
                _ = emb("Hi")
                
                st.success("Connection successful!")
            except Exception as e:
                st.error(f"Connection failed: {str(e)}")

    def _render_add_tab(self):
        vendors = list(embedding_models_manager.vendors().keys())
        
        with st.form("add_embedding"):
            name = st.text_input(
                "Name",
                help="Must be unique and non-empty"
            )
            
            vendor = st.selectbox(
                "Vendor",
                options=vendors,
                help="Choose the vendor of the Embedding model"
            )
            
            spec = st.text_area(
                "Specification (YAML)",
                value=yaml.dump({}),
                height=200
            )
            
            default = st.checkbox(
                "Set as default",
                help="Set this as the default embedding model"
            )
            
            if st.form_submit_button("Add Embedding"):
                self.create_emb(name, vendor, spec, default)
                st.rerun()
        
        if vendor:
            st.markdown(format_description(embedding_models_manager.vendors()[vendor]))

    def create_emb(self, name, vendor, spec, default):
        try:
            spec = yaml.load(spec, Loader=YAMLNoDateSafeLoader)
            spec["__type__"] = (
                embedding_models_manager.vendors()[vendor].__module__ + "." +
                embedding_models_manager.vendors()[vendor].__qualname__
            )
            embedding_models_manager.add(name, spec=spec, default=default)
            st.success(f'Created Embedding model "{name}" successfully')
        except Exception as e:
            st.error(f"Failed to create Embedding model {name}: {e}")

    def list_embeddings(self):
        items = []
        for item in embedding_models_manager.info().values():
            record = {
                "name": item["name"],
                "vendor": item["spec"].get("__type__", "-").split(".")[-1],
                "default": item["default"]
            }
            items.append(record)

        return pd.DataFrame(items if items else [{"name": "-", "vendor": "-", "default": "-"}])

    def save_emb(self, emb_name, default, spec):
        try:
            spec = yaml.load(spec, Loader=YAMLNoDateSafeLoader)
            spec["__type__"] = embedding_models_manager.info()[emb_name]["spec"]["__type__"]
            embedding_models_manager.update(emb_name, spec=spec, default=default)
            st.success(f'Saved Embedding model "{emb_name}" successfully')
        except Exception as e:
            st.error(f'Failed to save Embedding model "{emb_name}": {e}')

    def delete_emb(self, emb_name):
        try:
            embedding_models_manager.delete(emb_name)
            st.success(f'Deleted Embedding model "{emb_name}" successfully')
        except Exception as e:
            st.error(f'Failed to delete Embedding model "{emb_name}": {e}')