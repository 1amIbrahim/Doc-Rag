import streamlit as st
import requests
from pathlib import Path
from decouple import config
from theflow.settings import settings

KH_DEMO_MODE = getattr(settings, "KH_DEMO_MODE", False)
HF_SPACE_URL = config("HF_SPACE_URL", default="")


def get_remote_doc(url: str) -> str:
    try:
        res = requests.get(url)
        res.raise_for_status()
        return res.text
    except Exception as e:
        st.warning(f"⚠️ Failed to fetch document from {url}: {e}")
        return ""


def download_changelogs(release_url: str) -> str:
    try:
        res = requests.get(release_url).json()
        return res.get("body", "")
    except Exception as e:
        st.warning(f"⚠️ Failed to fetch changelogs: {e}")
        return ""


class HelpPage:
    def __init__(
        self,
        app,
        doc_dir: str = settings.KH_DOC_DIR,
        remote_content_url: str = "https://raw.githubusercontent.com/Cinnamon/kotaemon",
        app_version: str | None = settings.KH_APP_VERSION,
        changelogs_cache_dir: str | Path = (Path(settings.KH_APP_DATA_DIR) / "changelogs"),
    ):
        self._app = app
        self.doc_dir = Path(doc_dir)
        self.remote_content_url = remote_content_url
        self.app_version = app_version
        self.changelogs_cache_dir = Path(changelogs_cache_dir)
        self.changelogs_cache_dir.mkdir(parents=True, exist_ok=True)

    def render(self):
        # About section
        about_md_path = self.doc_dir / "about.md"
        if about_md_path.exists():
            about_md = about_md_path.read_text(encoding="utf-8")
        else:
            about_md = get_remote_doc(f"{self.remote_content_url}/v{self.app_version}/docs/about.md")
        if about_md:
            with st.expander("About", expanded=True):
                if self.app_version:
                    about_md = f"Version: {self.app_version}\n\n{about_md}"
                st.markdown(about_md)

        # Demo mode banner
        if KH_DEMO_MODE:
            with st.expander("Create Your Own Space"):
                st.markdown(
                    "This is a demo with limited functionality. "
                    "Use **Create space** button to install Kotaemon "
                    "in your own space with all features "
                    "(including upload and manage your private "
                    "documents securely)."
                )
                st.link_button("Create Your Own Space", HF_SPACE_URL)

        # User Guide
        usage_md_path = self.doc_dir / "usage.md"
        if usage_md_path.exists():
            user_guide_md = usage_md_path.read_text(encoding="utf-8")
        else:
            user_guide_md = get_remote_doc(f"{self.remote_content_url}/v{self.app_version}/docs/usage.md")
        if user_guide_md:
            with st.expander("User Guide", expanded=not KH_DEMO_MODE):
                st.markdown(user_guide_md)

        # Changelogs
        if self.app_version:
            changelogs = ""
            cache_path = self.changelogs_cache_dir / f"{self.app_version}.md"
            if cache_path.exists():
                changelogs = cache_path.read_text()
            else:
                release_url = f"https://api.github.com/repos/Cinnamon/kotaemon/releases/tags/v{self.app_version}"
                changelogs = download_changelogs(release_url)
                if changelogs:
                    cache_path.write_text(changelogs)
            if changelogs:
                with st.expander(f"Changelogs (v{self.app_version})"):
                    st.markdown(changelogs)
