import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # GitHub Configuration
    GITHUB_PAT = os.getenv("GITHUB_PAT", "")
    GITHUB_REPO_OWNER = os.getenv("GITHUB_REPO_OWNER", "")
    GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME", "")

    # Ollama Configuration
    OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "ministral-3:3b")

    # Agent Configuration
    AGENT_MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITERATIONS", "5"))
    AGENT_TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", "0.3"))

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.GITHUB_PAT:
            raise ValueError("GITHUB_PAT not set in .env")
        if not cls.GITHUB_REPO_OWNER or not cls.GITHUB_REPO_NAME:
            raise ValueError(
                "GITHUB_REPO_OWNER and GITHUB_REPO_NAME must be set in .env")


settings = Settings()
