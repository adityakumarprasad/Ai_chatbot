# AI Chat Space: Next.js + FastAPI + PostgreSQL + LangGraph + FastMCP

AI Chat Space is a premium, modular AI assistant workspace. It integrates Google Gemini AI, persistent PostgreSQL state checkpointers, multi-document RAG (Retrieval-Augmented Generation), a custom GitHub MCP (Model Context Protocol) tool server, and LangSmith observability, wrapped in a sleek, responsive Next.js frontend.

---

## 🚀 Key Features

* **Google Gemini AI Integration**: Powered by Gemini 2.5 Flash for high-speed reasoning, message streaming, and state tracking.
* **Persistent PostgreSQL Checkpoints**: Uses `AsyncPostgresSaver` connection pools with autocommit settings to save chat threads and context states permanently across server reboots.
* **Multi-Document RAG Q&A**: Upload multiple PDF documents dynamically within a thread. The backend chunks pages, indexes them into a local FAISS vector store, and enables the model to perform RAG searches across all active files.
* **Model Context Protocol (MCP)**: Spawns a custom GitHub MCP tool server (stdio subprocess) using `fastmcp`. This allows the AI agent to search repositories, list issues, create bugs, view source files, and commit code directly.
* **LangSmith Observability**: Injected telemetry hooks to automatically track, log, and trace LLM steps and tool calls in real-time.
* **Premium Dark Theme**: Next.js App Router frontend styled with Tailwind CSS, featuring glassmorphism cards, dynamic file attachment lists, typing indicator loaders, and smooth micro-animations.

---

## 📁 Directory Structure

```text
AI_chat/
├── README.md               # Project documentation
├── deployment_guide.md     # Production hosting guide (Vercel, Render, Neon)
├── docker-compose.yml      # Local PostgreSQL container
├── .gitignore              # Ignored local files (.venv, node_modules, .env)
├── .env.example            # Environment variables template
│
├── backend/                # FastAPI application
│   ├── Dockerfile          # Production container setup
│   ├── requirements.txt    # Python requirements (LangGraph, Gemini, psycopg3)
│   ├── run.py              # Server uvicorn entrypoint (dynamic port resolution)
│   └── app/                # Main backend source files
│       ├── main.py         # Routes (thread histories, streaming SSE, file uploads)
│       ├── config.py       # Pydantic settings & LangSmith environment bindings
│       ├── database.py     # Postgres connection pool and saver setup
│       ├── schemas.py      # Request/response validation models
│       └── chatbot/        # LangGraph subgraph
│           ├── graph.py    # StateGraph, chat nodes, and conditional routers
│           ├── state.py    # Message list and memory summarizer state schema
│           ├── tools.py    # Local tools (Calculator, DDG Search, RAG search)
│           ├── memory.py   # Short-term conversation summarizer node
│           └── rag.py      # PDF parsing, FAISS vector indexing, and RAG store
│
├── mcp_github/             # Standalone GitHub Model Context Protocol server
│   ├── requirements.txt    # FastMCP and httpx requirements
│   └── server.py           # GitHub tool definitions (Search, Code Read, Commits)
│
└── frontend/               # Next.js App Router Frontend
    ├── package.json        # Next, React, Lucide-React, and Tailwind dependencies
    ├── next.config.ts      # Next.js build compilation configurations
    └── src/
        ├── app/
        │   ├── globals.css # Tailwind theme settings and glassmorphic designs
        │   ├── layout.tsx  # Root html layout and Outfit Google Font
        │   └── page.tsx    # Home page coordinating socket states and SSE readers
        └── components/
            ├── Sidebar.tsx # Conversational thread history management cards
            └── ChatWindow.tsx # Chat dialog screen, tool accordion logs, and RAG badges
```

---

## 🛠️ Local Development Setup

### Prerequisite Environment Variables
Create a `.env` file in the root directory `c:\Users\itsad\Desktop\AI_chat\.env` and supply your credentials:
```env
# Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# GitHub Token (with repository write permissions for commits/issues)
GITHUB_TOKEN=your_github_personal_access_token_here

# PostgreSQL database URI (Local Docker default)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/chatbot

# LangSmith tracing variables (optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=ai-chat-workspace
```

### 1. Launch PostgreSQL database
Start Docker Desktop and run:
```bash
docker compose up -d
```

### 2. Boot the FastAPI Backend
Create a virtual environment, install the backend dependencies, and launch uvicorn:
```bash
# Initialize venv
uv venv
.venv\Scripts\activate

# Install requirements (Resolves in parallel with uv)
uv pip install -r backend/requirements.txt

# Run server
python backend/run.py
```
*The backend server will launch on `http://localhost:8000`.*

### 3. Boot the Next.js Frontend
In a new terminal window, navigate to the frontend folder, install npm packages, and run the developer server:
```bash
cd frontend
npm install
npm run dev
```
*The frontend application will boot on `http://localhost:3000`.*

---

## 🧪 Quick In-App Testing Prompts

Open `http://localhost:3000`, select a thread, and try these prompts to test tools:
* **DuckDuckGo Web Search**: *"Find the latest news about Google Gemini model updates."*
* **Arithmetic Calculator**: *"Solve `(256 * 18.5) / 2.2`."*
* **Stock Price Lookup**: *"What is the current stock quote of Apple (AAPL)?"*
* **GitHub MCP Search**: *"Search GitHub for repositories matching 'fastmcp'."*
* **Multi-Document RAG Q&A**:
  1. Click the **paperclip** icon next to the chat bar and upload a PDF document.
  2. Once the notification pill appears above the bar, ask: *"Summarize the main sections of this document."*
  3. Upload another PDF and ask: *"Contrast the findings in document 1 with document 2."*
