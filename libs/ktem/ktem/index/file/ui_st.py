import html
import json
import os
import shutil
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path
from typing import Generator, List, Tuple, Optional, Dict

import streamlit as st
import pandas as pd
import yaml
from ktem.app import BasePage
from ktem.db.engine import engine
from ktem.utils.render import Render
from sqlalchemy import select
from sqlalchemy.orm import Session
from theflow.settings import settings as flowsettings
from theflow.utils.modules import deserialize

KH_DEMO_MODE = getattr(flowsettings, "KH_DEMO_MODE", False)
KH_SSO_ENABLED = getattr(flowsettings, "KH_SSO_ENABLED", False)
MAX_FILENAME_LENGTH = 20
MAX_FILE_COUNT = 200

class DirectoryUpload(BasePage):
    def __init__(self, app, index):
        self._app = app
        self._index = index
        self._supported_file_types_str = self._index.config.get("supported_file_types", "")
        self._supported_file_types = [each.strip() for each in self._supported_file_types_str.split(",")]
        self.on_building_ui()

    def on_building_ui(self):
        with st.expander("Directory Upload"):
            st.markdown(f"Supported file types: {self._supported_file_types_str}")
            path = st.text_input("Directory path", placeholder="Enter directory path...")
            
            with st.expander("Advanced indexing options"):
                reindex = st.checkbox("Force reindex file")
            
            if st.button("Upload and Index"):
                self._handle_directory_upload(path, reindex)

    def _handle_directory_upload(self, path, reindex):
        if not path:
            st.warning("Please enter a directory path")
            return
            
        if not os.path.isdir(path):
            st.error("Invalid directory path")
            return
            
        with st.status("Indexing directory..."):
            try:
                files = self._get_files_from_dir(path)
                if not files:
                    st.warning("No supported files found in directory")
                    return
                    
                indexing_pipeline = self._index.get_indexing_pipeline(
                    st.session_state.settings, 
                    self._app.user_id
                )
                
                output_stream = indexing_pipeline.stream(files, reindex=reindex)
                while True:
                    response = next(output_stream)
                    if response is None:
                        continue
                    if response.channel == "index":
                        status = "✅" if response.content["status"] == "success" else "❌"
                        st.write(f"{status} {response.content['file_name']}")
            except StopIteration:
                st.success("Directory indexing completed")
            except Exception as e:
                st.error(f"Error indexing directory: {str(e)}")

    def _get_files_from_dir(self, folder_path):
        """Get supported files from directory"""
        files = []
        for root, _, filenames in os.walk(folder_path):
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in self._supported_file_types:
                    files.append(os.path.join(root, filename))
        return files

class FileIndexPage(BasePage):
    def __init__(self, app, index):
        super().__init__(app)
        self._index = index
        self._supported_file_types_str = self._index.config.get("supported_file_types", "")
        self._supported_file_types = [each.strip() for each in self._supported_file_types_str.split(",")]
        self._selected_file_id = None
        self._selected_group_id = None
        self._delete_confirm = False
        self._group_delete_confirm = False
        self._show_group_form = False
        
        if not KH_DEMO_MODE:
            self.on_building_ui()

    def upload_instruction(self) -> str:
        msgs = []
        if self._supported_file_types:
            msgs.append(f"- Supported file types: {self._supported_file_types_str}")
        if max_file_size := self._index.config.get("max_file_size", 0):
            msgs.append(f"- Maximum file size: {max_file_size} MB")
        if max_number_of_files := self._index.config.get("max_number_of_files", 0):
            msgs.append(f"- Maximum files: {max_number_of_files}")
        return "\n".join(msgs) if msgs else ""

    def on_building_ui(self):
        """Build the Streamlit UI for file indexing"""
        tab1, tab2 = st.tabs(["Files", "Groups"])
        
        with tab1:
            self._render_file_tab()
            
        with tab2:
            self._render_group_tab()

    def _render_file_tab(self):
        """Render the file management tab"""
        with st.expander("Upload Files", expanded=True):
            uploaded_files = st.file_uploader(
                "Choose files",
                type=self._supported_file_types,
                accept_multiple_files=True,
                help=self.upload_instruction()
            )
            
            urls = st.text_area(
                "Or enter web URLs (one per line)",
                height=100
            )
            
            reindex = st.checkbox("Force reindex files")
            
            if st.button("Upload and Index"):
                self._handle_upload(uploaded_files, urls, reindex)

        self._render_file_list()
        
        if self._selected_file_id:
            self._render_file_details()

    def _render_file_list(self):
        """Render the file list table"""
        files_df = self._get_files_df()
        
        if files_df.empty or files_df.iloc[0]["id"] == "-":
            st.warning("No files available")
            return
            
        st.dataframe(
            files_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": None,
                "name": "Name",
                "size": "Size",
                "tokens": "Tokens",
                "loader": "Loader",
                "date_created": "Created"
            }
        )
        
        # File selection
        file_options = [""] + files_df["name"].tolist()
        selected_file = st.selectbox(
            "Select a file to view details",
            options=file_options,
            key="selected_file"
        )
        
        if selected_file:
            self._selected_file_id = files_df[files_df["name"] == selected_file]["id"].values[0]

    def _render_file_details(self):
        """Render details for a selected file"""
        st.subheader("File Details")
        
        with st.status("Loading file chunks..."):
            chunks_html = self._get_file_chunks(self._selected_file_id)
        
        if chunks_html:
            st.components.v1.html(chunks_html, height=600, scrolling=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Chat with File"):
                self._navigate_to_chat(self._selected_file_id)
        with col2:
            if st.button("Download"):
                self._download_file(self._selected_file_id)
        with col3:
            if st.button("Delete", type="primary"):
                self._delete_confirm = True
                
        if self._delete_confirm:
            st.warning("Are you sure you want to delete this file?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Confirm Delete"):
                    self._delete_file(self._selected_file_id)
                    self._delete_confirm = False
                    st.rerun()
            with col2:
                if st.button("Cancel"):
                    self._delete_confirm = False

    def _render_group_tab(self):
        """Render the group management tab"""
        if st.button("Create New Group"):
            self._show_group_form = True
            
        if self._show_group_form:
            self._render_group_edit_form()
        
        groups_df = self._get_groups_df()
        
        if groups_df.empty or groups_df.iloc[0]["id"] == "-":
            st.warning("No groups available")
        else:
            st.dataframe(
                groups_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": None,
                    "name": "Name",
                    "files": "Files",
                    "date_created": "Created"
                }
            )
        
            # Group selection
            group_options = [""] + groups_df["name"].tolist()
            selected_group = st.selectbox(
                "Select a group to view/edit",
                options=group_options,
                key="selected_group"
            )
            
            if selected_group:
                self._render_group_details(selected_group, groups_df)

    def _render_group_details(self, group_name, groups_df):
        """Render details for a selected group"""
        group_info = groups_df[groups_df["name"] == group_name].iloc[0]
        
        st.subheader("Group Details")
        st.write(f"**Name:** {group_info['name']}")
        st.write(f"**Created:** {group_info['date_created']}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Chat with Group"):
                self._navigate_to_chat_with_group(group_info['id'])
        with col2:
            if st.button("Edit Group"):
                self._show_group_form = True
                self._selected_group_id = group_info['id']
                st.rerun()
        with col3:
            if st.button("Delete Group", type="primary"):
                self._group_delete_confirm = True
                
        if self._group_delete_confirm:
            st.warning("Are you sure you want to delete this group?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Confirm Delete"):
                    self._delete_group(group_info['id'])
                    self._group_delete_confirm = False
                    st.rerun()
            with col2:
                if st.button("Cancel"):
                    self._group_delete_confirm = False

    def _render_group_edit_form(self, group_id=None):
        """Render form for editing/creating groups"""
        files_df = self._get_files_df()
        file_options = [(row["name"], row["id"]) for _, row in files_df.iterrows() if row["id"] != "-"]
        
        with st.form("group_form"):
            # Load existing group data if editing
            if group_id:
                FileGroup = self._index._resources["FileGroup"]
                with Session(engine) as session:
                    group = session.query(FileGroup).filter_by(id=group_id).first()
                    default_name = group.name if group else ""
                    default_files = group.data.get("files", []) if group else []
            else:
                default_name = ""
                default_files = []
            
            name = st.text_input("Group Name", value=default_name)
            files = st.multiselect(
                "Select Files",
                options=file_options,
                format_func=lambda x: x[0],
                default=[f for f in file_options if f[1] in default_files]
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Save Group"):
                    try:
                        self._save_group(group_id, name, [f[1] for f in files])
                        st.success("Group saved successfully")
                        self._show_group_form = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving group: {str(e)}")
            with col2:
                if st.form_submit_button("Cancel"):
                    self._show_group_form = False
                    st.rerun()

    def _get_files_df(self):
        """Get files as DataFrame"""
        if not hasattr(self._app, 'user_id') or not self._app.user_id:
            return pd.DataFrame([{
                "id": "-", "name": "-", "size": "-", 
                "tokens": "-", "loader": "-", "date_created": "-"
            }])
            
        Source = self._index._resources["Source"]
        with Session(engine) as session:
            statement = select(Source)
            if self._index.config.get("private", False):
                statement = statement.where(Source.user == self._app.user_id)
                
            results = [
                {
                    "id": each[0].id,
                    "name": each[0].name,
                    "size": self._format_size(each[0].size),
                    "tokens": self._format_size(each[0].note.get("tokens", "-"), suffix=""),
                    "loader": each[0].note.get("loader", "-"),
                    "date_created": each[0].date_created.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for each in session.execute(statement).all()
            ]
            
        return pd.DataFrame(results if results else [{
            "id": "-", "name": "-", "size": "-", 
            "tokens": "-", "loader": "-", "date_created": "-"
        }])

    def _get_groups_df(self):
        """Get groups as DataFrame"""
        files_df = self._get_files_df()
        file_id_to_name = {row["id"]: row["name"] for _, row in files_df.iterrows()}
        
        if not hasattr(self._app, 'user_id') or not self._app.user_id:
            return pd.DataFrame([{
                "id": "-", "name": "-", "files": "-", "date_created": "-"
            }])
            
        FileGroup = self._index._resources["FileGroup"]
        with Session(engine) as session:
            statement = select(FileGroup)
            if self._index.config.get("private", False):
                statement = statement.where(FileGroup.user == self._app.user_id)
                
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
            for item in results:
                file_names = [file_id_to_name.get(fid, "-") for fid in item["files"]]
                item["files"] = ", ".join(
                    f"'{it[:MAX_FILENAME_LENGTH]}..'"
                    if len(it) > MAX_FILENAME_LENGTH else f"'{it}'"
                    for it in file_names
                )
            return pd.DataFrame(results)
        return pd.DataFrame([{
            "id": "-", "name": "-", "files": "-", "date_created": "-"
        }])

    def _format_size(self, num: float | str, suffix="B"):
        """Format size for human readability"""
        try:
            num = float(num)
        except ValueError:
            return num

        for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
            if abs(num) < 1024.0:
                return f"{num:3.0f}{unit}{suffix}"
            num /= 1024.0
        return f"{num:.0f}Yi{suffix}"

    def _get_file_chunks(self, file_id):
        """Get HTML chunks for a file"""
        if not file_id:
            return ""
            
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
            docs = sorted(docs, key=lambda x: x.metadata.get("page_label", float("inf")))
            
            for idx, doc in enumerate(docs):
                title = html.escape(f"{doc.text[:50]}..." if len(doc.text) > 50 else doc.text)
                doc_type = doc.metadata.get("type", "text")
                content = ""
                if doc_type == "text":
                    content = html.escape(doc.text)
                elif doc_type == "table":
                    content = Render.table(doc.text)
                elif doc_type == "image":
                    content = Render.image(
                        url=doc.metadata.get("image_origin", ""), text=doc.text
                    )

                header_prefix = f"[{idx+1}/{len(docs)}]"
                if doc.metadata.get("page_label"):
                    header_prefix += f" [Page {doc.metadata['page_label']}]"

                chunks.append(
                    Render.collapsible(
                        header=f"{header_prefix} {title}",
                        content=content,
                    )
                )
        return "".join(chunks)

    def _handle_upload(self, uploaded_files, urls, reindex):
        """Handle file upload"""
        if not uploaded_files and not urls:
            st.warning("No files or URLs provided")
            return
            
        with st.status("Indexing files..."):
            if urls:
                files = [url.strip() for url in urls.split("\n") if url.strip()]
                errors = []
            else:
                # Handle file uploads
                files = []
                errors = []
                for uploaded_file in uploaded_files:
                    # Save uploaded file to temp location
                    temp_dir = tempfile.mkdtemp()
                    file_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    files.append(file_path)
                
            if errors:
                st.warning(", ".join(errors))
                return
                
            # Get the pipeline
            indexing_pipeline = self._index.get_indexing_pipeline(
                st.session_state.settings, 
                self._app.user_id
            )
            
            # Process files
            output_stream = indexing_pipeline.stream(files, reindex=reindex)
            try:
                while True:
                    response = next(output_stream)
                    if response is None:
                        continue
                    if response.channel == "index":
                        status = "✅" if response.content["status"] == "success" else "❌"
                        st.write(f"{status} {response.content['file_name']}")
            except StopIteration:
                st.success("Indexing completed")
                st.rerun()
            except Exception as e:
                st.error(f"Error during indexing: {str(e)}")

    def _navigate_to_chat(self, file_id):
        """Navigate to chat with file"""
        st.session_state.selected_file_id = file_id
        st.session_state.current_tab = "Chat"
        st.rerun()

    def _navigate_to_chat_with_group(self, group_id):
        """Navigate to chat with group"""
        st.session_state.selected_group_id = group_id
        st.session_state.current_tab = "Chat"
        st.rerun()

    def _download_file(self, file_id):
        """Handle file download"""
        with Session(engine) as session:
            source = session.execute(
                select(self._index._resources["Source"]).where(
                    self._index._resources["Source"].id == file_id
                )
            ).first()
            
        if source:
            # In a real implementation, you would need to get the actual file content
            # This is a simplified version
            st.download_button(
                label="Download File",
                data="File content would be here",  # Replace with actual file content
                file_name=source[0].name,
                mime="application/octet-stream"
            )

    def _delete_file(self, file_id):
        """Delete a file"""
        with Session(engine) as session:
            source = session.execute(
                select(self._index._resources["Source"]).where(
                    self._index._resources["Source"].id == file_id
                )
            ).first()
            if source:
                file_name = source[0].name
                session.delete(source[0])

            vs_ids, ds_ids = [], []
            index = session.execute(
                select(self._index._resources["Index"]).where(
                    self._index._resources["Index"].source_id == file_id
                )
            ).all()
            for each in index:
                if each[0].relation_type == "vector":
                    vs_ids.append(each[0].target_id)
                elif each[0].relation_type == "document":
                    ds_ids.append(each[0].target_id)
                session.delete(each[0])
            session.commit()

        if vs_ids:
            self._index._vs.delete(vs_ids)
        self._index._docstore.delete(ds_ids)
        st.success(f"File {file_name} has been deleted")

    def _save_group(self, group_id, name, files):
        """Save a group"""
        FileGroup = self._index._resources["FileGroup"]
        
        with Session(engine) as session:
            if group_id:
                group = session.query(FileGroup).filter_by(id=group_id).first()
                group.name = name
                group.data["files"] = files
            else:
                # Check if group exists
                existing = session.query(FileGroup).filter_by(
                    name=name,
                    user=self._app.user_id,
                ).first()
                if existing:
                    raise Exception(f"Group {name} already exists")
                    
                group = FileGroup(
                    name=name,
                    data={"files": files},
                    user=self._app.user_id,
                )
                session.add(group)
            session.commit()

    def _delete_group(self, group_id):
        """Delete a group"""
        FileGroup = self._index._resources["FileGroup"]
        with Session(engine) as session:
            group = session.execute(
                select(FileGroup).where(FileGroup.id == group_id)
            ).first()
            if group:
                session.delete(group[0])
                session.commit()
                st.success(f"Group {group[0].name} deleted")
            else:
                st.error("Group not found")

class FileSelector(BasePage):
    """File selector UI in the Chat page"""
    
    def __init__(self, app, index):
        super().__init__(app)
        self._index = index
        self.on_building_ui()

    def default(self):
        if self._app.f_user_management:
            return "disabled", [], -1
        return "disabled", [], 1

    def on_building_ui(self):
        """Render the file selector UI"""
        st.radio(
            "Search Mode",
            options=[("Search All", "all"), ("Search In File(s)", "select")],
            key="search_mode",
            horizontal=True
        )
        
        if st.session_state.search_mode == "select":
            files_df = self._get_files_df()
            file_options = [(row["name"], row["id"]) for _, row in files_df.iterrows() if row["id"] != "-"]
            st.multiselect(
                "Select Files",
                options=file_options,
                format_func=lambda x: x[0],
                key="selected_files"
            )

    def _get_files_df(self):
        """Get files as DataFrame"""
        if not hasattr(self._app, 'user_id') or not self._app.user_id:
            return pd.DataFrame([{"id": "-", "name": "-"}])
            
        Source = self._index._resources["Source"]
        with Session(engine) as session:
            statement = select(Source)
            if self._index.config.get("private", False):
                statement = statement.where(Source.user == self._app.user_id)
                
            results = [
                {"id": each[0].id, "name": each[0].name}
                for each in session.execute(statement).all()
            ]
            
        return pd.DataFrame(results if results else [{"id": "-", "name": "-"}])

    def get_selected_ids(self):
        """Get selected file IDs based on current selection"""
        if st.session_state.search_mode == "disabled":
            return []
        elif st.session_state.search_mode == "select":
            return [f[1] for f in st.session_state.selected_files]
        else:  # "all" mode
            files_df = self._get_files_df()
            return [row["id"] for _, row in files_df.iterrows() if row["id"] != "-"]