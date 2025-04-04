from ktem.main import BaseApp
from ktem.pages.chat import ChatPage

class App(BaseApp):
    def ui(self):
        self.chat_page = ChatPage(self)
    
    def process_query(self, query: str) -> str:
        aggregated_context = ""
        for index in self.index_manager.indices:
            result = index.search(query)
            aggregated_context += result + "\n"
        if not aggregated_context.strip():
            aggregated_context = "No relevant context found."
        if hasattr(self, "chat_page") and hasattr(self.chat_page, "generate_response"):
            answer = self.chat_page.generate_response(query, aggregated_context)
        else:
            answer = (f"Query: {query}\n"
                      f"Context:\n{aggregated_context}\n"
                      "[Response generation is not implemented]")
        return answer
