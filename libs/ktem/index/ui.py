import streamlit as st
import yaml
from ktem.utils.file import YAMLNoDateSafeLoader
from .manager import IndexManager
import pandas as pd
class IndexManagement:
    def __init__(self, app):
        self.app = app
        self.manager: IndexManager = app.index_manager
        self.render()

    def render(self):
        st.header("Index Management")

        tabs = st.tabs(["View", "Add"])

        # === View Tab ===
        with tabs[0]:
            indices_df = self.list_indices()
            st.dataframe(indices_df, use_container_width=True)

            selected_index = st.number_input(
                "Selected Index ID", min_value=-1, step=1, value=-1, key="selected_index_id"
            )

            if selected_index != -1 and selected_index < len(self.manager.indices):
                index = self.manager.info()[selected_index]
                st.subheader("Edit Index")
                
                name = st.text_input("Index name", index.name, key="edit_name")
                spec = st.text_area(
                    "Index config (YAML)", yaml.dump(index.config), height=300, key="edit_spec"
                )
                
                st.warning("⚠️ Changing or deleting the index requires restarting the system.")

                col1, col2, col3 = st.columns([1, 1, 1])
                if col1.button("Save", key="btn_edit_save"):
                    self.update_index(selected_index, name, spec)

                if col2.button("Delete", key="btn_delete"):
                    confirm = st.checkbox("Confirm deletion")
                    if confirm and col2.button("Confirm Delete"):
                        self.delete_index(selected_index)

                if col3.button("Close", key="btn_close"):
                    st.session_state["selected_index_id"] = -1

        # === Add Tab ===
        with tabs[1]:
            st.subheader("Add New Index")

            name = st.text_input("Index name", key="new_index_name")
            index_type_keys = list(self.manager.index_types.keys())
            index_type = st.selectbox("Index type", options=index_type_keys, key="new_index_type")

            default_config, desc = self.on_index_type_change(index_type)
            spec = st.text_area("Specification (YAML)", default_config, height=300, key="new_spec")

            st.markdown(desc, unsafe_allow_html=True)

            if st.button("Add", key="btn_add_index"):
                self.create_index(name, index_type, spec)

    def list_indices(self):
        items = []
        for item in self.manager.indices:
            record = {
                "id": item.id,
                "name": item.name,
                "index type": item.__class__.__name__,
            }
            items.append(record)

        if not items:
            return pd.DataFrame([{"id": "-", "name": "-", "index type": "-"}])
        return pd.DataFrame(items)

    def create_index(self, name: str, index_type: str, config: str):
        try:
            self.manager.build_index(
                name=name,
                config=yaml.load(config, Loader=YAMLNoDateSafeLoader),
                index_type=index_type,
            )
            st.success(f'Created index "{name}" successfully. Please restart the app.')
        except Exception as e:
            st.error(f"Failed to create index {name}: {e}")

    def update_index(self, selected_index_id: int, name: str, config: str):
        try:
            spec = yaml.load(config, Loader=YAMLNoDateSafeLoader)
            self.manager.update_index(selected_index_id, name, spec)
            st.success(f'Updated index "{name}" successfully. Please restart the app.')
        except Exception as e:
            st.error(f"Failed to update index {name}: {e}")

    def delete_index(self, selected_index_id: int):
        try:
            self.manager.delete_index(selected_index_id)
            st.success("Deleted index successfully. Please restart the app.")
            st.session_state["selected_index_id"] = -1
        except Exception as e:
            st.warning(f"Failed to delete index: {e}")
    
    def format_description(self,index_type_cls):
        """Returns a formatted description of the index type."""
        return f"Index Type: {index_type_cls.__name__}\nDescription: {index_type_cls.__doc__}"

    
    def on_index_type_change(self, index_type: str):
        """Handles index type selection and returns default config and description."""
        if index_type not in self.manager.index_types:
            return "", "Invalid index type"

        index_type_cls = self.manager.index_types[index_type]
        required_config = {
            key: value.get("value", None)
            for key, value in index_type_cls.get_admin_settings().items()
        }
        
        import yaml
        return yaml.dump(required_config, sort_keys=False), self.format_description(index_type_cls)

