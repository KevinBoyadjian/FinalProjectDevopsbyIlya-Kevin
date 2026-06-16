import importlib.util
import os

if importlib.util.find_spec("dotenv") is not None:
    from dotenv import load_dotenv
else:
    def load_dotenv(dotenv_path=None):
        if dotenv_path is None:
            dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        try:
            with open(dotenv_path, "r") as env_file:
                for line in env_file:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = value
        except OSError:
            pass

load_dotenv()


class Config:
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "dev-secret-key"
    )

    # API-Sports
    FOOTBALL_API_KEY = os.getenv(
        "FOOTBALL_API_KEY",
        ""
    )

    FOOTBALL_API_BASE_URL = os.getenv(
        "FOOTBALL_API_BASE_URL",
        "https://v3.football.api-sports.io"
    )

    # Football-Data.org
    FOOTBALL_DATA_API_KEY = os.getenv(
        "FOOTBALL_DATA_API_KEY",
        ""
    )

    FOOTBALL_DATA_BASE_URL = os.getenv(
        "FOOTBALL_DATA_BASE_URL",
        "https://api.football-data.org/v4"
    )

    SEASON = os.getenv(
        "SEASON",
        "2026"
    )
