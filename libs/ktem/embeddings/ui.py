import streamlit as st
import pandas as pd
import yaml
from copy import deepcopy
from theflow.utils.modules import deserialize
from ktem.utils.file import YAMLNoDateSafeLoader
from .manager import embedding_models_manager


def format_description(cls):
    params = cls.describe()["params"]
    params_lines = ["| Name | Type | Description |", "| --- | --- | --- |"]
    for key, value in params.items():
        if isinstance(value["auto_callback"], str):
            continue
        params_lines.append(f"| {key} | {value['type']} | {value['help']} |")
    return f"{cls.__doc__}\n\n" + "\n".join(params_lines)


class EmbeddingManagement:
    def __init__(self,app):
        self.spec_desc_default = (
            "# Spec description\n\nSelect a model to view the spec description."
        )
        self.selected_emb_name = ""
        self.emb_list = None
        self.emb_choices = None
        self._selected_panel = None
        self._check_connection_panel = None
        self._selected_panel_btn = None
        self.on_building_ui()

    def on_building_ui(self):
        st.sidebar.title("Embedding Management")
        tab = st.sidebar.radio("Choose tab", ["View", "Add"])

        if tab == "View":
            self.view_embeddings_tab()
        elif tab == "Add":
            self.add_embedding_tab()

    def view_embeddings_tab(self):
        self.emb_list = self.list_embeddings()
        if not self.emb_list.empty:
            st.write(self.emb_list)
        else:
            st.write("No embeddings available. Please add one.")

        if self.selected_emb_name:
            self.show_selected_embedding_details()
        else:
            st.write("No embedding selected.")

    def add_embedding_tab(self):
        self.name = st.text_input("Name", help="Must be unique and non-empty.")
        self.emb_choices = st.selectbox("Vendors", options=list(embedding_models_manager.vendors().keys()))
        self.spec = st.text_area("Specification", help="Specification of the Embedding model in YAML format.")
        self.default = st.checkbox("Set default", help="Set this Embedding model as default.")

        if st.button("Add"):
            self.create_emb(self.name, self.emb_choices, self.spec, self.default)

        st.markdown(self.spec_desc_default)

    def create_emb(self, name, choices, spec, default):
        try:
            spec = yaml.load(spec, Loader=YAMLNoDateSafeLoader)
            spec["__type__"] = (
                embedding_models_manager.vendors()[choices].__module__
                + "." + embedding_models_manager.vendors()[choices].__qualname__
            )

            embedding_models_manager.add(name, spec=spec, default=default)
            st.success(f'Created Embedding model "{name}" successfully.')
        except Exception as e:
            st.error(f"Failed to create Embedding model {name}: {e}")

    def list_embeddings(self):
        """List the Embedding models"""
        items = []
        for item in embedding_models_manager.info().values():
            record = {
                "name": item["name"],
                "vendor": item["spec"].get("__type__", "-").split(".")[-1],
                "default": item["default"]
            }
            items.append(record)

        if items:
            return pd.DataFrame.from_records(items)
        else:
            return pd.DataFrame.from_records([{"name": "-", "vendor": "-", "default": "-"}])

    def select_emb(self, emb_list, ev):
        if ev == "-" and ev.index[0] == 0:
            st.info("No embedding model is loaded. Please add first")
            return ""

        if not ev:
            return ""

        return emb_list["name"][ev.index[0]]

    def on_selected_emb_change(self, selected_emb_name):
        if selected_emb_name == "":
            return "", "", "", "", "", "", "", False

        info = deepcopy(embedding_models_manager.info()[selected_emb_name])
        vendor_str = info["spec"].pop("__type__", "-").split(".")[-1]
        vendor = embedding_models_manager.vendors()[vendor_str]

        edit_spec = yaml.dump(info["spec"])
        edit_spec_desc = format_description(vendor)
        edit_default = info["default"]

        return edit_spec, edit_spec_desc, edit_default

    def show_selected_embedding_details(self):
        spec, spec_desc, default = self.on_selected_emb_change(self.selected_emb_name)

        with st.expander("Edit Embedding Model"):
            st.text_area("Specification", value=spec, height=300)
            st.markdown(spec_desc)
            st.checkbox("Set as Default", value=default)

        st.button("Save", on_click=self.save_emb, args=(self.selected_emb_name, default, spec))
        st.button("Delete", on_click=self.delete_emb, args=(self.selected_emb_name,))

    def save_emb(self, selected_emb_name, default, spec):
        try:
            spec = yaml.load(spec, Loader=YAMLNoDateSafeLoader)
            spec["__type__"] = embedding_models_manager.info()[selected_emb_name]["spec"]["__type__"]
            embedding_models_manager.update(selected_emb_name, spec=spec, default=default)
            st.success(f'Saved Embedding model "{selected_emb_name}" successfully.')
        except Exception as e:
            st.error(f'Failed to save Embedding model "{selected_emb_name}": {e}')

    def delete_emb(self, selected_emb_name):
        try:
            embedding_models_manager.delete(selected_emb_name)
            st.success(f'Deleted Embedding model "{selected_emb_name}" successfully.')
        except Exception as e:
            st.error(f'Failed to delete Embedding model "{selected_emb_name}": {e}')

    def check_connection(self, selected_emb_name, selected_spec):
        log_content = ""
        try:
            log_content += f"- Testing model: {selected_emb_name}\n"

            info = deepcopy(embedding_models_manager.info()[selected_emb_name])

            spec = yaml.load(selected_spec, Loader=YAMLNoDateSafeLoader)
            info["spec"].update(spec)

            emb = deserialize(info["spec"], safe=False)

            if emb is None:
                raise Exception(f"Cannot find model: {selected_emb_name}")

            log_content += "- Sending a message `Hi`\n"
            _ = emb("Hi")

            log_content += "Connection success.\n"
            st.success("Connection successful")
        except Exception as e:
            log_content += f"Connection failed. Error: {e}\n"
            st.error(f"Connection failed: {e}")

        st.text_area("Connection Logs", log_content, height=300)


if __name__ == "__main__":
    app = EmbeddingManagement()
    app.on_building_ui()
