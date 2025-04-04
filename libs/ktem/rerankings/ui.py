import yaml
import pandas as pd
import streamlit as st
from copy import deepcopy
from kotaemon.base import Document
from theflow.utils.modules import deserialize
from ktem.utils.file import YAMLNoDateSafeLoader
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
    def __init__(self,app):
        self.spec_desc_default = (
            "# Spec description\n\nSelect a model to view the spec description."
        )
        self.selected_rerank_name = None
        self._init_ui()

    def _init_ui(self):
        # Tab for "View"
        st.subheader("View")
        
        self.rerank_list = st.dataframe(
            self.list_rerankings(),
            use_container_width=True,
        )

        # Tab for "Add"
        st.subheader("Add")
        self.name = st.text_input(
            label="Name",
            help="Must be unique and non-empty. The name will be used to identify the reranking model.",
        )
        self.rerank_choices = st.selectbox(
            label="Vendors",
            options=list(reranking_models_manager.vendors().keys()),
            help="Choose the vendor of the Reranking model. Each vendor has different specification.",
        )
        self.spec = st.text_area(
            label="Specification",
            help="Specification of the Embedding model in YAML format.",
        )
        self.default = st.checkbox(
            label="Set default",
            help="Set this Reranking model as default. This default Reranking will be used by other components by default if no Reranking is specified for such components.",
        )

        st.button("Add", on_click=self.create_rerank)

        # For the selected model
        if self.selected_rerank_name:
            self._show_selected_rerank()

    def _show_selected_rerank(self):
        info = deepcopy(reranking_models_manager.info()[self.selected_rerank_name])
        vendor_str = info["spec"].pop("__type__", "-").split(".")[-1]
        vendor = reranking_models_manager.vendors()[vendor_str]

        st.subheader("Edit Model")
        edit_spec = st.text_area("Specification", value=yaml.dump(info["spec"]), height=200)
        edit_spec_desc = format_description(vendor)
        st.markdown(edit_spec_desc)

        edit_default = st.checkbox("Set Default", value=info["default"])

        if st.button("Save"):
            self.save_rerank(self.selected_rerank_name, edit_default, edit_spec)
        if st.button("Delete"):
            self.delete_rerank(self.selected_rerank_name)

    def list_rerankings(self):
        """List the Reranking models"""
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
            return pd.DataFrame.from_records(
                [{"name": "-", "vendor": "-", "default": "-"}]
            )

    def create_rerank(self):
        try:
            spec = yaml.load(self.spec, Loader=YAMLNoDateSafeLoader)
            spec["__type__"] = (
                reranking_models_manager.vendors()[self.rerank_choices].__module__
                + "."
                + reranking_models_manager.vendors()[self.rerank_choices].__qualname__
            )

            reranking_models_manager.add(self.name, spec=spec, default=self.default)
            st.success(f'Create Reranking model "{self.name}" successfully')
        except Exception as e:
            st.error(f"Failed to create Reranking model {self.name}: {e}")

    def save_rerank(self, selected_rerank_name, default, spec):
        try:
            spec = yaml.load(spec, Loader=YAMLNoDateSafeLoader)
            spec["__type__"] = reranking_models_manager.info()[selected_rerank_name][
                "spec"
            ]["__type__"]
            reranking_models_manager.update(
                selected_rerank_name, spec=spec, default=default
            )
            st.success(f'Save Reranking model "{selected_rerank_name}" successfully')
        except Exception as e:
            st.error(f'Failed to save Embedding model "{selected_rerank_name}": {e}')

    def delete_rerank(self, selected_rerank_name):
        try:
            reranking_models_manager.delete(selected_rerank_name)
            self.selected_rerank_name = None
            st.success(f'Deleted Reranking model "{selected_rerank_name}" successfully')
        except Exception as e:
            st.error(f'Failed to delete Reranking model "{selected_rerank_name}": {e}')

    def on_rerank_vendor_change(self):
        vendor = reranking_models_manager.vendors()[self.rerank_choices]
        required = {}
        desc = vendor.describe()
        for key, value in desc["params"].items():
            if value.get("required", False):
                required[key] = value.get("default", None)

        return yaml.dump(required), format_description(vendor)

    def check_connection(self, selected_rerank_name, selected_spec):
        log_content: str = ""
        try:
            log_content += f"- Testing model: {selected_rerank_name}<br>"
            yield log_content

            info = deepcopy(reranking_models_manager.info()[selected_rerank_name])
            spec = yaml.load(selected_spec, Loader=YAMLNoDateSafeLoader)
            info["spec"].update(spec)

            rerank = deserialize(info["spec"], safe=False)

            if rerank is None:
                raise Exception(f"Cannot find model: {selected_rerank_name}")

            log_content += "- Sending a message ([`Hello`], `Hi`)<br>"
            yield log_content
            _ = rerank([Document(content="Hello")], "Hi")

            log_content += (
                "<mark style='background: green; color: white'>- Connection success. "
                "</mark><br>"
            )
            yield log_content

            st.success(f"Embedding {selected_rerank_name} connected successfully")
        except Exception as e:
            log_content += (
                f"<mark style='color: yellow; background: red'>- Connection failed. "
                f"Got error:\n {str(e)}</mark>"
            )
            yield log_content

            st.error(f"Connection failed: {str(e)}")
