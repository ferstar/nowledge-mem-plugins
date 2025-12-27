"""Configuration management for Nowledge Mem"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Constants
DEFAULT_API_URL = "http://localhost:14243"
DEFAULT_TIMEOUT = 30.0
DEFAULT_TIMEOUT_HEALTH = 5.0
MIN_CONTENT_LENGTH = 5
MAX_CONTENT_LENGTH = 15000
VALID_SESSION_SOURCES = frozenset({"auto", "claude", "codex"})

SKILL_DIR = Path(__file__).parent.parent


class ConfigError(Exception):
    """Raised when configuration is invalid"""
    pass


@dataclass
class Config:
    """Unified configuration for Nowledge Mem

    Attributes:
        api_url: API endpoint URL
        auth_token: Bearer token for authentication (optional, omit header if empty)
        timeout: Default timeout for API requests
        timeout_health: Timeout for health check requests
        project_path: Project directory path (for persist command)
        max_messages: Maximum messages to extract (0 = unlimited)
        session_source: Session source hint (auto/claude/codex)
    """

    api_url: str
    auth_token: str
    timeout: float = field(default=DEFAULT_TIMEOUT)
    timeout_health: float = field(default=DEFAULT_TIMEOUT_HEALTH)
    project_path: Path | None = None
    max_messages: int = 0
    session_source: str = "auto"

    def __post_init__(self):
        """Validate configuration after initialization"""
        # auth_token is optional - when empty, no Authorization header is sent

        if self.max_messages < 0:
            object.__setattr__(self, "max_messages", 0)

        if self.session_source not in VALID_SESSION_SOURCES:
            object.__setattr__(self, "session_source", "auto")

        if self.timeout <= 0:
            object.__setattr__(self, "timeout", DEFAULT_TIMEOUT)

        if self.timeout_health <= 0:
            object.__setattr__(self, "timeout_health", DEFAULT_TIMEOUT_HEALTH)

    @classmethod
    def from_env(
        cls,
        project_path: str | None = None,
        session_source: str | None = None,
    ) -> "Config":
        """Load configuration from environment variables and .env file

        Priority (highest to lowest):
            1. Function arguments (from CLI)
            2. Existing environment variables
            3. Variables from .env file
        """
        # Load .env from skill directory first, then search parents
        skill_env = SKILL_DIR / ".env"
        if skill_env.exists():
            load_dotenv(dotenv_path=skill_env, override=False)
        else:
            load_dotenv(override=False)

        # Determine project path
        resolved_project_path = (
            Path(project_path)
            if project_path
            else Path(os.getenv("PROJECT_PATH", os.getcwd()))
        )

        # Determine session source
        resolved_session_source = (
            session_source
            or os.getenv("NOWLEDGE_MEM_SESSION_SOURCE", "auto").strip().lower()
            or "auto"
        )

        # Parse max_messages safely
        try:
            max_messages = int(os.getenv("NOWLEDGE_MEM_MAX_MESSAGES", "0"))
        except ValueError:
            max_messages = 0

        return cls(
            api_url=os.getenv("NOWLEDGE_MEM_API_URL", DEFAULT_API_URL),
            auth_token=os.getenv("NOWLEDGE_MEM_AUTH_TOKEN", "").strip(),
            timeout=float(os.getenv("NOWLEDGE_MEM_TIMEOUT", DEFAULT_TIMEOUT)),
            timeout_health=float(os.getenv("NOWLEDGE_MEM_TIMEOUT_HEALTH", DEFAULT_TIMEOUT_HEALTH)),
            project_path=resolved_project_path,
            max_messages=max_messages,
            session_source=resolved_session_source,
        )
