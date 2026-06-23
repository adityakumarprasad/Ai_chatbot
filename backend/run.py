import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the workspace root to sys.path so 'backend' package imports work correctly
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import uvicorn

if __name__ == "__main__":
    # Load environment variables from .env
    load_dotenv()
    
    # Read dynamic PORT (default 8000) and ENV (default development) for production cloud runners
    port = int(os.environ.get("PORT", 8000))
    env = os.environ.get("ENV", "development")
    reload = env == "development"
    
    # Run the uvicorn server
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port, reload=reload)
