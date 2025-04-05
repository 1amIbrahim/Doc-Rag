import streamlit as st
import pandas as pd
import yaml
from copy import deepcopy
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
    def __init__(self,app):
        self.spec_desc_default = "# Spec description\n\nSelect an LLM to view the spec description."
        self.selected_llm_name = None
        self.on_building_ui()

    def on_building_ui(self):
        st.title("LLM Management")

        tab1, tab2 = st.tabs(["View", "Add"])

        # VIEW TAB
        with tab1:
            # DataFrame for listing LLMs
            llm_data = []
            for item in llms.info().values():
                llm_data.append({
                    "name": item["name"],
                    "vendor": item["spec"].get("__type__", "-").split(".")[-1],
                    "default": item["default"]
                })
            llm_df = pd.DataFrame(llm_data) if llm_data else pd.DataFrame([{"name": "-", "vendor": "-", "default": "-"}])

            selected_row = st.dataframe(llm_df, use_container_width=True)

            llm_names = list(llms.info().keys())
            selected_llm = st.selectbox("Select LLM", [""] + llm_names)

            if selected_llm:
                self.selected_llm_name = selected_llm
                info = deepcopy(llms.info()[selected_llm])
                vendor_name = info["spec"].pop("__type__", "-").split(".")[-1]
                vendor = llms.vendors()[vendor_name]

                spec_desc = format_description(vendor)
                st.subheader(f"Editing: {selected_llm}")
                st.markdown(spec_desc)

                edited_spec = st.text_area("Specification (YAML)", value=yaml.dump(info["spec"]), height=300)
                set_default = st.checkbox("Set as default", value=info["default"])

                if st.button("Test Connection"):
                    with st.spinner("Testing connection..."):
                        log_content = f"- Testing model: {selected_llm}<br>"
                        try:
                            spec = yaml.load(edited_spec, Loader=YAMLNoDateSafeLoader)
                            info["spec"].update(spec)
                            llm = deserialize(info["spec"], safe=False)
                            respond = llm("Hi")
                            log_content += f"<mark style='background: green; color: white'>- Connection success. Got response: {respond}</mark><br>"
                        except Exception as e:
                            log_content += f"<mark style='background: red; color: white'>- Connection failed: {e}</mark><br>"
                        st.markdown(log_content, unsafe_allow_html=True)

                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Save"):
                        try:
                            spec = yaml.load(edited_spec, Loader=YAMLNoDateSafeLoader)
                            spec["__type__"] = llms.info()[selected_llm]["spec"]["__type__"]
                            llms.update(selected_llm, spec=spec, default=set_default)
                            st.success(f"LLM {selected_llm} saved successfully")
                        except Exception as e:
                            st.error(f"Failed to save LLM {selected_llm}: {e}")
                with col2:
                    if st.button("Delete"):
                        try:
                            llms.delete(selected_llm)
                            st.success(f"LLM {selected_llm} deleted successfully")
                            self.selected_llm_name = None
                        except Exception as e:
                            st.error(f"Failed to delete LLM {selected_llm}: {e}")
                with col3:
                    if st.button("Close"):
                        self.selected_llm_name = None

        # ADD TAB
        with tab2:
            st.subheader("Add a new LLM")
            llm_name = st.text_input("LLM name")
            vendor_list = list(llms.vendors().keys())
            vendor_choice = st.selectbox("LLM Vendor", vendor_list)

            if vendor_choice:
                required_spec = yaml.dump({
                    k: None
                    for k, v in llms.vendors()[vendor_choice].describe()["params"].items()
                    if v.get("required", False)
                })
                spec_description = format_description(llms.vendors()[vendor_choice])
                st.markdown(spec_description)
            else:
                required_spec = ""

            llm_spec = st.text_area("Specification (YAML)", value=required_spec, height=250)
            set_default = st.checkbox("Set default")

            if st.button("Add LLM"):
                try:
                    spec = yaml.load(llm_spec, Loader=YAMLNoDateSafeLoader)
                    spec["__type__"] = (
                        llms.vendors()[vendor_choice].__module__
                        + "." + llms.vendors()[vendor_choice].__qualname__
                    )
                    llms.add(llm_name, spec=spec, default=set_default)
                    st.success(f"LLM {llm_name} created successfully")
                except Exception as e:
                    st.error(f"Failed to create LLM: {e}")

    def on_register_events(self):
        """Register events and interactions"""
        pass


# Instantiate and use in your Streamlit app
if __name__ == "__main__":
    llm_management = LLMManagement()
    llm_management.on_register_events()
