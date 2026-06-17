import os

def load_dotenv():
    # Look for .env in multiple directories to support uvicorn and pytest environments
    for path in [".env", "../.env", "app/.env"]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, val = line.split("=", 1)
                        # Strip spaces and optional quotes
                        key = key.strip()
                        val = val.strip().strip("'\"")
                        # Only set if not already set by system environment (like Docker Compose/terminal)
                        if key not in os.environ:
                            os.environ[key] = val
            break

# Load variables
load_dotenv()

# Export configurations
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app/schedule.db")
DEBUG = os.getenv("DEBUG", "true").lower() in ("true", "1", "t", "yes")
