"""Server entry point for OpenEnv deployment."""
import os
import uvicorn
from src.main import app


def main():
    """Main entry point."""
    port = int(os.getenv("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()

