# Implementation Plan - Modular Next.js & FastAPI Refactor with PostgreSQL, FastMCP GitHub Server, LangGraph, LangSmith, and Gemini AI

This plan outlines the restructuring of the AI Chat application. The current project is a single-process Streamlit application using an SQLite database checkpointer. We will refactor it into a modular, professional multi-tier service:

1. **Frontend**: A Next.js (TypeScript) App Router project styled with **Tailwind CSS** for a clean, premium, and fully responsive user interface.
2. **Backend**: A FastAPI application that compiles and serves the LangGraph chatbot, handling threads, chat history, and streaming SSE tokens.
3. **Database**: A PostgreSQL service used as a checkpointer for LangGraph (`AsyncPostgresSaver`), replacing SQLite.
4. **MCP Server**: A custom GitHub MCP server built using `fastmcp` to expose GitHub tools to the LangGraph chatbot via `stdio` transport.
5. **Observability**: **LangSmith** integration to track, debug, and evaluate the LangGraph agent's execution steps and tool calls.
6. **LLM Provider**: **Gemini AI** (`ChatGoogleGenerativeAI`) as the underlying language model.
7. **Python Tooling**: **`uv`** as the package and virtual environment manager for high-speed dependency resolution.

---

## User Review Required

Please review the following architecture and setup details:

> [!IMPORTANT]
> **Environment Configuration & API Keys**
> You will need to provide the following configuration values in a `.env` file at the project root:
> - `GEMINI_API_KEY` (or `GOOGLE_API_KEY`): For the Gemini LLM model (`ChatGoogleGenerativeAI`).
> - `GITHUB_TOKEN`: For the custom GitHub MCP server to interact with repository operations.
> - `DATABASE_URL`: PostgreSQL connection string (e.g., `postgresql://postgres:postgres@localhost:5432/postgres`).
> - **LangSmith Settings**:
>   - `LANGCHAIN_TRACING_V2`: Set to `true` to enable automatic tracing.
>   - `LANGCHAIN_API_KEY`: Your LangSmith API key.
>   - `LANGCHAIN_PROJECT`: The project name in LangSmith (e.g., `ai-chat-modular`).

> [!TIP]
> **Local PostgreSQL via Docker**
> To make it easy to start a local database, we will include a `docker-compose.yml` file. You can spin up the PostgreSQL instance with:
> ```bash
> docker compose up -d
> ```
> If you prefer a local PostgreSQL instance, you can simply adjust the `DATABASE_URL` connection string accordingly.

---

## Proposed Changes

```mermaid
graph TD
    NextJS[Next.js Frontend] <-->|HTTP / SSE| FastAPI[FastAPI Backend]
    FastAPI <-->|psycopg3| Postgres[(PostgreSQL DB)]
    FastAPI <-->|stdio subprocess| FastMCP[GitHub FastMCP Server]
    FastMCP <-->|GitHub API| GitHub[GitHub Platform]
    FastAPI -.->|Telemetry| LangSmith[LangSmith Cloud]
    FastAPI <-->|Gemini API| Gemini[Google Gemini AI]
```

### 1. Project Configuration & Database Setup

We will introduce a central environment configuration and database helper to manage PostgreSQL connection pools, automatic migrations, and environment bindings for LangSmith.

#### [NEW] [docker-compose.yml](file:///c:/Users/itsad/Desktop/AI_chat/docker-compose.yml)
- Docker configuration file to easily spin up a local PostgreSQL database container.

#### [NEW] [.env.example](file:///c:/Users/itsad/Desktop/AI_chat/.env.example)
- Example template for environment variables (`GEMINI_API_KEY`, `GITHUB_TOKEN`, `DATABASE_URL`, and LangSmith configurations).

---

### 2. FastAPI Backend Component

The backend will be structured as a modular Python package located in `backend/`. Python virtual environments and dependencies will be managed via `uv`.

#### [NEW] [requirements.txt](file:///c:/Users/itsad/Desktop/AI_chat/backend/requirements.txt)
- Lists packages: `fastapi`, `uvicorn`, `langgraph`, `langchain-google-genai`, `langchain-community`, `langchain-mcp-adapters`, `python-dotenv`, `psycopg[binary]`, `psycopg-pool`, `requests`, `duckduckgo-search`, `sse-starlette`, `langsmith`.

#### [NEW] [config.py](file:///c:/Users/itsad/Desktop/AI_chat/backend/app/config.py)
- Configuration module using Pydantic settings to parse, validate, and export environmental configurations. It will automatically load the LangSmith tracing variables into the system environment on execution.

#### [NEW] [database.py](file:///c:/Users/itsad/Desktop/AI_chat/backend/app/database.py)
- Code to manage the PostgreSQL async connection pool and provide the connection manager for LangGraph.

#### [NEW] [schemas.py](file:///c:/Users/itsad/Desktop/AI_chat/backend/app/schemas.py)
- Request and response schemas for REST API endpoints.

#### [NEW] [state.py](file:///c:/Users/itsad/Desktop/AI_chat/backend/app/chatbot/state.py)
- Defines the modular chatbot state using `MessagesState` and tracking an extra conversation summary field.

#### [NEW] [tools.py](file:///c:/Users/itsad/Desktop/AI_chat/backend/app/chatbot/tools.py)
- Defines local tools (DuckDuckGo, stock prices) and initializes the `MultiServerMCPClient` connection.

#### [NEW] [memory.py](file:///c:/Users/itsad/Desktop/AI_chat/backend/app/chatbot/memory.py)
- Nodes and conditional edges for managing short-term conversation summarization.

#### [NEW] [graph.py](file:///c:/Users/itsad/Desktop/AI_chat/backend/app/chatbot/graph.py)
- Compiles the LangGraph StateGraph, integrating the nodes (configured for Gemini), conditional routers, checkpointer, and bindings.

#### [NEW] [main.py](file:///c:/Users/itsad/Desktop/AI_chat/backend/app/main.py)
- The FastAPI application endpoints:
  - App lifespan setup (starting PostgreSQL pool, setting up checkpointer schema, initiating GitHub MCP connection).
  - `POST /api/threads`: Creates new thread UUIDs.
  - `GET /api/threads`: Lists existing active thread IDs from database.
  - `GET /api/threads/{thread_id}/messages`: Returns messages history.
  - `POST /api/chat`: Receives new user messages and streams SSE chunks back.

#### [NEW] [run.py](file:///c:/Users/itsad/Desktop/AI_chat/backend/run.py)
- Python entrypoint to boot FastAPI application using `uvicorn`.

---

### 3. GitHub MCP Component

A standalone directory for the custom GitHub Model Context Protocol server.

#### [NEW] [requirements.txt](file:///c:/Users/itsad/Desktop/AI_chat/mcp_github/requirements.txt)
- Packages needed for the MCP server: `fastmcp` and `httpx`.

#### [NEW] [server.py](file:///c:/Users/itsad/Desktop/AI_chat/mcp_github/server.py)
- The MCP server exposing GitHub tools using `@mcp.tool()`. Exposes search, file reading, issue creation, and file commits.

---

### 4. Next.js Frontend Component

A beautiful Next.js application styled with Tailwind CSS that displays conversation lists and provides standard chat bubbles and collapsible tool indicators.

#### [NEW] [package.json](file:///c:/Users/itsad/Desktop/AI_chat/frontend/package.json)
- React, Next.js, and Tailwind CSS dependencies.

#### [NEW] [layout.tsx](file:///c:/Users/itsad/Desktop/AI_chat/frontend/src/app/layout.tsx)
- Sets up standard HTML and mounts Google Fonts (Outfit or Inter) for premium typography.

#### [NEW] [globals.css](file:///c:/Users/itsad/Desktop/AI_chat/frontend/src/app/globals.css)
- Imports Tailwind directives and details premium custom utilities, animations, and typography.

#### [NEW] [Sidebar.tsx](file:///c:/Users/itsad/Desktop/AI_chat/frontend/src/components/Sidebar.tsx)
- Tailwind-styled panel containing conversation history cards, "New Chat" button, and status info.

#### [NEW] [ChatWindow.tsx](file:///c:/Users/itsad/Desktop/AI_chat/frontend/src/components/ChatWindow.tsx)
- Contains message bubbles, typing indicators, tool-execution status logs (expandable cards detailing tool inputs/outputs), and chat input.

#### [NEW] [page.tsx](file:///c:/Users/itsad/Desktop/AI_chat/frontend/src/app/page.tsx)
- Combines `Sidebar` and `ChatWindow` into a cohesive, responsive grid layout.

---

### 5. Cleanup

We will remove the monolithic files once they have been successfully refactored.

#### [DELETE] [backend.py](file:///c:/Users/itsad/Desktop/AI_chat/backend.py)
#### [DELETE] [frontend.py](file:///c:/Users/itsad/Desktop/AI_chat/frontend.py)
#### [DELETE] [short_term_memory.py](file:///c:/Users/itsad/Desktop/AI_chat/short_term_memory.py)

---

## Verification Plan

### Automated Tests
1. **Python Dependencies Verification**: Run `uv venv` and install requirements with `uv pip install -r backend/requirements.txt` and `uv pip install -r mcp_github/requirements.txt`.
2. **FastAPI Lint Check**: Run uvicorn server in a dry run or execute basic import verification.
3. **TypeScript Build Check**: Run `npm run build` in `frontend/` to confirm there are no syntax or type errors.

### Manual Verification
1. Start PostgreSQL server (locally or using docker).
2. Start the GitHub MCP server standalone using `mcp dev mcp_github/server.py` (or verify it can be imported).
3. Start the FastAPI backend server using `python backend/run.py`.
4. Start the Next.js dev server using `npm run dev` in `frontend/`.
5. Open the app in browser, initiate a chat thread, verify LLM remembers state across messages (checked via PostgreSQL thread checkpoints).
6. Request the LLM to search for a GitHub repository or create a GitHub issue, and verify that the tool call starts the stdio MCP server, issues the request, and displays the tool log with results.
7. Open LangSmith dashboard to verify traces are recorded for each step of the LangGraph execution.
