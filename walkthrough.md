# Walkthrough - Modular Next.js & FastAPI Refactor

The AI Chat application has been successfully refactored from a monolithic Streamlit script into a professional, modular, multi-tier stack featuring **Next.js** (frontend), **FastAPI** (backend), **PostgreSQL** (persistent checkpointers), and a custom **GitHub MCP server**. 

Here is a summary of what has been accomplished.

---

## 1. Directory Structure

The project has been organized into the following clean, modular structure:

```text
AI_chat/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── backend/
│   ├── requirements.txt
│   ├── run.py
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── schemas.py
│       └── chatbot/
│           ├── __init__.py
│           ├── graph.py
│           ├── state.py
│           ├── tools.py
│           └── memory.py
├── mcp_github/
│   ├── requirements.txt
│   └── server.py
└── frontend/
    ├── package.json
    ├── next.config.ts
    ├── src/
    │   ├── app/
    │   │   ├── globals.css
    │   │   ├── layout.tsx
    │   │   └── page.tsx
    │   └── components/
    │       ├── Sidebar.tsx
    │       └── ChatWindow.tsx
```

---

## 2. Changes Made & Component Features

### A. Project & DB Setup
- **[docker-compose.yml](file:///c:/Users/itsad/Desktop/AI_chat/docker-compose.yml)**: Configured to spin up a PostgreSQL instance on port `5432` with a persistent volume.
- **[.gitignore](file:///c:/Users/itsad/Desktop/AI_chat/.gitignore)**: Configured to ignore python environments (`.venv`), node modules, compiler files, and local `.env` variables.
- **[.env.example](file:///c:/Users/itsad/Desktop/AI_chat/.env.example)**: Added configuration templates for Gemini AI, GitHub, PostgreSQL, and LangSmith.

### B. FastAPI Backend (`backend/`)
- **Python Tooling**: Created a virtual environment using **`uv`**, speeding up resolutions and dependency management.
- **Auto-Telemetry Setup (`app/config.py`)**: Automatically loads and binds LangSmith environment variables (`LANGCHAIN_TRACING_V2=true`, `LANGCHAIN_API_KEY`) on startup to log and track execution steps.
- **Checkpointer (`app/database.py`)**: Configured `AsyncPostgresSaver` backed by a `psycopg-pool` async connection pool, setting up chat schemas in PostgreSQL.
- **LangGraph Compiler (`app/chatbot/graph.py`)**: Rebuilt the graph to use Google Gemini (`ChatGoogleGenerativeAI`), binding both local tools (DuckDuckGo, Stock Quote) and dynamic stdio-transport MCP tools. Included a custom sequential router to handle tool queries and summarization checks on the state.
- **Streaming Endpoints (`app/main.py`)**: Implemented REST calls for thread tracking, message history, and a Server-Sent Events (SSE) `/api/chat` router. It yields granular trace events (e.g. `tool_start` with names and IDs, raw `message` tokens, and `tool` completions).

### C. GitHub MCP Server (`mcp_github/`)
- **[mcp_github/server.py](file:///c:/Users/itsad/Desktop/AI_chat/mcp_github/server.py)**: A FastMCP server exposing GitHub APIs via `@mcp.tool()` wrappers. Includes:
  - `search_repositories`
  - `get_repository_details`
  - `list_issues`
  - `create_issue`
  - `get_file_content`
  - `create_or_update_file` (automatically resolves commit SHAs if a file exists, making updates clean).

### D. Next.js Frontend (`frontend/`)
- **Bootstrap**: Next.js App Router project initialized with Tailwind CSS.
- **[globals.css](file:///c:/Users/itsad/Desktop/AI_chat/frontend/src/app/globals.css)**: Implemented a premium dark mode layout with custom scrollbars, glowing accent boundaries, glassmorphism panel styles, and entrance transitions.
- **[Sidebar.tsx](file:///c:/Users/itsad/Desktop/AI_chat/frontend/src/components/Sidebar.tsx)**: Thread history listings with responsive selected glows and creation handlers.
- **[ChatWindow.tsx](file:///c:/Users/itsad/Desktop/AI_chat/frontend/src/components/ChatWindow.tsx)**: Displays bubbles with custom bot/user indicators. Render collapsible, expandable accordion cards for tool executions showing raw inputs and returns.
- **[page.tsx](file:///c:/Users/itsad/Desktop/AI_chat/frontend/src/app/page.tsx)**: Manages communication states. Implemented a custom asynchronous reader using `ReadableStream` on `fetch` to read and display SSE events (updating text tokens and tool indicators in real-time).

---

## 3. Verification & Build Results

1. **Backend Imports & Settings Verification**:
   Running a dry-run check of the Python graph compiler and database pool initialization completed successfully.
   ```powershell
   Imports successful!
   ```
2. **Next.js Production Build Validation**:
   Executed a full production compile of the Next.js React project. Built cleanly in Turbopack with zero errors:
   ```bash
   ✓ Compiled successfully in 8.9s
   ✓ Generating static pages (4/4) in 662ms
   ```

---

## 4. How to Run Locally

### Step 1: Set up environment variables
Create a `.env` file in the root workspace `c:\Users\itsad\Desktop\AI_chat\.env` (using `.env.example` as a template) and add your keys:
```env
GEMINI_API_KEY=AIzaSy...
GITHUB_TOKEN=ghp_...
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/chatbot
```

### Step 2: Spin up PostgreSQL database
Run Docker Desktop and start the container:
```powershell
docker compose up -d
```

### Step 3: Run the FastAPI backend
Activate the virtual environment and start the uvicorn development server:
```powershell
.venv\Scripts\activate
python backend/run.py
```

### Step 4: Run the Next.js frontend
In a separate terminal, launch the dev server:
```powershell
cd frontend
npm run dev
```

Open `http://localhost:3000` in your browser. Create a new thread and interact with your AI agent!
