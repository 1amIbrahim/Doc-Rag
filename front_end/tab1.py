import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import numpy as np

# Set page configuration
st.set_page_config(page_title="File Collection", layout="wide")

# --- Enhanced Custom Dark Theme CSS ---
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #f1f1f1;
    }
    .upload-box, .rag-container {
        background: linear-gradient(135deg, #1a1a1a 0%, #222222 100%);
        border-radius: 15px;
        padding: 2rem;
        border: 1px solid #333;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }
    .upload-box:hover, .rag-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.4);
        border-color: #555;
    }
    .custom-caption {
        font-size: 0.9rem;
        color: #aaaaaa;
        line-height: 1.5;
    }
    .dataframe-container {
        background-color: #1a1a1a;
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid #333;
    }
    .stDataFrame th {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
        border-bottom: 2px solid #4CAF50 !important;
    }
    .stDataFrame td {
        color: #e0e0e0 !important;
        border-bottom: 1px solid #333 !important;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #45a049;
        transform: translateY(-1px);
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1.1rem;
        padding: 0.75rem 1.5rem;
        color: #aaaaaa;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #4CAF50;
        border-bottom: 2px solid #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# --- Initialize Session State ---
if 'files_df' not in st.session_state:
    st.session_state.files_df = pd.DataFrame({
        "name": ["Assembly Lang Programming by Sir Belal Hashmi"],
        "size": ["1MB"],
        "token_load": ["139K"],
        "type": ["PDF Document"],  # Changed to a more standard type
        "date_created": [datetime.datetime(2025, 3, 27, 16, 59).strftime("%Y-%m-%d %H:%M:%S")]
    })

# --- Page Header with Icon ---
st.markdown("""
    <div style='display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem;'>
        <span style='font-size: 2.5rem;'>📂</span>
        <h1 style='margin: 0; color: #ffffff;'>File Collection</h1>
    </div>
""", unsafe_allow_html=True)

# --- Tabs ---
tabs = st.tabs(["📤 Upload Files", "📊 GraphRAG Collection", "✨ LightRAG Collection"])

# --- Upload Files Tab ---
with tabs[0]:
    col1, col2 = st.columns([1, 2], gap="large")

    with col1:
        st.markdown('<div class="upload-box">', unsafe_allow_html=True)
        st.subheader("Upload Your Files", anchor=False)

        uploaded_file = st.file_uploader(
            "",
            label_visibility="collapsed",
            type=["png", "jpg", "jpeg", "tiff", "pdf", "xls", "xlsx", "doc",
                  "docx", "pptx", "csv", "html", "mhtml", "txt", "zip"],
            accept_multiple_files=True
        )

        st.markdown("""
        <div class="custom-caption">
            📁 Supported formats: Images (PNG, JPG, TIFF), Documents (PDF, DOC, XLS, PPTX), 
            Data (CSV), Web (HTML, MHTML), Text (TXT), Archives (ZIP)<br>
            📦 Max file size: 1000 MB | Multiple files supported
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("⚙️ Advanced Indexing Options", expanded=False):
            chunk_size = st.slider("Chunk Size (KB)", 100, 1000, 500)
            enable_ocr = st.checkbox("Enable OCR for Images/PDFs")
            compression_level = st.select_slider(
                "Compression Level",
                options=["Low", "Medium", "High"],
                value="Medium"
            )

        # MIME type to user-friendly type mapping
        mime_to_type = {
            "image/png": "PNG Image",
            "image/jpeg": "JPEG Image",
            "image/tiff": "TIFF Image",
            "application/pdf": "PDF Document",
            "application/vnd.ms-excel": "Excel Spreadsheet",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Excel Spreadsheet",
            "application/msword": "Word Document",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Word Document",
            "application/vnd.ms-powerpoint": "PowerPoint Presentation",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": "PowerPoint Presentation",
            "text/csv": "CSV File",
            "text/html": "HTML File",
            "text/plain": "Text File",
            "application/zip": "ZIP Archive",
            "multipart/related": "MHTML File"  # Added for .mhtml
        }

        if st.button("📤 Upload and Index", use_container_width=True):
            if uploaded_file:
                for file in uploaded_file:
                    if file.size > 1000 * 1024 * 1024:  # 1000 MB limit
                        st.error(f"File {file.name} exceeds the maximum size of 1000 MB.")
                        continue
                    file_type = mime_to_type.get(file.type, "Unknown Type")
                    token_load = int(file.size / 1000)  # Simple token estimation
                    new_file = {
                        "name": [file.name],
                        "size": [f"{round(file.size / 1024 / 1024, 2)}MB"],
                        "token_load": [f"{token_load}K"],
                        "type": [file_type],
                        "date_created": [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                    }
                    st.session_state.files_df = pd.concat(
                        [st.session_state.files_df, pd.DataFrame(new_file)],
                        ignore_index=True
                    )
                st.success("Files uploaded successfully!")
                st.rerun()
            else:
                st.warning("No files selected for upload.")

    with col2:
        st.subheader("File Library", anchor=False)

        filter_text = st.text_input(
            "Filter by name:",
            placeholder="Case-insensitive search...",
            label_visibility="collapsed"
        )

        display_df = st.session_state.files_df.copy()
        if filter_text:
            display_df = display_df[
                display_df["name"].str.contains(filter_text, case=False, na=False)
            ]

        st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "name": st.column_config.TextColumn("File Name", width="medium"),
                "size": st.column_config.TextColumn("Size", width="small"),
                "token_load": st.column_config.TextColumn("Token Load", width="small"),
                "type": st.column_config.TextColumn("Type", width="small"),
                "date_created": st.column_config.DatetimeColumn("Date Created", width="medium")
            }
        )
        st.markdown("</div>", unsafe_allow_html=True)

        selected_file = st.selectbox(
            "Selected file:",
            options=["Select a file"] + display_df["name"].tolist(),
            label_visibility="collapsed"
        )

        with st.expander("🔧 Advanced File Options", expanded=False):
            col_opt1, col_opt2 = st.columns(2)
            with col_opt1:
                if st.button("🗑️ Delete Selected", disabled=selected_file == "Select a file"):
                    if selected_file != "Select a file":
                        st.session_state.files_df = st.session_state.files_df[
                            st.session_state.files_df["name"] != selected_file
                        ]
                        st.success(f"Deleted {selected_file}")
                        st.rerun()
            with col_opt2:
                if st.button("📋 View Details", disabled=selected_file == "Select a file"):
                    if selected_file != "Select a file":
                        file_details = st.session_state.files_df[
                            st.session_state.files_df["name"] == selected_file
                        ].iloc[0]
                        st.write(f"**Name:** {file_details['name']}")
                        st.write(f"**Size:** {file_details['size']}")
                        st.write(f"**Token Load:** {file_details['token_load']}")
                        st.write(f"**Type:** {file_details['type']}")
                        st.write(f"**Date Created:** {file_details['date_created']}")

# --- GraphRAG Collection Tab ---
with tabs[1]:
    st.markdown('<div class="rag-container">', unsafe_allow_html=True)
    st.subheader("GraphRAG Collection Dashboard", anchor=False)

    col_gr1, col_gr2 = st.columns([1, 1], gap="medium")

    with col_gr1:
        st.markdown("### Collection Statistics")
        stats = {
            "Total Nodes": len(st.session_state.files_df) * 10,
            "Total Edges": len(st.session_state.files_df) * 15,
            "Average Degree": 3.5 if len(st.session_state.files_df) > 0 else 0,
            "Graph Density": 0.12 if len(st.session_state.files_df) > 0 else 0
        }
        for key, value in stats.items():
            st.metric(key, value)

        with st.expander("GraphRAG Settings"):
            st.slider("Max Node Connections", 1, 20, 5)
            st.checkbox("Enable Entity Resolution", value=True)
            st.selectbox("Embedding Model", ["BERT", "RoBERTa", "DistilBERT"], index=1)

    with col_gr2:
        st.markdown("### Knowledge Graph Visualization")
        if not st.session_state.files_df.empty:
            graph_data = pd.DataFrame({
                "Node": [f"Node_{i}" for i in range(min(10, len(st.session_state.files_df)))],
                "Connections": np.random.randint(1, 10, min(10, len(st.session_state.files_df)))
            })
            fig = px.bar(graph_data, x="Node", y="Connections",
                         title="Node Connectivity",
                         color_discrete_sequence=["#4CAF50"])
            fig.update_layout(
                paper_bgcolor="#1a1a1a",
                plot_bgcolor="#1a1a1a",
                font_color="#ffffff",
                title_font_color="#ffffff"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No files uploaded to visualize.")

    if st.button("🔄 Rebuild GraphRAG Index", use_container_width=True):
        st.success("GraphRAG index rebuilt successfully!")
    st.markdown("</div>", unsafe_allow_html=True)

# --- LightRAG Collection Tab ---
with tabs[2]:
    st.markdown('<div class="rag-container">', unsafe_allow_html=True)
    st.subheader("LightRAG Collection Dashboard", anchor=False)

    col_lr1, col_lr2 = st.columns([1, 1], gap="medium")

    with col_lr1:
        st.markdown("### Collection Overview")
        total_tokens = sum(int(t.replace('K', '')) * 1000 for t in st.session_state.files_df["token_load"] if t != "N/A")
        avg_size = sum(float(s.replace('MB', '')) for s in st.session_state.files_df["size"]) / len(st.session_state.files_df) if len(st.session_state.files_df) > 0 else 0
        overview = {
            "Total Documents": len(st.session_state.files_df),
            "Indexed Tokens": f"{total_tokens // 1000}K",
            "Avg. Doc Size": f"{avg_size:.2f}MB",
            "Last Updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        for key, value in overview.items():
            st.metric(key, value)

        with st.expander("LightRAG Settings"):
            st.slider("Retrieval Window", 100, 1000, 300)
            st.checkbox("Use Semantic Search", value=True)
            st.selectbox("Similarity Metric", ["Cosine", "Euclidean", "Manhattan"], index=0)

    with col_lr2:
        st.markdown("### Document Distribution")
        if not st.session_state.files_df.empty:
            dist_data = st.session_state.files_df["type"].value_counts().reset_index()
            dist_data.columns = ["File Type", "Count"]
            fig = px.pie(dist_data, names="File Type", values="Count",
                         title="File Type Distribution",
                         color_discrete_sequence=px.colors.sequential.Viridis)
            fig.update_layout(
                paper_bgcolor="#1a1a1a",
                plot_bgcolor="#1a1a1a",
                font_color="#ffffff",
                title_font_color="#ffffff"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No files uploaded to visualize.")

    if st.button("🔄 Rebuild LightRAG Index", use_container_width=True):
        st.success("LightRAG index rebuilt successfully!")
    st.markdown("</div>", unsafe_allow_html=True)