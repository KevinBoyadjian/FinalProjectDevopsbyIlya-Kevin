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
        self.worldcup_json_path = (
            Path(__file__).resolve().parents[1]
            / "data"
            / "world-cup-2026.json"
        )

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
            print("RESPONSE:", response.text[:500])
            print("===================================")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as error:
            print("API HTTP ERROR:", error)
            return {"response": []}

        except requests.exceptions.RequestException as error:
            print("API REQUEST ERROR:", error)
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
            "stadium": item["fixture"]["venue"]["name"]
            if item["fixture"].get("venue")
            else "",
            "city": item["fixture"]["venue"]["city"]
            if item["fixture"].get("venue")
            else "",
            "stage": item["league"].get("round", ""),
            "events": [],
            "lineups": {
                "home": [],
                "away": [],
            },
        }

    def _format_worldcup_match(self, item):
        return {
            "id": item.get("id"),
            "league": item.get("league", "FIFA World Cup 2026"),
            "home_team": item.get("home_team", "TBD"),
            "away_team": item.get("away_team", "TBD"),
            "home_score": item.get("home_score"),
            "away_score": item.get("away_score"),
            "status": item.get("status", "NS"),
            "minute": item.get("minute", 0),
            "date": item.get("date", ""),
            "stadium": item.get("stadium", ""),
            "city": item.get("city", ""),
            "group": item.get("group", ""),
            "stage": item.get("stage", "Group Stage"),
            "source": item.get("source", "FIFA official schedule"),
            "events": item.get("events", []),
            "lineups": item.get(
                "lineups",
                {
                    "home": [],
                    "away": [],
                },
            ),
        }

    def _load_worldcup_json(self):
        if not self.worldcup_json_path.exists():
            print(f"WORLD CUP JSON NOT FOUND: {self.worldcup_json_path}")
            return []

        try:
            with open(self.worldcup_json_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            matches = data.get("matches", [])

            formatted_matches = [
                self._format_worldcup_match(match)
                for match in matches
            ]

            return sorted(
                formatted_matches,
                key=lambda match: match.get("date", ""),
            )

        except json.JSONDecodeError as error:
            print("WORLD CUP JSON ERROR: invalid JSON format")
            print(error)
            return []

        except OSError as error:
            print("WORLD CUP JSON ERROR: cannot read file")
            print(error)
            return []

    def _get_league_ids(self, league_key):
        if league_key and league_key in SUPPORTED_LEAGUES:
            league = SUPPORTED_LEAGUES[league_key]

            if league.get("source") == "local-json":
                return []

            return [league["id"]]

        return [
            league["id"]
            for league in SUPPORTED_LEAGUES.values()
            if league.get("source") == "api-football"
        ]

    def _get_league_season(self, league_key):
        if league_key and league_key in SUPPORTED_LEAGUES:
            return SUPPORTED_LEAGUES[league_key].get(
                "season",
                self.default_season,
            )

        return self.default_season

    def get_available_dates(self, league_key=None):
        if league_key == "world-cup-2026":
            matches = self._load_worldcup_json()

            dates = sorted(
                {
                    match.get("date", "")[:10]
                    for match in matches
                    if match.get("date")
                }
            )

            return dates

        today = date.today()

        return [
            (today + timedelta(days=day_offset)).isoformat()
            for day_offset in range(0, 14)
        ]

    def get_default_date(self, available_dates):
        today = date.today().isoformat()

        if today in available_dates:
            return today

        future_dates = [
            available_date
            for available_date in available_dates
            if available_date >= today
        ]

        if future_dates:
            return future_dates[0]

        if available_dates:
            return available_dates[-1]

        return today

    def get_live_matches(self, league_key=None):
        if league_key == "world-cup-2026":
            matches = self._load_worldcup_json()
            live_statuses = [
                "1H",
                "HT",
                "2H",
                "ET",
                "BT",
                "P",
                "SUSP",
                "INT",
                "LIVE",
            ]

            return [
                match
                for match in matches
                if match.get("status") in live_statuses
            ]

        league_ids = self._get_league_ids(league_key)
        matches = []

        for league_id in league_ids:
            data = self._get(
                "fixtures",
                {
                    "live": "all",
                    "league": league_id,
                },
            )

            matches.extend(
                [
                    self._format_fixture(item)
                    for item in data.get("response", [])
                ]
            )

        return matches
    
    def get_all_live_matches(self):
        """
        Fetch ALL live matches from the Pro API (including World Cup 2026).
        """
        data = self._get(
        "fixtures",
        {
            "live": "all",
        },
    )

        matches = [
            self._format_fixture(item)
        for item in data.get("response", [])
    ]

        print(f"DEBUG: Total live matches returned by Pro API: {len(matches)}")
    
        if matches:
            leagues = list(set([m['league'] for m in matches]))
        print(f"DEBUG: Leagues found: {leagues}")

        return sorted(
            matches,
            key=lambda match: match.get("date", ""),
            reverse=True,
    )


    def get_matches_by_date(self, league_key=None, selected_date=None):
        if not selected_date:
            selected_date = date.today().isoformat()

        if league_key == "world-cup-2026":
            matches = self._load_worldcup_json()

            return [
                match
                for match in matches
                if match.get("date", "").startswith(selected_date)
            ]

        league_ids = self._get_league_ids(league_key)
        season = self._get_league_season(league_key)
        matches = []

        for league_id in league_ids:
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

        return matches

    def get_upcoming_matches(self, league_key=None, limit=10):
        if league_key == "world-cup-2026":
            matches = self._load_worldcup_json()
            today = date.today().isoformat()
            upcoming_statuses = ["NS", "TBD", "PST"]

            upcoming_matches = [
                match
                for match in matches
                if match.get("status") in upcoming_statuses
                and match.get("date", "")[:10] >= today
            ]

            return upcoming_matches[:limit]

        league_ids = self._get_league_ids(league_key)
        matches = []
        today = date.today()
        season = self._get_league_season(league_key)

        for league_id in league_ids:
            for day_offset in range(0, 14):
                match_date = today + timedelta(days=day_offset)

                data = self._get(
                    "fixtures",
                    {
                        "league": league_id,
                        "season": season,
                        "date": match_date.isoformat(),
                    },
                )

                matches.extend(
                    [
                        self._format_fixture(item)
                        for item in data.get("response", [])
                    ]
                )

                if len(matches) >= limit:
                    return matches[:limit]

        return matches[:limit]

    def get_match_details(self, match_id):
        worldcup_matches = self._load_worldcup_json()

        for match in worldcup_matches:
            if str(match.get("id")) == str(match_id):
                return match

        data = self._get("fixtures", {"id": match_id})
        response = data.get("response", [])

        if not response:
            return None

        item = response[0]

        events_data = self._get(
            "fixtures/events",
            {"fixture": match_id},
        ).get("response", [])

        lineups_data = self._get(
            "fixtures/lineups",
            {"fixture": match_id},
        ).get("response", [])

        home_name = item["teams"]["home"]["name"]
        away_name = item["teams"]["away"]["name"]

        events = []

        for event in events_data:
            events.append(
                {
                    "minute": event.get("time", {}).get("elapsed", 0),
                    "team": event.get("team", {}).get("name", ""),
                    "type": event.get("type", ""),
                    "player": event.get("player", {}).get("name", ""),
                }
            )

        home_lineup = []
        away_lineup = []

        for lineup in lineups_data:
            team_name = lineup.get("team", {}).get("name", "")

            players = [
                player["player"].get("name", "")
                for player in lineup.get("startXI", [])
                if player.get("player")
            ]

            if team_name == home_name:
                home_lineup = players
            elif team_name == away_name:
                away_lineup = players

        match = self._format_fixture(item)
        match["events"] = events
        match["lineups"] = {
            "home": home_lineup,
            "away": away_lineup,
        }

        return match

    def get_standings(self, league_key="premier-league"):
        if league_key == "world-cup-2026":
            return []

        league = SUPPORTED_LEAGUES.get(
            league_key,
            SUPPORTED_LEAGUES["premier-league"],
        )

        season = league.get("season", self.default_season)

        data = self._get(
            "standings",
            {
                "league": league["id"],
                "season": season,
            },
        )

        response = data.get("response", [])

        if not response:
            return []

        table = response[0]["league"]["standings"][0]

        return [
            {
                "position": team["rank"],
                "team": team["team"]["name"],
                "points": team["points"],
            }
            for team in table
        ]
