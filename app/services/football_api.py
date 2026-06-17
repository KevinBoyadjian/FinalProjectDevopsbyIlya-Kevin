from datetime import date, timedelta
from pathlib import Path
import json
import requests

SUPPORTED_LEAGUES = {
    "premier-league": {
        "id": 39,
        "name": "Premier League",
        "season": "2025",
        "source": "api-football",
    },
    "la-liga": {
        "id": 140,
        "name": "La Liga",
        "season": "2025",
        "source": "api-football",
    },
    "serie-a": {
        "id": 135,
        "name": "Serie A",
        "season": "2025",
        "source": "api-football",
    },
    "ligue-1": {
        "id": 61,
        "name": "Ligue 1",
        "season": "2025",
        "source": "api-football",
    },
    "bundesliga": {
        "id": 78,
        "name": "Bundesliga",
        "season": "2025",
        "source": "api-football",
    },
    "champions-league": {
        "id": 2,
        "name": "Champions League",
        "season": "2025",
        "source": "api-football",
    },
    "world-cup-2026": {
        "id": 1,
        "name": "FIFA World Cup 2026",
        "season": "2026",
        "source": "api-football",
    },
}

class FootballAPIService:
    def __init__(self, app_config):
        self.api_key = app_config.get("FOOTBALL_API_KEY", "")
        self.base_url = app_config.get(
            "FOOTBALL_API_BASE_URL",
            "https://v3.football.api-sports.io",
        )
        self.default_season = app_config.get("SEASON", "2026")

    def get_supported_leagues(self):
        return SUPPORTED_LEAGUES

    def _get_headers(self):
        return {
            "x-apisports-key": self.api_key,
        }

    def _get(self, endpoint, params=None):
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=20,
            )
            print("===================================")
            print("URL:", response.url)
            print("STATUS:", response.status_code)
            print("===================================")
            response.raise_for_status()
            return response.json()
        except Exception as error:
            print("API ERROR:", error)
            return {"response": []}

    def _format_fixture(self, item):
        return {
            "id": item["fixture"]["id"],
            "league": item["league"]["name"],
            "home_team": item["teams"]["home"]["name"],
            "away_team": item["teams"]["away"]["name"],
            "home_score": item["goals"]["home"],
            "away_score": item["goals"]["away"],
            "status": item["fixture"]["status"]["short"],
            "minute": item["fixture"]["status"]["elapsed"] or 0,
            "date": item["fixture"]["date"],
            "stadium": item["fixture"]["venue"]["name"] if item["fixture"].get("venue") else "",
            "city": item["fixture"]["venue"]["city"] if item["fixture"].get("venue") else "",
            "stage": item["league"].get("round", ""),
            "events": [],
            "lineups": {"home": [], "away": []},
        }

    def _get_league_ids(self, league_key):
        if league_key and league_key in SUPPORTED_LEAGUES:
            return [SUPPORTED_LEAGUES[league_key]["id"]]
        return [l["id"] for l in SUPPORTED_LEAGUES.values() if l.get("source") == "api-football"]

    def _get_league_season(self, league_key):
        if league_key and league_key in SUPPORTED_LEAGUES:
            return SUPPORTED_LEAGUES[league_key].get("season", self.default_season)
        return self.default_season

    def get_available_dates(self, league_key=None):
        # Start from June 11th (Tournament Start) until the end of the tournament
        start_date = date(2026, 6, 11)
        # Create a list of 40 days to cover the whole tournament
        return [(start_date + timedelta(days=i)).isoformat() for i in range(0, 40)]

    def get_default_date(self, available_dates):
        today = date.today().isoformat()
        if today in available_dates: return today
        return available_dates[0] if available_dates else today

    def get_live_matches(self, league_key=None):
        league_ids = self._get_league_ids(league_key)
        matches = []
        for league_id in league_ids:
            data = self._get("fixtures", {"live": "all", "league": league_id})
            matches.extend([self._format_fixture(item) for item in data.get("response", [])])
        return matches
    
    def get_all_live_matches(self):
        data = self._get("fixtures", {"live": "all"})
        matches = [self._format_fixture(item) for item in data.get("response", [])]
        print(f"DEBUG: Total live matches: {len(matches)}")
        return sorted(matches, key=lambda x: x.get("date", ""), reverse=True)

    
    def get_upcoming_matches(self, league_key=None, limit=10):
        league_ids = self._get_league_ids(league_key)
        season = self._get_league_season(league_key)
        matches = []
        data = self._get("fixtures", {"league": league_ids[0], "season": season, "next": limit})
        matches.extend([self._format_fixture(item) for item in data.get("response", [])])
        return matches[:limit]

    def get_match_details(self, match_id):
        data = self._get("fixtures", {"id": match_id})
        response = data.get("response", [])
        if not response: return None
        item = response[0]
        match = self._format_fixture(item)
        return match

    def get_standings(self, league_key="premier-league"):
        league = SUPPORTED_LEAGUES.get(league_key, SUPPORTED_LEAGUES["premier-league"])
        season = league.get("season", self.default_season)
        data = self._get("standings", {"league": league["id"], "season": season})
        response = data.get("response", [])
        if not response: return []
        table = response[0]["league"]["standings"][0]
        return [{"position": t["rank"], "team": t["team"]["name"], "points": t["points"]} for t in table]

    def get_matches_by_date(self, league_key=None, selected_date=None):
        if not selected_date:
            selected_date = date.today().isoformat()

        league_ids = self._get_league_ids(league_key)
        season = self._get_league_season(league_key)
        matches = []

        for league_id in league_ids:
            # This calls the Pro API for the specific date
            data = self._get(
                "fixtures",
                {
                    "league": league_id,
                    "season": season,
                    "date": selected_date,
                },
            )

            matches.extend(
                [
                    self._format_fixture(item)
                    for item in data.get("response", [])
                ]
            )

        # Sort matches by time
        return sorted(matches, key=lambda x: x.get("date", ""))
