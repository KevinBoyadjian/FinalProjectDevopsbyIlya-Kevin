from datetime import date, timedelta
import requests

SUPPORTED_LEAGUES = {
    "premier-league": {"id": 39, "name": "Premier League", "season": "2025"},
    "la-liga": {"id": 140, "name": "La Liga", "season": "2025"},
    "serie-a": {"id": 135, "name": "Serie A", "season": "2025"},
    "ligue-1": {"id": 61, "name": "Ligue 1", "season": "2025"},
    "bundesliga": {"id": 78, "name": "Bundesliga", "season": "2025"},
    "champions-league": {"id": 2, "name": "Champions League", "season": "2025"},
    "world-cup-2026": {"id": 1, "name": "FIFA World Cup 2026", "season": "2026"},
}


class FootballAPIService:
    def __init__(self, app_config):
        self.api_key = app_config.get("FOOTBALL_API_KEY", "")
        self.base_url = app_config.get(
            "FOOTBALL_API_BASE_URL",
            "https://v3.football.api-sports.io"
        )
        self.default_season = app_config.get("SEASON", "2026")

    def _get_headers(self):
        return {"x-apisports-key": self.api_key}

    def get_supported_leagues(self):
        return SUPPORTED_LEAGUES

    def _get(self, endpoint, params=None):
        url = f"{self.base_url}/{endpoint}"

        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=20
            )

            print(f"API CALL: {response.url} | STATUS: {response.status_code}")

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
            "stadium": item["fixture"].get("venue", {}).get("name", ""),
            "city": item["fixture"].get("venue", {}).get("city", ""),
            "stage": item["league"].get("round", "")
        }

    def get_available_dates(self, league_key=None):
        start_date = date(2026, 6, 11)
        return [
            (start_date + timedelta(days=i)).isoformat()
            for i in range(0, 40)
        ]

    def get_all_live_matches(self):
        """OPTIMIZED: One API call for everything live"""
        data = self._get("fixtures", {"live": "all"})
        response = data.get("response", [])

        matches = [self._format_fixture(item) for item in response]

        supported_ids = [league["id"] for league in SUPPORTED_LEAGUES.values()]

        filtered = [
            match
            for match in matches
            if any(
                item["fixture"]["id"] == match["id"]
                and item["league"]["id"] in supported_ids
                for item in response
            )
        ]

        return sorted(filtered, key=lambda x: x.get("date", ""), reverse=True)

    def get_live_matches(self, league_key=None):
        """OPTIMIZED: Use the all-live list and filter in memory"""
        all_live = self.get_all_live_matches()

        if not league_key:
            return all_live

        if league_key not in SUPPORTED_LEAGUES:
            return []

        target_league_name = SUPPORTED_LEAGUES[league_key]["name"]

        return [
            match
            for match in all_live
            if match["league"] == target_league_name
        ]

    def get_standings(self, league_key):
        if league_key not in SUPPORTED_LEAGUES:
            return []

        league = SUPPORTED_LEAGUES[league_key]
        season = league.get("season", self.default_season)

        data = self._get("standings", {
            "league": league["id"],
            "season": season
        })

        response = data.get("response", [])

        if not response:
            return []

        table = response[0]["league"]["standings"][0]

        return [
            {
                "position": team["rank"],
                "team": team["team"]["name"],
                "points": team["points"]
            }
            for team in table
        ]

    def get_matches_by_date(self, league_key=None, selected_date=None):
        if not selected_date:
            selected_date = date.today().isoformat()

        if not league_key:
            league_key = "world-cup-2026"

        if league_key not in SUPPORTED_LEAGUES:
            print(f"DEBUG: League {league_key} not found, defaulting to World Cup")
            league_key = "world-cup-2026"

        league_info = SUPPORTED_LEAGUES[league_key]
        league_id = league_info["id"]
        season = league_info["season"]

        data = self._get("fixtures", {
            "league": league_id,
            "season": season,
            "date": selected_date
        })

        return [
            self._format_fixture(item)
            for item in data.get("response", [])
        ]

    def get_match_details(self, match_id):
        """
        Get full details for one match.
        Used by route: /match/<match_id>
        """
        data = self._get("fixtures", {"id": match_id})
        response = data.get("response", [])

        if not response:
            return None

        item = response[0]
        match = self._format_fixture(item)

        match["events"] = []

        for event in item.get("events", []) or []:
            match["events"].append({
                "minute": event.get("time", {}).get("elapsed"),
                "extra_minute": event.get("time", {}).get("extra"),
                "team": event.get("team", {}).get("name", ""),
                "player": event.get("player", {}).get("name", ""),
                "assist": event.get("assist", {}).get("name", ""),
                "type": event.get("type", ""),
                "detail": event.get("detail", ""),
                "comments": event.get("comments", "")
            })

        match["lineups"] = {
            "home": [],
            "away": []
        }

        for lineup in item.get("lineups", []) or []:
            team_name = lineup.get("team", {}).get("name", "")

            players = [
                player_item.get("player", {}).get("name", "")
                for player_item in lineup.get("startXI", [])
            ]

            if team_name == match["home_team"]:
                match["lineups"]["home"] = players

            elif team_name == match["away_team"]:
                match["lineups"]["away"] = players

        match["statistics"] = {
            "home": [],
            "away": []
        }

        for stat in item.get("statistics", []) or []:
            team_name = stat.get("team", {}).get("name", "")
            stats = stat.get("statistics", [])

            formatted_stats = [
                {
                    "type": s.get("type", ""),
                    "value": s.get("value", "")
                }
                for s in stats
            ]

            if team_name == match["home_team"]:
                match["statistics"]["home"] = formatted_stats

            elif team_name == match["away_team"]:
                match["statistics"]["away"] = formatted_stats

        return match

    def get_upcoming_matches(self, league_key=None):
        """
        Get upcoming matches.
        Used when there are no live matches.
        """
        if not league_key:
            league_key = "world-cup-2026"

        if league_key not in SUPPORTED_LEAGUES:
            return []

        league = SUPPORTED_LEAGUES[league_key]

        data = self._get("fixtures", {
            "league": league["id"],
            "season": league["season"],
            "next": 10
        })

        return [
            self._format_fixture(item)
            for item in data.get("response", [])
        ]