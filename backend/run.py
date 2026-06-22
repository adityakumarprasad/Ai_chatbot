import uvicorn
from dotenv import load_dotenv

if __name__ == "__main__":
    # Load environment variables from .env
    load_dotenv()
    # Run the uvicorn development server
    # 'backend.app.main:app' maps to backend/app/main.py -> app object
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
