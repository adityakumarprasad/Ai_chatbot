import sys
import uuid
import json
from pathlib import Path
from contextlib import asynccontextmanager, AsyncExitStack
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient

from backend.app.config import settings
from backend.app.database import get_db_pool, init_checkpointer, close_db_pool
from backend.app.schemas import ChatRequest, ThreadCreateResponse, ThreadListResponse, HistoryResponse, MessageResponse
from backend.app.chatbot.graph import compile_chatbot

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the startup and shutdown lifecycles:
    - Open PostgreSQL connection pool and run checkpointer migrations.
    - Start the GitHub MCP server subprocess and connect over stdio.
    - Compile the chatbot graph with the database checkpointer and tools.
    - Clean up resources on shutdown.
    """
    app.state.exit_stack = AsyncExitStack()
    
    try:
        # 1. Initialize PostgreSQL pool and database saver
        print("Connecting to PostgreSQL pool...")
        pool = get_db_pool()
        await pool.open()
        checkpointer = await init_checkpointer()
        print("PostgreSQL checkpointer configured successfully.")

        # 2. Configure and startup GitHub MCP server over stdio
        server_path = str(Path(settings.BASE_DIR) / "mcp_github" / "server.py")
        print(f"Spawning GitHub MCP server: {server_path}")
        
        mcp_client = MultiServerMCPClient({
            "github": {
                "transport": "stdio",
                "command": sys.executable,  # Use backend virtual environment Python binary
                "args": [server_path]
            }
        })
        
        # Enter the client async context, starting the subprocess
        await app.state.exit_stack.enter_async_context(mcp_client)
        print("Connected to GitHub MCP server.")

        # Retrieve tools from MCP server
        mcp_tools = await mcp_client.get_tools()
        print(f"Retrieved {len(mcp_tools)} tools from GitHub MCP.")

        # 3. Compile LangGraph chatbot
        chatbot = compile_chatbot(checkpointer=checkpointer, mcp_tools=mcp_tools)
        
        # Store in app state
        app.state.chatbot = chatbot
        app.state.mcp_client = mcp_client
        app.state.db_pool = pool
        
    except Exception as e:
        print(f"CRITICAL failure during startup: {str(e)}")
        # Clean up anything started
        await app.state.exit_stack.aclose()
        await close_db_pool()
        raise e

    yield
    
    # Clean up resources on shutdown
    print("Stopping application services...")
    await app.state.exit_stack.aclose()
    await close_db_pool()
    print("Application services stopped.")

# Initialize app with lifespan
app = FastAPI(title="AI Chat Space Backend", lifespan=lifespan)

# Enable CORS for Next.js frontend calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/threads", response_model=ThreadCreateResponse)
async def create_thread():
    """Create a new thread ID (UUID)."""
    return {"thread_id": str(uuid.uuid4())}

@app.get("/api/threads", response_model=ThreadListResponse)
async def list_threads():
    """Retrieve all active thread IDs from database checkpoints."""
    try:
        checkpointer = await init_checkpointer()
        threads = set()
        async for checkpoint in checkpointer.alist(None):
            thread_id = checkpoint.config["configurable"].get("thread_id")
            if thread_id:
                threads.add(str(thread_id))
        return {"threads": list(threads)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch threads: {str(e)}"
        )

@app.get("/api/threads/{thread_id}/messages", response_model=HistoryResponse)
async def get_thread_history(thread_id: str):
    """Retrieve message history for a specific thread."""
    chatbot = getattr(app.state, "chatbot", None)
    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chatbot is not initialized."
        )
    
    try:
        state = await chatbot.aget_state(config={"configurable": {"thread_id": thread_id}})
        messages = state.values.get("messages", [])
        
        formatted = []
        for m in messages:
            # Map role
            if m.type == "human":
                role = "user"
            elif m.type == "ai":
                role = "assistant"
            elif m.type == "tool":
                role = "tool"
            else:
                role = m.type
            
            # Map name if present (useful for tool calls)
            name = getattr(m, "name", None)
            formatted.append(MessageResponse(role=role, content=str(m.content), name=name))
            
        return {"messages": formatted}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load history: {str(e)}"
        )

@app.post("/api/chat")
async def chat(request_data: ChatRequest):
    """
    Handles user messages and streams back Server-Sent Events (SSE).
    Yields:
      - 'message': raw text chunks from assistant
      - 'tool_start': tool execution is starting
      - 'tool': tool execution finished
      - 'error': errors
    """
    chatbot = getattr(app.state, "chatbot", None)
    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chatbot is not initialized."
        )
        
    thread_id = request_data.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    async def event_generator():
        try:
            async for message_chunk, metadata in chatbot.astream(
                {"messages": [HumanMessage(content=request_data.message)]},
                config=config,
                stream_mode="messages"
            ):
                # 1. Handle tool execution completion
                if isinstance(message_chunk, ToolMessage):
                    yield {
                        "event": "tool",
                        "data": json.dumps({
                            "name": getattr(message_chunk, "name", "tool"),
                            "content": str(message_chunk.content),
                            "status": "complete"
                        })
                    }
                # 2. Handle assistant chunks
                elif isinstance(message_chunk, AIMessage):
                    # Check if the assistant has requested a tool call (starting status)
                    if hasattr(message_chunk, "tool_calls") and message_chunk.tool_calls:
                        for tc in message_chunk.tool_calls:
                            yield {
                                "event": "tool_start",
                                "data": json.dumps({
                                    "name": tc.get("name", "tool"),
                                    "id": tc.get("id")
                                })
                            }
                    # Stream ordinary text token
                    elif message_chunk.content:
                        yield {
                            "event": "message",
                            "data": json.dumps({
                                "content": str(message_chunk.content)
                            })
                        }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"detail": str(e)})
            }

    return EventSourceResponse(event_generator())
