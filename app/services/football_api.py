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
        self.base_url = app_config.get("FOOTBALL_API_BASE_URL", "https://v3.football.api-sports.io")
        self.default_season = app_config.get("SEASON", "2026")

    def _get_headers(self):
        return {"x-apisports-key": self.api_key}

    def get_supported_leagues(self):
        return SUPPORTED_LEAGUES

    def _get(self, endpoint, params=None):
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=20)
            print(f"API CALL: {response.url} | STATUS: {response.status_code}")
            response.raise_for_status()
            return response.json()
        except Exception as error:
            print("API ERROR:", error)
            return {"response": []}

    def _format_fixture(self, item):
        fixture = item.get("fixture", {})
        league = item.get("league", {})
        teams = item.get("teams", {})
        goals = item.get("goals", {})
        status = fixture.get("status", {})
        venue = fixture.get("venue", {})

        return {
            "id": fixture.get("id"),
            "league": league.get("name", ""),
            "home_team": teams.get("home", {}).get("name", ""),
            "away_team": teams.get("away", {}).get("name", ""),
            "home_score": goals.get("home"),
            "away_score": goals.get("away"),
            "status": status.get("short", ""),
            "minute": status.get("elapsed") or 0,
            "date": fixture.get("date", ""),
            "stadium": venue.get("name", ""),
            "city": venue.get("city", ""),
            "round": league.get("round", "")
        }

    def get_all_live_matches(self):
        data = self._get("fixtures", {"live": "all"})
        response = data.get("response", [])
        matches = [self._format_fixture(item) for item in response]
        supported_ids = [l["id"] for l in SUPPORTED_LEAGUES.values()]
        filtered = [m for m in matches if any(r for r in response if r['fixture']['id'] == m['id'] and r['league']['id'] in supported_ids)]
        return sorted(filtered, key=lambda x: x.get("date", ""), reverse=True)

    def get_standings(self, league_key):
        if league_key not in SUPPORTED_LEAGUES: return []
        league = SUPPORTED_LEAGUES[league_key]
        season = league.get("season", self.default_season)
        data = self._get("standings", {"league": league["id"], "season": season})
        response = data.get("response", [])
        if not response: return []
        try:
            standings_data = response[0]["league"]["standings"]
            table = standings_data[0] if isinstance(standings_data[0], list) else standings_data
            return [{"position": t["rank"], "team": t["team"]["name"], "points": t["points"]} for t in table]
        except (KeyError, IndexError): return []

    def get_available_rounds(self, league_key="world-cup-2026"):
        league_id = SUPPORTED_LEAGUES[league_key]["id"]
        season = SUPPORTED_LEAGUES[league_key]["season"]
        data = self._get("fixtures/rounds", {"league": league_id, "season": season})
        return data.get("response", [])

    def get_matches_by_round(self, league_key, round_name):
        league_id = SUPPORTED_LEAGUES[league_key]["id"]
        season = SUPPORTED_LEAGUES[league_key]["season"]
        data = self._get("fixtures", {"league": league_id, "season": season, "round": round_name})
        return [self._format_fixture(item) for item in data.get("response", [])]

    def get_match_details(self, match_id):
        # Full detail implementation including stats and lineups
        fixture_data = self._get("fixtures", {"id": match_id})
        response = fixture_data.get("response", [])
        if not response: return None
        
        match = self._format_fixture(response[0])
        
        # Add Events, Lineups, Stats (Using the 'main' branch detailed logic)
        events_data = self._get("fixtures/events", {"fixture": match_id})
        lineups_data = self._get("fixtures/lineups", {"fixture": match_id})
        
        match["events"] = [{"minute": e.get("time", {}).get("elapsed"), "team": e.get("team", {}).get("name"), "player": e.get("player", {}).get("name"), "type": e.get("type")} for e in events_data.get("response", [])]
        
        match["lineups"] = {"home": [], "away": []}
        for lineup in lineups_data.get("response", []):
            side = "home" if lineup.get("team", {}).get("name") == match["home_team"] else "away"
            match["lineups"][side] = [p["player"].get("name") for p in lineup.get("startXI", [])]
            
        return match
