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
        st.error(f"Failed to fetch document from {url}: {e}")
        return ""


def download_changelogs(release_url: str) -> str:
    try:
        res = requests.get(release_url).json()
        changelogs = res.get("body", "")
        return changelogs
    except Exception as e:
        st.error(f"Failed to fetch changelogs from {release_url}: {e}")
        return ""


class HelpPage:
    def __init__(
        self,
        app,
        doc_dir: str = settings.KH_DOC_DIR,
        remote_content_url: str = "https://raw.githubusercontent.com/Cinnamon/kotaemon",
        app_version: str | None = settings.KH_APP_VERSION,
        changelogs_cache_dir: str | Path = Path(settings.KH_APP_DATA_DIR) / "changelogs",
    ):
        self.app = app
        self.doc_dir = Path(doc_dir)
        self.remote_content_url = remote_content_url
        self.app_version = app_version
        self.changelogs_cache_dir = Path(changelogs_cache_dir)
        self.changelogs_cache_dir.mkdir(parents=True, exist_ok=True)

    def render(self):
        """Render the Help Page UI using Streamlit."""

        st.title("Help & Documentation")

        # About Section
        about_md = ""
        about_md_path = self.doc_dir / "about.md"
        if about_md_path.exists():
            with about_md_path.open(encoding="utf-8") as fi:
                about_md = fi.read()
        else:
            about_md = get_remote_doc(
                f"{self.remote_content_url}/v{self.app_version}/docs/about.md"
            )

        if about_md:
            with st.expander("About"):
                if self.app_version:
                    st.markdown(f"**Version:** {self.app_version}\n\n{about_md}")
                else:
                    st.markdown(about_md)

        # Demo Mode Info
        if KH_DEMO_MODE:
            with st.expander("Create Your Own Space"):
                st.markdown(
                    "This is a demo with limited functionality. "
                    "Use the button below to install Kotaemon "
                    "in your own space with all features "
                    "(including uploading and managing your private "
                    "documents securely)."
                )
                st.markdown(f"[Create Your Own Space]({HF_SPACE_URL})", unsafe_allow_html=True)

        # User Guide Section
        user_guide_md = ""
        user_guide_md_path = self.doc_dir / "usage.md"
        if user_guide_md_path.exists():
            with user_guide_md_path.open(encoding="utf-8") as fi:
                user_guide_md = fi.read()
        else:
            user_guide_md = get_remote_doc(
                f"{self.remote_content_url}/v{self.app_version}/docs/usage.md"
            )

        if user_guide_md:
            with st.expander("User Guide"):
                st.markdown(user_guide_md)

        # Changelog Section
        if self.app_version:
            changelogs = ""
            changelog_file = self.changelogs_cache_dir / f"{self.app_version}.md"

            if changelog_file.exists():
                with changelog_file.open("r") as fi:
                    changelogs = fi.read()
            else:
                release_url_base = "https://api.github.com/repos/Cinnamon/kotaemon/releases"
                changelogs = download_changelogs(
                    f"{release_url_base}/tags/v{self.app_version}"
                )
                with changelog_file.open("w") as fi:
                    fi.write(changelogs)

            if changelogs:
                with st.expander(f"Changelogs (v{self.app_version})"):
                    st.markdown(changelogs)


# Example usage
if __name__ == "__main__":
    help_page = HelpPage()
    help_page.render()
