import streamlit as st
import pandas as pd
import yaml
import time
import os

from ktem.streamlit_app import StreamlitBaseApp
from ktem.utils.file import YAMLNoDateSafeLoader
from .manager import IndexManager


def update_current_module_atime():
    file_path = __file__
    print("Updating atime for", file_path)
    current_time = time.time()
    os.utime(file_path, (current_time, current_time))


def format_description(cls):
    user_settings = cls.get_admin_settings()
    params_lines = ["| Name | Default | Description |", "| --- | --- | --- |"]
    for key, value in user_settings.items():
        params_lines.append(
            f"| {key} | {value.get('value', '')} | {value.get('info', '')} |"
        )
    return f"{cls.__doc__}\n\n" + "\n".join(params_lines)


class IndexManagement(StreamlitBaseApp):
    def __init__(self, app):
        self._app = app
        self.manager: IndexManager = app.index_manager
        self.spec_desc_default = "# Spec description\n\nSelect an index to view the spec description."
        self.selected_index_id = -1
        self.on_building_ui()

    def on_building_ui(self):
        tab1, tab2 = st.tabs(["View", "Add"])

        with tab1:
            st.header("View Indices")
            self.index_df = self.list_indices()
            selected = st.dataframe(self.index_df)

            selected_index = st.number_input("Selected Index ID", value=-1, step=1)
            if st.button("Load Index Details"):
                self.selected_index_id = int(selected_index)
                self.show_index_details(self.selected_index_id)

        with tab2:
            st.header("Add New Index")
            self.name = st.text_input("Index Name")
            index_types = [(key.split(".")[-1], key) for key in self.manager.index_types.keys()]
            type_labels = [name for name, key in index_types]
            type_keys = {name: key for name, key in index_types}

            self.index_type = st.selectbox("Index Type", options=type_labels)

            self.spec = st.text_area(
                "Specification (YAML format)",
                height=300,
            )
            st.markdown("<mark>Note</mark>: After creating index, please restart the app", unsafe_allow_html=True)

            if st.button("Add Index"):
                if self.name and self.index_type and self.spec:
                    self.create_index(
                        self.name,
                        type_keys[self.index_type],
                        self.spec
                    )
                    update_current_module_atime()
                else:
                    st.warning("Please fill all fields!")

    def show_index_details(self, selected_index_id):
        if selected_index_id == -1:
            st.info("No index selected.")
            return

        index_info = self.manager.info().get(selected_index_id)
        if not index_info:
            st.error("Invalid Index ID")
            return

        with st.expander("Edit Index"):
            new_name = st.text_input("Edit Name", value=index_info.name)
            new_spec = st.text_area("Edit Spec (YAML)", value=yaml.dump(index_info.config), height=300)
            st.markdown(format_description(index_info.__class__))

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Save Changes"):
                    self.update_index(selected_index_id, new_name, new_spec)
                    update_current_module_atime()
            with col2:
                if st.button("Delete Index", type="primary"):
                    if st.confirm("Are you sure you want to delete this index?"):
                        self.delete_index(selected_index_id)
                        update_current_module_atime()
            with col3:
                if st.button("Close"):
                    self.selected_index_id = -1

    def on_index_type_change(self, index_type: str):
        index_type_cls = self.manager.index_types[index_type]
        required = {
            key: value.get("value", None)
            for key, value in index_type_cls.get_admin_settings().items()
        }
        return yaml.dump(required, sort_keys=False), format_description(index_type_cls)

    def create_index(self, name: str, index_type: str, config: str):
        try:
            self.manager.build_index(
                name=name,
                config=yaml.load(config, Loader=YAMLNoDateSafeLoader),
                index_type=index_type,
            )
            st.success(f'Created index "{name}" successfully. Please restart the app!')
        except Exception as e:
            st.error(f"Failed to create index {name}: {e}")

    def list_indices(self):
        items = []
        for item in self.manager.indices:
            record = {
                "id": item.id,
                "name": item.name,
                "index type": item.__class__.__name__,
            }
            items.append(record)

        if items:
            return pd.DataFrame.from_records(items)
        else:
            return pd.DataFrame([{"id": "-", "name": "-", "index type": "-"}])

    def update_index(self, selected_index_id: int, name: str, config: str):
        try:
            spec = yaml.load(config, Loader=YAMLNoDateSafeLoader)
            self.manager.update_index(selected_index_id, name, spec)
            st.success(f'Updated index "{name}" successfully. Please restart the app!')
        except Exception as e:
            st.error(f'Failed to save index "{name}": {e}')

    def delete_index(self, selected_index_id):
        try:
            self.manager.delete_index(selected_index_id)
            st.success("Deleted index successfully. Please restart the app!")
        except Exception as e:
            st.warning(f"Failed to delete index: {e}")
