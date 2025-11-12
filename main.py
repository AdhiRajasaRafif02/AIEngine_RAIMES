"""Project entrypoint.

This is the main entry point that exposes the FastAPI app instance from src.api
for both uvicorn CLI and local development usage.
"""

from src.api_fastapi import app  # Import the main FastAPI app from src.api_fastapi


if __name__ == "__main__":
    """Run the application locally with uvicorn in development mode."""
    import uvicorn

    uvicorn.run("src.api_fastapi:app", host="127.0.0.1", port=8000, reload=True)
