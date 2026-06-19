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
        venue = fixture.get("venue", {})
        status = fixture.get("status", {})

        return {
            "id": fixture.get("id"),
            "league": league.get("name", ""),
            "league_id": league.get("id"),
            "season": league.get("season", ""),
            "round": league.get("round", ""),
            "stage": league.get("round", ""),
            "home_team": teams.get("home", {}).get("name", ""),
            "away_team": teams.get("away", {}).get("name", ""),
            "home_logo": teams.get("home", {}).get("logo", ""),
            "away_logo": teams.get("away", {}).get("logo", ""),
            "home_score": goals.get("home"),
            "away_score": goals.get("away"),
            "status": status.get("short", ""),
            "minute": status.get("elapsed") or 0,
            "date": fixture.get("date", ""),
            "stadium": venue.get("name", ""),
            "city": venue.get("city", ""),
        }

    def get_available_dates(self, league_key=None):
        start_date = date(2026, 6, 11)
        return [(start_date + timedelta(days=i)).isoformat() for i in range(0, 40)]

    def get_default_date(self, available_dates):
        today = date.today().isoformat()
        if today in available_dates: return today
        return available_dates[0] if available_dates else today

    def get_all_live_matches(self):
        data = self._get("fixtures", {"live": "all"})
        response = data.get("response", [])
        matches = [self._format_fixture(item) for item in response]
        supported_ids = [l["id"] for l in SUPPORTED_LEAGUES.values()]
        
        filtered = [m for m in matches if m["league_id"] in supported_ids]
        return sorted(filtered, key=lambda x: x.get("date", ""), reverse=True)

    def get_live_matches(self, league_key=None):
        all_live = self.get_all_live_matches()
        if not league_key: return all_live
        if league_key not in SUPPORTED_LEAGUES: return []
        
        target_league_name = SUPPORTED_LEAGUES[league_key]["name"]
        return [m for m in all_live if m["league"] == target_league_name]

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
        except (KeyError, IndexError):
            return []

    def get_available_rounds(self, league_key="world-cup-2026"):
        if not league_key or league_key not in SUPPORTED_LEAGUES: league_key = "world-cup-2026"
        league_id = SUPPORTED_LEAGUES[league_key]["id"]
        season = SUPPORTED_LEAGUES[league_key]["season"]
        data = self._get("fixtures/rounds", {"league": league_id, "season": season})
        return data.get("response", [])

    def get_matches_by_round(self, league_key, round_name):
        if not league_key or league_key not in SUPPORTED_LEAGUES: league_key = "world-cup-2026"
        league_id = SUPPORTED_LEAGUES[league_key]["id"]
        season = SUPPORTED_LEAGUES[league_key]["season"]
        data = self._get("fixtures", {"league": league_id, "season": season, "round": round_name})
        matches = [self._format_fixture(item) for item in data.get("response", [])]
        return sorted(matches, key=lambda x: x['date'])

    def get_matches_by_date(self, league_key=None, selected_date=None):
        if not selected_date: selected_date = date.today().isoformat()
        if not league_key: league_key = "world-cup-2026"
        league_info = SUPPORTED_LEAGUES[league_key]
        data = self._get("fixtures", {"league": league_info["id"], "season": league_info["season"], "date": selected_date})
        return [self._format_fixture(item) for item in data.get("response", [])]

    def get_match_details(self, match_id):
        fixture_data = self._get("fixtures", {"id": match_id})
        response = fixture_data.get("response", [])
        if not response: return None
        item = response[0]
        match = self._format_fixture(item)

        # Get Events, Lineups, and Stats
        events_data = self._get("fixtures/events", {"fixture": match_id})
        lineups_data = self._get("fixtures/lineups", {"fixture": match_id})
        statistics_data = self._get("fixtures/statistics", {"fixture": match_id})

        match["events"] = self._format_events(events_data.get("response", []))
        match["lineups"] = {"home": [], "away": []}
        self._attach_lineups(match, lineups_data.get("response", []))
        self._attach_statistics(match, statistics_data.get("response", []))

        return match

    def _format_events(self, events):
        return [{"minute": e.get("time", {}).get("elapsed"), "team": e.get("team", {}).get("name"), "player": e.get("player", {}).get("name"), "type": e.get("type"), "detail": e.get("detail")} for e in events or []]

    def _attach_lineups(self, match, lineups):
        for lineup in lineups or []:
            players = [p["player"].get("name") for p in lineup.get("startXI", [])]
            side = "home" if lineup.get("team", {}).get("name") == match["home_team"] else "away"
            match["lineups"][side] = players

    def _attach_statistics(self, match, statistics):
        match["statistics"] = {"home": [], "away": []}
        for stat in statistics or []:
            formatted = [{"type": s.get("type"), "value": s.get("value")} for s in stat.get("statistics", [])]
            side = "home" if stat.get("team", {}).get("name") == match["home_team"] else "away"
            match["statistics"][side] = formatted
