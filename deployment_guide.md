# Deployment Guide: Next.js (Vercel) + FastAPI (Render/Railway) + PostgreSQL

This guide provides step-by-step instructions to deploy your modular AI Chat application to production.

---

## Production Tech Stack Overview
1. **Frontend**: Next.js hosted on **Vercel**.
2. **Backend**: FastAPI containerized and hosted on **Render** or **Railway**.
3. **Database**: PostgreSQL hosted on **Supabase** or **Neon**.
4. **GitHub MCP Server**: Spawns automatically as a stdio subprocess inside the backend container.

```mermaid
graph LR
    Vercel[Vercel: Next.js Frontend] -->|HTTPS Requests / SSE| Render[Render/Railway: FastAPI Backend]
    Render -->|Postgres Protocol| Supabase[(Supabase / Neon DB)]
    Render -->|Local Stdio Subprocess| MCP[GitHub MCP Server]
```

---

## Step 1: Set up a Managed PostgreSQL Database (Neon or Supabase)

To replace your local Docker PostgreSQL, you need a cloud-hosted Postgres instance.

### Using Neon (Easiest)
1. Go to [Neon.tech](https://neon.tech/) and sign up.
2. Create a new project named `ai-chat-db`.
3. Select **PostgreSQL 16** (default).
4. Copy the connection string from the dashboard. It will look like this:
   `postgresql://neondb_owner:password@ep-cool-snowflake-a5h...neon.tech/neondb?sslmode=require`
5. Store this string. This is your production `DATABASE_URL`.

---

## Step 2: Deploy the FastAPI Backend (Render or Railway)

We will deploy the backend as a containerized web service. The `backend/Dockerfile` in your root folder automatically installs `uv` and configures python libraries.

### Using Render
1. Commit all your changes and push them to a private/public **GitHub repository**.
2. Sign up on [Render.com](https://render.com/).
3. Click **New +** and select **Web Service**.
4. Connect your GitHub repository.
5. In the creation wizard, configure:
   - **Name**: `ai-chat-backend`
   - **Language**: `Docker` (Render will automatically detect your `backend/Dockerfile` inside the repo)
   - **Docker Build Context**: `.` (Crucial: set to the project root folder)
   - **Dockerfile Path**: `backend/Dockerfile`
   - **Instance Type**: Free or Starter
6. Expand **Advanced** and add the following **Environment Variables**:
   - `GEMINI_API_KEY`: Your Gemini API key.
   - `GITHUB_TOKEN`: Your Personal Access Token for GitHub tools.
   - `DATABASE_URL`: The Neon or Supabase connection string from Step 1.
   - `ENV`: `production` (tells uvicorn to disable reload).
   - `LANGCHAIN_TRACING_V2`: `true`
   - `LANGCHAIN_API_KEY`: Your LangSmith API key.
   - `LANGCHAIN_PROJECT`: `ai-chat-production`
7. Click **Create Web Service**. Once built, copy your service URL (e.g., `https://ai-chat-backend.onrender.com`).

---

## Step 3: Deploy the Next.js Frontend (Vercel)

Next.js is natively supported and optimized on Vercel.

1. Sign up on [Vercel.com](https://vercel.com/) and click **Add New** > **Project**.
2. Import your GitHub repository.
3. In the project settings, configure:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: `frontend` (Crucial: click edit and select the `frontend` folder since Next.js resides inside it)
4. Expand **Environment Variables** and add the public API url configuration:
   - **Key**: `NEXT_PUBLIC_API_URL`
   - **Value**: The URL of your deployed Render/Railway backend (e.g., `https://ai-chat-backend.onrender.com`)
5. Click **Deploy**. Vercel will build your static files and deploy the application.

---

## Step 4: Configure CORS (Cross-Origin Resource Sharing)

In a production environment, browsers block frontend calls to a different backend domain unless CORS is configured to trust that domain.

### Action: Restrict CORS domains in backend
Open `backend/app/main.py` and modify the CORS origin configuration:
```python
# In backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-vercel-subdomain.vercel.app"], # Replace with your Vercel deployment URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
Commit and push this change to GitHub. Render will automatically redeploy the backend with the new security boundaries.
