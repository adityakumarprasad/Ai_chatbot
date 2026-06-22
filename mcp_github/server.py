import os
import base64
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("GitHub Manager")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}" if GITHUB_TOKEN else "",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "FastMCP-Github-Server"
}

@mcp.tool()
async def search_repositories(query: str) -> str:
    """
    Search public and private GitHub repositories.
    Returns a list of repository names, descriptions, and URLs.
    """
    url = f"https://api.github.com/search/repositories?q={query}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=HEADERS)
        if r.status_code != 200:
            return f"Error: Failed to fetch repositories from GitHub. Status code: {r.status_code}. Response: {r.text}"
        
        items = r.json().get("items", [])
        if not items:
            return "No repositories found matching the query."
        
        results = []
        for item in items[:5]:
            results.append(f"- **{item['full_name']}**: {item['description'] or 'No description'} (URL: {item['html_url']})")
        return "\n".join(results)

@mcp.tool()
async def get_repository_details(owner: str, repo: str) -> str:
    """
    Get detailed information about a specific GitHub repository.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=HEADERS)
        if r.status_code != 200:
            return f"Error: Repository {owner}/{repo} not found or inaccessible."
        
        data = r.json()
        return (
            f"Repository: {data['full_name']}\n"
            f"Description: {data['description'] or 'No description'}\n"
            f"Stars: {data['stargazers_count']} | Forks: {data['forks_count']} | Open Issues: {data['open_issues_count']}\n"
            f"URL: {data['html_url']}\n"
            f"Primary Language: {data.get('language', 'Unknown')}"
        )

@mcp.tool()
async def list_issues(owner: str, repo: str, state: str = "open") -> str:
    """
    List issues in a GitHub repository.
    State can be 'open', 'closed', or 'all'.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/issues?state={state}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=HEADERS)
        if r.status_code != 200:
            return f"Error: Failed to list issues for {owner}/{repo}."
        
        issues = r.json()
        if not issues:
            return f"No {state} issues found for {owner}/{repo}."
        
        results = []
        for issue in issues[:10]:
            # Pull requests are returned in the issues API, check if it has pull_request key
            is_pr = "pull_request" in issue
            type_lbl = "PR" if is_pr else "Issue"
            results.append(f"- [{type_lbl} #{issue['number']}] {issue['title']} (State: {issue['state']}) - {issue['html_url']}")
        return "\n".join(results)

@mcp.tool()
async def create_issue(owner: str, repo: str, title: str, body: str = None) -> str:
    """
    Create a new issue in a GitHub repository.
    """
    if not GITHUB_TOKEN:
        return "Error: GITHUB_TOKEN environment variable is not configured. Cannot create issue."
    
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    payload = {"title": title}
    if body:
        payload["body"] = body
        
    async with httpx.AsyncClient() as client:
        r = await client.post(url, headers=HEADERS, json=payload)
        if r.status_code != 201:
            return f"Error: Failed to create issue. Status: {r.status_code}. Details: {r.text}"
        
        data = r.json()
        return f"Successfully created issue #{data['number']}: {data['title']}. View here: {data['html_url']}"

@mcp.tool()
async def get_file_content(owner: str, repo: str, path: str, ref: str = None) -> str:
    """
    Retrieve the text content of a file in a GitHub repository.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    if ref:
        url += f"?ref={ref}"
        
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=HEADERS)
        if r.status_code != 200:
            return f"Error: File '{path}' not found in {owner}/{repo}."
        
        data = r.json()
        if data.get("type") != "file":
            return f"Error: Path '{path}' is a {data.get('type')}, not a file."
        
        # Decode base64 contents
        content_b64 = data.get("content", "")
        try:
            content_decoded = base64.b64decode(content_b64.encode('utf-8')).decode('utf-8')
            return f"--- File: {owner}/{repo}/{path} ---\n{content_decoded}"
        except Exception as e:
            return f"Error: Failed to decode base64 file content: {str(e)}"

@mcp.tool()
async def create_or_update_file(
    owner: str, repo: str, path: str, content: str, message: str, branch: str = None
) -> str:
    """
    Create a new file or update an existing file in a GitHub repository.
    If the file exists, it automatically resolves its SHA and overrides it.
    """
    if not GITHUB_TOKEN:
        return "Error: GITHUB_TOKEN environment variable is not configured. Cannot commit file."
        
    # 1. Fetch file if exists to retrieve SHA
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    if branch:
        url += f"?ref={branch}"
        
    sha = None
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=HEADERS)
        if r.status_code == 200:
            # File exists, get SHA
            sha = r.json().get("sha")
            
    # 2. Base64 encode content
    content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    
    # 3. Create payload
    payload = {
        "message": message,
        "content": content_b64,
    }
    if sha:
        payload["sha"] = sha
    if branch:
        payload["branch"] = branch
        
    async with httpx.AsyncClient() as client:
        # Perform PUT request to create/update
        put_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        r = await client.put(put_url, headers=HEADERS, json=payload)
        if r.status_code in (200, 201):
            action = "updated" if sha else "created"
            data = r.json()
            return f"Successfully {action} file '{path}' in repository {owner}/{repo}. Commit SHA: {data['commit']['sha']}"
        else:
            return f"Error: Failed to commit file. Status: {r.status_code}. Response: {r.text}"

if __name__ == "__main__":
    mcp.run()
