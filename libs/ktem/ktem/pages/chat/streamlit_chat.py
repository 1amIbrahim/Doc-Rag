import streamlit as st
#from ktem.utils import extract_file_urls, parse_chat_command

class ChatPageStreamlit:
    def __init__(self, app):
        self.app = app

    # def render(self):
    #     st.title("Kotaemon Chat")

    #     if "chat_history" not in st.session_state:
    #         st.session_state.chat_history = []
    #     if "conversation_id" not in st.session_state:
    #         st.session_state.conversation_id = None
    #     if "chat_state" not in st.session_state:
    #         st.session_state.chat_state = {}
    #     if "command_state" not in st.session_state:
    #         st.session_state.command_state = {}
    #     if "user_id" not in st.session_state:
    #         st.session_state.user_id = "default"

    #     # Settings UI
    #     with st.sidebar:
    #         st.header("Settings")
    #         reasoning_type = st.selectbox("Reasoning", self.app.default_settings.reasoning.get_ids())
    #         llm_type = st.selectbox("LLM", self.app.default_settings.application.get("llm_provider").options)
    #         use_mindmap = st.checkbox("Enable Mindmap", value=True)
    #         use_citation = st.checkbox("Show Citations", value=True)
    #         language = st.selectbox("Language", self.app.default_settings.application.get("language").options)

    #     # Show history
    #     for role, msg in st.session_state.chat_history:
    #         with st.chat_message(role):
    #             st.markdown(msg)

    #     # Input + handler
    #     if user_input := st.chat_input("Ask something..."):
    #         with st.chat_message("user"):
    #             st.markdown(user_input)
    #         st.session_state.chat_history.append(("user", user_input))

    #         with st.chat_message("assistant"):
    #             with st.spinner("Thinking..."):
    #                 for response in self.chat_fn(
    #                     st.session_state.conversation_id,
    #                     st.session_state.chat_history,
    #                     self.app.default_settings,
    #                     reasoning_type,
    #                     llm_type,
    #                     use_mindmap,
    #                     use_citation,
    #                     language,
    #                     st.session_state.chat_state,
    #                     st.session_state.command_state,
    #                     st.session_state.user_id,
    #                 ):
    #                     if response.channel == "chat":
    #                         st.markdown(response.content)
    #                     elif response.channel == "info":
    #                         st.info(response.content)
    #                     elif response.channel == "plot":
    #                         st.plotly_chart(response.content)

    #                 st.session_state.chat_history.append(("assistant", response.content))

    def chat_fn(self, conversation_id, chat_history, settings, reasoning_type, llm_type,
                use_mindmap, use_citation, language, chat_state, command_state, user_id, *args):

        pipeline, reasoning_state = self.create_pipeline(
            settings,
            reasoning_type,
            llm_type,
            use_mindmap,
            use_citation,
            language,
            chat_state,
            command_state,
            user_id,
            *args,
        )

        last_user_msg = next((msg for role, msg in reversed(chat_history) if role == "user"), "")

        return pipeline.stream(
            query=last_user_msg,
            conversation_id=conversation_id,
            history=chat_history,
        )

    def create_pipeline(self, settings, reasoning_type, llm_type,
                        use_mindmap, use_citation, language,
                        chat_state, command_state, user_id, *args):
        from ktem.reasoning import get_reasoning
        from ktem.llm import get_llm
        from ktem.retriever import get_retrievers

        llm = get_llm(settings, llm_type=llm_type)
        retrievers = get_retrievers(settings=settings, inputs=args)
        reasoning = get_reasoning(reasoning_type)

        pipeline = reasoning(
            llm=llm,
            retrievers=retrievers,
            use_mindmap=use_mindmap,
            use_citation=use_citation,
            language=language,
            chat_state=chat_state,
            command_state=command_state,
            user_id=user_id,
        )

        return pipeline, reasoning
