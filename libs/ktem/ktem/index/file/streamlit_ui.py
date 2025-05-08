import os
import json
import shutil
import zipfile
import tempfile
from pathlib import Path
from copy import deepcopy
from typing import Generator, List, Tuple, Dict, Optional
import pandas as pd
import streamlit as st
from sqlalchemy import select
from sqlalchemy.orm import Session

# Assuming these are available from your original imports
from ktem.db.engine import engine
from ktem.app import BasePage
from ktem.utils.render import Render
from theflow.settings import settings as flowsettings
from ...utils.commands import WEB_SEARCH_COMMAND
from ...utils.rate_limit import check_rate_limit
from .utils import download_arxiv_pdf, is_arxiv_url

# Constants (from original)
KH_DEMO_MODE = getattr(flowsettings, "KH_DEMO_MODE", False)
KH_SSO_ENABLED = getattr(flowsettings, "KH_SSO_ENABLED", False)
DOWNLOAD_MESSAGE = "Start download"
MAX_FILENAME_LENGTH = 20
MAX_FILE_COUNT = 200

class FileManager:
    """Base class for file management functionality"""
    
    def __init__(self, index):
        self._index = index
        self._supported_file_types_str = self._index.config.get("supported_file_types", "")
        self._supported_file_types = [each.strip() for each in self._supported_file_types_str.split(",")]
        
    def format_size_human_readable(self, num: float | str, suffix="B"):
        try:
            num = float(num)
        except ValueError:
            return num

        for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
            if abs(num) < 1024.0:
                return f"{num:3.0f}{unit}{suffix}"
            num /= 1024.0
        return f"{num:.0f}Yi{suffix}"

    def _may_extract_zip(self, files: List[str], zip_dir: str) -> List[str]:
        """Handle zip files (from original)"""
        zip_files = [file for file in files if file.endswith(".zip")]
        remaining_files = [file for file in files if not file.endswith("zip")]

        # Clean-up <zip_dir> before unzip to remove old files
        shutil.rmtree(zip_dir, ignore_errors=True)

        for zip_file in zip_files:
            basename = os.path.splitext(os.path.basename(zip_file))[0]
            zip_out_dir = os.path.join(zip_dir, basename)
            os.makedirs(zip_out_dir, exist_ok=True)
            with zipfile.ZipFile(zip_file, "r") as zip_ref:
                zip_ref.extractall(zip_out_dir)

        n_zip_file = 0
        for root, dirs, files in os.walk(zip_dir):
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext not in [".zip"] and ext in self._supported_file_types:
                    remaining_files.append(os.path.join(root, file))
                    n_zip_file += 1

        if n_zip_file > 0:
            st.info(f"Extracted {n_zip_file} files from zip archives")

        return remaining_files

    def validate(self, files: List[str]) -> List[str]:
        """Validate if the files are valid (from original)"""
        paths = [Path(file) for file in files]
        errors = []
        if max_file_size := self._index.config.get("max_file_size", 0):
            errors_max_size = []
            for path in paths:
                if path.stat().st_size > max_file_size * 1e6:
                    errors_max_size.append(path.name)
            if errors_max_size:
                str_errors = ", ".join(errors_max_size)
                if len(str_errors) > 60:
                    str_errors = str_errors[:55] + "..."
                errors.append(
                    f"Maximum file size ({max_file_size} MB) exceeded: {str_errors}"
                )

        if max_number_of_files := self._index.config.get("max_number_of_files", 0):
            with Session(engine) as session:
                current_num_files = session.query(
                    self._index._resources["Source"].id
                ).count()
            if len(paths) + current_num_files > max_number_of_files:
                errors.append(
                    f"Maximum number of files ({max_number_of_files}) will be exceeded"
                )

        return errors

class DirectoryUploadUI(FileManager):
    """Streamlit implementation of DirectoryUpload"""
    
    def render(self):
        with st.expander("Directory upload", expanded=False):
            st.markdown(f"Supported file types: {self._supported_file_types_str}")
            
            self.path = st.text_input(
                "Directory path",
                placeholder="Directory path...",
                key="dir_upload_path"
            )
            
            with st.expander("Advanced indexing options", expanded=False):
                self.reindex = st.checkbox(
                    "Force reindex file",
                    value=False,
                    key="dir_reindex"
                )
            
            if st.button("Upload and Index"):
                self.handle_upload()

    def handle_upload(self):
        if not self.path:
            st.warning("Please enter a directory path")
            return
            
        # Implement directory indexing logic here
        st.info(f"Indexing directory: {self.path}")
        # Call appropriate indexing methods from FileManager

class FileIndexUI(BasePage):
    """Streamlit implementation of FileIndexPage"""
    
    def __init__(self, index):
        super().__init__(index)
        self._index = index
        self._supported_file_types_str = self._index.config.get("supported_file_types", "")
        self._supported_file_types = [each.strip() for each in self._supported_file_types_str.split(",")]
        
        self.selected_panel_false = "Selected file: (please select above)"
        self.selected_panel_true = "Selected file: {name}"
        
        if not KH_DEMO_MODE:
            self.initialize_session_state()
            #self.render_ui()

    def initialize_session_state(self):
        if 'file_list_state' not in st.session_state:
            st.session_state.file_list_state = []
        if 'selected_file_id' not in st.session_state:
            st.session_state.selected_file_id = None
        if 'group_list_state' not in st.session_state:
            st.session_state.group_list_state = []
        if 'selected_group_id' not in st.session_state:
            st.session_state.selected_group_id = None

    def upload_instruction(self) -> str:
        msgs = []
        if self._supported_file_types:
            msgs.append(f"- Supported file types: {self._supported_file_types_str}")

        if max_file_size := self._index.config.get("max_file_size", 0):
            msgs.append(f"- Maximum file size: {max_file_size} MB")

        if max_number_of_files := self._index.config.get("max_number_of_files", 0):
            st.session_state.max_files = max_number_of_files
            msgs.append(f"- The index can have maximum {max_number_of_files} files")

        if msgs:
            return "\n".join(msgs)
        return ""

    def render_ui(self):
        """Main UI rendering method"""
        st.title("File Management")
        
        col1, col2 = st.columns([1, 4])
        
        with col1:
            self.render_upload_panel()
        
        with col2:
            tab1, tab2 = st.tabs(["Files", "Groups"])
            
            with tab1:
                self.render_file_list()
            
            with tab2:
                self.render_group_list()

    def render_upload_panel(self):
        """Render the upload panel"""
        with st.container():
            st.subheader("Upload Files")
            
            upload_tab, url_tab = st.tabs(["Upload Files", "Use Web Links"])
            
            with upload_tab:
                self.files = st.file_uploader(
                    "Choose files",
                    type=self._supported_file_types,
                    accept_multiple_files=True,
                    key="file_uploader"
                )
                
                msg = self.upload_instruction()
                if msg:
                    st.markdown(msg)

            with url_tab:
                self.urls = st.text_area(
                    "Input web URLs",
                    height=200,
                    placeholder="Enter one URL per line",
                    key="url_input"
                )
                st.markdown("(separated by new line)")

            with st.expander("Advanced indexing options", expanded=False):
                self.reindex = st.checkbox(
                    "Force reindex file",
                    value=False,
                    key="reindex_checkbox"
                )

            if st.button("Upload and Index", type="primary"):
                self.handle_upload()

    def render_file_list(self):
        """Render the file list and associated controls"""
        st.subheader("Files")
        
        # Filter input
        self.filter = st.text_input(
            "Filter by name:",
            key="file_filter",
            help="(1) Case-insensitive. (2) Search with empty string to show all files."
        )
        
        # Display file list
        file_list_state, file_list_df = self.list_file(st.session_state.get('user_id'), self.filter)
        print("User id = ",st.session_state.get('user_id'))
        st.session_state.file_list_state = file_list_state
        
        # Display as editable dataframe
        edited_df = st.data_editor(
            file_list_df,
            hide_index=True,
            disabled=["id", "name", "size", "tokens", "loader", "date_created"],
            use_container_width=True,
            key="file_data_editor"
        )
        
        # Selection handling
        if st.session_state.get('file_data_editor', {}).get('edited_rows'):
            selected_row = list(st.session_state.file_data_editor['edited_rows'].keys())[0]
            self.handle_file_selection(selected_row)
        
        # Selected file panel
        if st.session_state.selected_file_id:
            self.render_selected_file_panel()
        
        # Advanced options
        with st.expander("Advanced options", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                if not KH_SSO_ENABLED and st.button("Download all files"):
                    self.download_all_files()
            
            with col2:
                if st.button("Delete all files", type="secondary"):
                    st.session_state.show_delete_all_confirm = True
                
                if st.session_state.get('show_delete_all_confirm'):
                    st.warning("Are you sure you want to delete all files?")
                    confirm_col1, confirm_col2 = st.columns(2)
                    with confirm_col1:
                        if st.button("Confirm delete", type="primary"):
                            self.delete_all_files(file_list_state)
                            st.session_state.show_delete_all_confirm = False
                            st.rerun()
                    with confirm_col2:
                        if st.button("Cancel"):
                            st.session_state.show_delete_all_confirm = False
                            st.rerun()

    def render_selected_file_panel(self):
        """Render panel for selected file"""
        st.markdown(f"**Selected file:** {self.get_selected_file_name()}")
        
        cols = st.columns(4)
        with cols[0]:
            if st.button("Go to Chat"):
                self.set_file_id_selector(st.session_state.selected_file_id)
        
        with cols[1]:
            if not KH_SSO_ENABLED:
                if st.button(DOWNLOAD_MESSAGE):
                    self.download_single_file(st.session_state.selected_file_id)
            else:
                if st.button(DOWNLOAD_MESSAGE):
                    self.download_single_file_simple(st.session_state.selected_file_id)
        
        with cols[2]:
            if st.button("Delete", type="secondary"):
                self.delete_event(st.session_state.selected_file_id)
                st.rerun()
        
        with cols[3]:
            if st.button("Close"):
                st.session_state.selected_file_id = None
                st.rerun()
        
        # Show file chunks/preview
        self.render_file_chunks(st.session_state.selected_file_id)

    def render_file_chunks(self, file_id):
        """Render file chunks/preview (from original file_selected method)"""
        if file_id is None:
            return

        chunks = []
        Index = self._index._resources["Index"]
        with Session(engine) as session:
            matches = session.execute(
                select(Index).where(
                    Index.source_id == file_id,
                    Index.relation_type == "document",
                )
            )
            doc_ids = [doc.target_id for (doc,) in matches]
            docs = self._index._docstore.get(doc_ids)
            docs = sorted(
                docs, key=lambda x: x.metadata.get("page_label", float("inf"))
            )

            for idx, doc in enumerate(docs):
                title = f"{doc.text[:50]}..." if len(doc.text) > 50 else doc.text
                doc_type = doc.metadata.get("type", "text")
                
                with st.expander(f"Chunk {idx+1}/{len(docs)} - {title}"):
                    if doc_type == "text":
                        st.text(doc.text)
                    elif doc_type == "table":
                        st.table(pd.read_json(doc.text))
                    elif doc_type == "image":
                        st.image(doc.metadata.get("image_origin", ""), caption=doc.text)

    def render_group_list(self):
        """Render the group list and associated controls"""
        st.subheader("Groups")
        
        # Display group list
        group_list_state, group_list_df = self.list_group(
            st.session_state.get('user_id'), 
            self._index,
            st.session_state.file_list_state
        )
        st.session_state.group_list_state = group_list_state
        
        # Display as editable dataframe
        edited_group_df = st.data_editor(
            group_list_df,
            hide_index=True,
            disabled=["id", "name", "files", "date_created"],
            use_container_width=True,
            key="group_data_editor"
        )
        
        # Selection handling
        if st.session_state.get('group_data_editor', {}).get('edited_rows'):
            selected_row = list(st.session_state.group_data_editor['edited_rows'].keys())[0]
            self.handle_group_selection(selected_row)
        
        # Group management buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Add Group"):
                st.session_state.show_group_form = True
                st.session_state.editing_group_id = None
                st.rerun()
        
        # Group form
        if st.session_state.get('show_group_form'):
            self.render_group_form()

    def render_group_form(self):
        """Render form for adding/editing groups"""
        st.markdown("### Group Information")
        
        group_name = st.text_input(
            "Group name",
            value=st.session_state.get('editing_group_name', ''),
            key="group_name_input"
        )
        
        file_options = [(item["name"], item["id"]) for item in st.session_state.file_list_state]
        selected_files = st.multiselect(
            "Attached files",
            options=file_options,
            default=st.session_state.get('editing_group_files', []),
            format_func=lambda x: x[0],
            key="group_files_select"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save", type="primary"):
                self.save_group(
                    st.session_state.get('editing_group_id'),
                    group_name,
                    [f[1] for f in selected_files],
                    st.session_state.get('user_id')
                )
                st.session_state.show_group_form = False
                st.rerun()
        
        with col2:
            if st.button("Cancel"):
                st.session_state.show_group_form = False
                st.rerun()

    def format_size_human_readable(self,size, suffix="B"):
        """Simple helper to format sizes in a human-readable way."""
        if size == "-" or size is None:
            return "-"
        size = int(size)
        for unit in ["", "K", "M", "G", "T", "P"]:
            if abs(size) < 1024.0:
                return f"{size:3.1f}{unit}{suffix}"
            size /= 1024.0
        return f"{size:.1f}P{suffix}"
    
    def list_file(self,user_id, name_pattern=""):
        if user_id is None:
            # not signed in
            print("NO User")
            return [], pd.DataFrame.from_records(
                [
                    {
                        "id": "-",
                        "name": "-",
                        "size": "-",
                        "tokens": "-",
                        "loader": "-",
                        "date_created": "-",
                    }
                ]
            )

        Source = self._index._resources["Source"]
        with Session(engine) as session:
            statement = select(Source)
            if self._index.config.get("private", False):
                statement = statement.where(Source.user == user_id)
            if name_pattern:
                statement = statement.where(Source.name.ilike(f"%{name_pattern}%"))
            
            results = [
                {
                    "id": each[0].id,
                    "name": each[0].name,
                    "size": self.format_size_human_readable(each[0].size),
                    "tokens": self.format_size_human_readable(
                        each[0].note.get("tokens", "-"), suffix=""
                    ),
                    "loader": each[0].note.get("loader", "-"),
                    "date_created": each[0].date_created.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for each in session.execute(statement).all()
            ]

        if results:
            file_list_df = pd.DataFrame.from_records(results)
        else:
            file_list_df = pd.DataFrame.from_records(
                [
                    {
                        "id": "-",
                        "name": "-",
                        "size": "-",
                        "tokens": "-",
                        "loader": "-",
                        "date_created": "-",
                    }
                ]
            )

        return results, file_list_df
    

    MAX_FILENAME_LENGTH = 10  # or whatever value you have in your constants/settings

    def list_group(self,user_id, index, file_list):
        # supply file_list to display the file names in the group
        if file_list:
            file_id_to_name = {item["id"]: item["name"] for item in file_list}
        else:
            file_id_to_name = {}

        if user_id is None:
            # not signed in
            return [], pd.DataFrame.from_records(
                [
                    {
                        "id": "-",
                        "name": "-",
                        "files": "-",
                        "date_created": "-",
                    }
                ]
            )

        FileGroup = self._index._resources["FileGroup"]
        with Session(engine) as session:
            statement = select(FileGroup)
            if self._index.config.get("private", False):
                statement = statement.where(FileGroup.user == user_id)

            results = [
                {
                    "id": each[0].id,
                    "name": each[0].name,
                    "files": each[0].data.get("files", []),
                    "date_created": each[0].date_created.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for each in session.execute(statement).all()
            ]

        if results:
            formatted_results = deepcopy(results)
            for item in formatted_results:
                file_names = [
                    file_id_to_name.get(file_id, "-") for file_id in item["files"]
                ]
                # Format nicely
                item["files"] = ", ".join(
                    f"'{it[:MAX_FILENAME_LENGTH]}..'" if len(it) > MAX_FILENAME_LENGTH else f"'{it}'"
                    for it in file_names
                )
                item_count = len(file_names)
                item_postfix = "s" if item_count > 1 else ""
                item["files"] = f"[{item_count} item{item_postfix}] " + item["files"]

            group_list_df = pd.DataFrame.from_records(formatted_results)
        else:
            group_list_df = pd.DataFrame.from_records(
                [
                    {
                        "id": "-",
                        "name": "-",
                        "files": "-",
                        "date_created": "-",
                    }
                ]
            )

        return results, group_list_df

    
    # Original methods from FileIndexPage implemented below
    # (list_file, list_group, delete_event, download_single_file, etc.)
    # These would be copied from the original with minimal changes
    
    def handle_upload(self):
        """Handle file upload and indexing"""
        if self.urls:
            files = [it.strip() for it in self.urls.split("\n") if it.strip()]
            errors = []
        else:
            if not self.files:
                st.warning("No files uploaded")
                return

            # Save uploaded files to temp directory
            temp_dir = tempfile.mkdtemp()
            file_paths = []
            for uploaded_file in self.files:
                file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                file_paths.append(file_path)

            files = self._may_extract_zip(file_paths, flowsettings.KH_ZIP_INPUT_DIR)
            errors = self.validate(files)
            if errors:
                for error in errors:
                    st.error(error)
                return

        st.info(f"Start indexing {len(files)} files...")
        
        # Implement indexing logic
        # This would call the appropriate methods from the original index_fn
        # and display progress/results

    def handle_file_selection(self, row_index):
        """Handle file selection from the dataframe"""
        file_list = st.session_state.file_list_state
        if row_index >= len(file_list):
            return
            
        selected_file = file_list[row_index]
        st.session_state.selected_file_id = selected_file["id"]
        st.session_state.selected_file_name = selected_file["name"]

    def handle_group_selection(self, row_index):
        """Handle group selection from the dataframe"""
        group_list = st.session_state.group_list_state
        if row_index >= len(group_list):
            return
            
        selected_group = group_list[row_index]
        st.session_state.selected_group_id = selected_group["id"]
        st.session_state.editing_group_id = selected_group["id"]
        st.session_state.editing_group_name = selected_group["name"]
        st.session_state.editing_group_files = selected_group["files"]
        st.session_state.show_group_form = True

    def get_selected_file_name(self):
        """Get name of currently selected file"""
        if not st.session_state.selected_file_id:
            return None
            
        for file in st.session_state.file_list_state:
            if file["id"] == st.session_state.selected_file_id:
                return file["name"]
        return None

    # Implement all the original methods from FileIndexPage here
    # (list_file, list_group, delete_event, download_single_file, etc.)
    # These would be nearly identical to the original implementations,
    # just adapted to work with Streamlit's session state instead of Gradio's state

class FileSelectorUI:
    """Streamlit implementation of FileSelector"""
    
    def __init__(self, index):
        self._index = index
        
    def render(self):
        """Render the file selector UI"""
        st.sidebar.subheader("File Selection")
        
        mode = st.sidebar.radio(
            "Search Mode",
            options=["Search All", "Search In File(s)"],
            index=0 if st.session_state.get('search_mode', 'all') == 'all' else 1,
            key="search_mode_radio"
        )
        
        if mode == "Search In File(s)":
            self.render_file_selector()
    
    def render_file_selector(self):
        """Render the file selector dropdown"""
        options = self.get_file_options()
        
        selected = st.sidebar.multiselect(
            "Select files to search",
            options=options,
            format_func=lambda x: x[0],
            key="file_selector"
        )
        
        # Store selected file IDs in session state
        st.session_state.selected_file_ids = [x[1] for x in selected]
    
    def get_file_options(self) -> List[Tuple[str, str]]:
        """Get list of available files and groups"""
        options = []
        
        # Get files from Source table
        with Session(engine) as session:
            statement = select(self._index._resources["Source"])
            if self._index.config.get("private", False):
                statement = statement.where(
                    self._index._resources["Source"].user == st.session_state.get('user_id')
                )

            if KH_DEMO_MODE:
                statement = statement.limit(MAX_FILE_COUNT)

            results = session.execute(statement).all()
            for result in results:
                options.append((result[0].name, result[0].id))

            # Get groups from FileGroup table
            FileGroup = self._index._resources["FileGroup"]
            statement = select(FileGroup)
            if self._index.config.get("private", False):
                statement = statement.where(
                    FileGroup.user == st.session_state.get('user_id')
                )
            results = session.execute(statement).all()
            for result in results:
                item = result[0]
                options.append(
                    (f"group: '{item.name}'", json.dumps(item.data.get("files", [])))
                )

        return options

    def get_selected_ids(self) -> List[str]:
        """Get IDs of selected files/groups"""
        mode = st.session_state.get('search_mode', 'all')
        if mode == 'all' or not hasattr(st.session_state, 'selected_file_ids'):
            return self.get_all_file_ids()
        return st.session_state.selected_file_ids
    
    def get_all_file_ids(self) -> List[str]:
        """Get IDs of all available files"""
        file_ids = []
        with Session(engine) as session:
            statement = select(self._index._resources["Source"].id)
            if self._index.config.get("private", False):
                statement = statement.where(
                    self._index._resources["Source"].user == st.session_state.get('user_id')
                )
            results = session.execute(statement).all()
            for (id,) in results:
                file_ids.append(id)
        return file_ids