# Model Context Protocol (MCP) Guide: Setting Up a GitHub Server

This guide explains what **Model Context Protocol (MCP)** is, how to write a custom GitHub MCP server using `fastmcp` (in Python), and how to connect it to our main LangGraph chatbot.

---

## 1. What is Model Context Protocol (MCP)?

Created by Anthropic, **Model Context Protocol (MCP)** is an open standard that allows LLMs to interact with external tools, APIs, and data sources securely and dynamically.

Instead of writing custom API integration code for every tool in every LLM framework, MCP introduces a standard client-server architecture:

```text
┌─────────────────┐           ┌──────────────┐           ┌──────────────┐
│  AI Application │ ◄───────► │  MCP Client  │ ◄───────► │  MCP Server  │
│  (e.g. LangGraph)│           │  (Adapter)   │  Stdio   │  (GitHub API)│
└─────────────────┘           └──────────────┘           └──────────────┘
```

- **MCP Host**: The application using the LLM (our FastAPI backend).
- **MCP Client**: The integration layer inside the host that connects to the server (`langchain-mcp-adapters`).
- **MCP Server**: A standalone process that exposes specific resources, prompts, and **tools** (our FastMCP GitHub script).

---

## 2. Transports: Stdio vs. SSE

MCP supports two primary communication channels (transports) between clients and servers:

### A. Stdio (Standard Input/Output)
- **How it works**: The host launches the MCP server script as a **local subprocess** and communicates with it by writing to the server's `stdin` and reading from its `stdout`.
- **Pros**: Zero networking overhead, highly secure (only the parent process can access it), no port allocation or firewalls to worry about.
- **Best For**: Local tools, development, and internal subprocess scripts. **We are using this transport for our GitHub integration!**

### B. SSE (Server-Sent Events)
- **How it works**: The server runs as a separate web application (often over HTTP), and the client establishes a persistent SSE connection.
- **Pros**: Allows the server to run in a separate network, cloud container, or cluster.
- **Best For**: Remote microservices or cloud-hosted tool integrations.

---

## 3. Building an MCP Server with `fastmcp`

`fastmcp` is a clean, developer-friendly Python framework (built on top of the raw `mcp` SDK) that lets you turn functions into LLM tools using decorators, similar to FastAPI.

### Code Example: Basic MCP Server

```python
# server.py
from mcp.server.fastmcp import FastMCP

# 1. Initialize the FastMCP app
mcp = FastMCP("My Local Helper")

# 2. Register a tool using the decorator
@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""  # This docstring is sent to the LLM as the tool description!
    return a + b

if __name__ == "__main__":
    # 3. Run the server using stdio transport
    mcp.run()
```

---

## 4. The GitHub MCP Server Implementation

Our custom GitHub MCP server will read the `GITHUB_TOKEN` environment variable and use `httpx` (async HTTP client) to communicate with the GitHub API.

### Exposing GitHub Tools
Here is a simplified view of the tools we'll build in `mcp_github/server.py`:

```python
import os
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("GitHub Server")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}" if GITHUB_TOKEN else "",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "FastMCP-Github-Server"
}

@mcp.tool()
async def search_repos(query: str) -> str:
    """
    Search for repositories on GitHub.
    Returns the names and descriptions of matching repositories.
    """
    url = f"https://api.github.com/search/repositories?q={query}"
    
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=HEADERS)
        if r.status_code != 200:
            return f"Error: Failed to fetch repositories from GitHub ({r.status_code})"
        
        items = r.json().get("items", [])
        results = []
        for item in items[:5]:
            results.append(f"- {item['full_name']}: {item['description']} ({item['html_url']})")
        return "\n".join(results) if results else "No repositories found."
```

---

## 5. Connecting the MCP Server to LangGraph

In the main application, we use the `langchain-mcp-adapters` package to load the MCP server's tools into LangGraph.

Because we are using **stdio** transport, the backend will spawn our GitHub MCP script using Python.

```python
import sys
from pathlib import Path
from langchain_mcp_adapters.client import MultiServerMCPClient

# 1. Define the connections to our MCP servers
mcp_client = MultiServerMCPClient({
    "github": {
        "transport": "stdio",
        "command": sys.executable,  # Uses the currently running python environment executable
        "args": ["c:/Users/itsad/Desktop/AI_chat/mcp_github/server.py"]
    }
})

# 2. Manage the connection lifecycle inside FastAPI's startup lifespan
async with mcp_client:
    # 3. Retrieve the parsed LangChain tools from the MCP server
    mcp_tools = await mcp_client.get_tools()
    
    # 4. Combine with any local tools
    all_tools = [local_search_tool, *mcp_tools]
    
    # 5. Bind the tools to our OpenAI Model
    llm_with_tools = llm.bind_tools(all_tools)
```

### How the LLM executes the tool
1. User asks: *"Find the repository 'openai/openai-python' on GitHub."*
2. **LangGraph Chat Node**: Invokes the LLM with the list of bound tools. The LLM recognizes the query and outputs a tool call request: `search_repos(query="openai/openai-python")`.
3. **LangGraph Tool Node**: Sees the tool call request, identifies it as an MCP tool, and forwards the arguments over stdio (`stdin`) to the `mcp_github/server.py` subprocess.
4. **GitHub MCP Server**: Receives the command, runs `search_repos` function, queries the GitHub API, and writes the output string back to standard output (`stdout`).
5. **Tool Node**: Receives the output string and attaches it to the LangGraph thread as a `ToolMessage`.
6. **Chat Node**: The LLM reads the tool output and gives the final natural response to the user.
