"""
BizMind AI — Modal Serverless Entry Point
Deploy this with: `modal deploy modal_app.py`
"""
import modal

app = modal.App("bizmind-backend")

# Define the serverless container image
image = (
    modal.Image.debian_slim(python_version="3.11")
    # Install dependencies straight from our existing pyproject.toml
    .pip_install_from_pyproject("pyproject.toml")
    # Pre-download the local HuggingFace embedding model into the image cache
    .run_commands(
        "python -c \"from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')\""
    )
)

# Run the FastAPI app on Modal, attaching the secret vault
@app.function(
    image=image, 
    secrets=[modal.Secret.from_name("bizmind-secrets", required=False)],
    keep_warm=1,  # Keeps 1 instance running to prevent cold starts (optional)
)
@modal.asgi_app()
def fastapi_app():
    # Import the FastAPI app inside the function so it loads within the Modal container
    from backend.main import app
    return app
