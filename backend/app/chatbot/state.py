from langgraph.graph import MessagesState

class ChatState(MessagesState):
    """
    State representing the chat conversation.
    Inherits 'messages' from MessagesState (with automatic add_messages reducer).
    Adds 'summary' to track the consolidated short-term memory summary.
    """
    summary: str
