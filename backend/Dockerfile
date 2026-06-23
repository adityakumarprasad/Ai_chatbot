# Use a lightweight Python base image
FROM python:3.11-slim

# Install system dependencies needed for compiling Postgres and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Install uv package manager for high-speed installs
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy Python requirements files
COPY backend/requirements.txt ./backend_requirements.txt
COPY mcp_github/requirements.txt ./mcp_requirements.txt

# Install backend and MCP dependencies into the system python environment
RUN uv pip install --system -r backend_requirements.txt -r mcp_requirements.txt

# Copy backend and MCP codebase
COPY backend /app/backend
COPY mcp_github /app/mcp_github

# Set PYTHONPATH environment variable to resolve packages
ENV PYTHONPATH=/app
# Default environment to production
ENV ENV=production

# Expose dynamic container port
EXPOSE 8000

# Launch uvicorn runner
CMD ["python", "backend/run.py"]
