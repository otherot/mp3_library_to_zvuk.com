"""
Configuration module for the application
"""

from pathlib import Path


class Config:
    """Application configuration"""

    def __init__(self, token: str, library_path: str | Path):
        """
        Initialize configuration

        Args:
            token: Zvuk.com API token
            library_path: Path to local MP3 library
        """
        self.zvuk_api_token = token
        self.library_path = Path(library_path)

        if not self.library_path.exists():
            raise ValueError(f"Library path does not exist: {self.library_path}")

    @property
    def api_headers(self) -> dict:
        """Headers for API requests"""
        return {
            "Authorization": f"Bearer {self.zvuk_api_token}",
            "Content-Type": "application/json"
        }
