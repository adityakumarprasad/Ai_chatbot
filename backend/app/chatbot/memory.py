from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, RemoveMessage
from backend.app.chatbot.state import ChatState

def get_summarizer_model() -> ChatGoogleGenerativeAI:
    """Return the Gemini model for summarization."""
    return ChatGoogleGenerativeAI(model="gemini-1.5-flash")

async def summarize_conversation(state: ChatState):
    """Summarizes older conversation messages and deletes them from active state."""
    model = get_summarizer_model()
    existing_summary = state.get("summary", "")

    # Build summarization prompt
    if existing_summary:
        prompt = (
            f"Existing summary:\n{existing_summary}\n\n"
            "Extend the summary using the new conversation above."
        )
    else:
        prompt = "Summarize the conversation above."

    messages_for_summary = state["messages"] + [
        HumanMessage(content=prompt)
    ]

    response = await model.ainvoke(messages_for_summary)

    # Keep only last 2 messages verbatim, delete the rest to save context window
    messages_to_delete = state["messages"][:-2]

    return {
        "summary": str(response.content),
        "messages": [RemoveMessage(id=m.id) for m in messages_to_delete if m.id],
    }

def should_summarize(state: ChatState) -> str:
    """Routing function that determines if memory consolidation is needed."""
    messages = state.get("messages", [])
    # If the thread message history grows past 6 messages, trigger summarization
    if len(messages) > 6:
        return "summarize"
    return "__end__"
