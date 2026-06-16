import os

from dotenv import load_dotenv


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
