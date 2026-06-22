from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.app.chatbot.state import ChatState
from backend.app.chatbot.tools import get_base_tools
from backend.app.chatbot.memory import summarize_conversation, should_summarize

def compile_chatbot(checkpointer, mcp_tools=None):
    """
    Compiles the LangGraph StateGraph chatbot with the given checkpointer
    and dynamically loaded MCP tools.
    """
    if mcp_tools is None:
        mcp_tools = []

    # 1. Bind local tools and MCP tools to the Gemini LLM
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
    all_tools = get_base_tools() + mcp_tools
    llm_with_tools = llm.bind_tools(all_tools) if all_tools else llm

    # 2. Define the main chat node
    async def chat_node(state: ChatState):
        messages = []
        
        # Inject existing summary if present
        summary = state.get("summary", "")
        if summary:
            messages.append({
                "role": "system",
                "content": f"Conversation summary:\n{summary}"
            })
            
        messages.extend(state["messages"])
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    # 3. Setup StateGraph
    builder = StateGraph(ChatState)
    builder.add_node("chat", chat_node)
    builder.add_node("summarize", summarize_conversation)

    # 4. Integrate tool execution and routing
    if all_tools:
        tool_node = ToolNode(all_tools)
        builder.add_node("tools", tool_node)

        # Custom router to handle tool calling and summarization in sequence
        def route_after_chat(state: ChatState) -> str:
            last_message = state["messages"][-1]
            # If the LLM requested a tool execution, route to tools
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "tools"
            # Otherwise, evaluate if history is large enough to summarize
            return should_summarize(state)

        builder.add_conditional_edges(
            "chat",
            route_after_chat,
            {
                "tools": "tools",
                "summarize": "summarize",
                "__end__": END
            }
        )
        # Go back to chat node after tool completes
        builder.add_edge("tools", "chat")
    else:
        # If no tools are configured, route straight to summarization check
        builder.add_conditional_edges(
            "chat",
            should_summarize,
            {
                "summarize": "summarize",
                "__end__": END
            }
        )

    # Edge from summarizer to the end
    builder.add_edge("summarize", END)

    # Set entry point
    builder.add_edge(START, "chat")

    # Compile the graph with persistent PostgreSQL checkpointer
    return builder.compile(checkpointer=checkpointer)
