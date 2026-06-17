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
        # Your excellent tournament calendar logic
        start_date = date(2026, 6, 11)
        return [(start_date + timedelta(days=i)).isoformat() for i in range(0, 40)]

    def get_all_live_matches(self):
        """OPTIMIZED: One API call for everything live"""
        data = self._get("fixtures", {"live": "all"})
        matches = [self._format_fixture(item) for item in data.get("response", [])]
        
        # Only return matches belonging to our supported leagues
        supported_ids = [l["id"] for l in SUPPORTED_LEAGUES.values()]
        filtered = [m for m in matches if any(match_item for match_item in data.get("response", []) if match_item['fixture']['id'] == m['id'] and match_item['league']['id'] in supported_ids)]
        
        return sorted(filtered, key=lambda x: x.get("date", ""), reverse=True)

    def get_live_matches(self, league_key=None):
        """OPTIMIZED: Use the all-live list and filter in memory"""
        all_live = self.get_all_live_matches()
        if not league_key: return all_live
        
        target_league_name = SUPPORTED_LEAGUES[league_key]["name"]
        return [m for m in all_live if m["league"] == target_league_name]

    def get_standings(self, league_key):
        if league_key not in SUPPORTED_LEAGUES: return []
        league = SUPPORTED_LEAGUES[league_key]
        season = league.get("season", self.default_season)
        
        data = self._get("standings", {"league": league["id"], "season": season})
        response = data.get("response", [])
        if not response: return []
        
        table = response[0]["league"]["standings"][0]
        return [{"position": t["rank"], "team": t["team"]["name"], "points": t["points"]} for t in table]

    def get_matches_by_date(self, league_key, selected_date):
        league_id = SUPPORTED_LEAGUES[league_key]["id"]
        season = SUPPORTED_LEAGUES[league_key]["season"]
        data = self._get("fixtures", {"league": league_id, "season": season, "date": selected_date})
        return [self._format_fixture(item) for item in data.get("response", [])]
