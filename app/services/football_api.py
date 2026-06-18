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
            "country": league.get("country", ""),
            "round": league.get("round", ""),
            "stage": league.get("round", ""),
            "home_team": teams.get("home", {}).get("name", ""),
            "away_team": teams.get("away", {}).get("name", ""),
            "home_logo": teams.get("home", {}).get("logo", ""),
            "away_logo": teams.get("away", {}).get("logo", ""),
            "home_winner": teams.get("home", {}).get("winner"),
            "away_winner": teams.get("away", {}).get("winner"),
            "home_score": goals.get("home"),
            "away_score": goals.get("away"),
            "status": status.get("short", ""),
            "status_long": status.get("long", ""),
            "minute": status.get("elapsed") or 0,
            "date": fixture.get("date", ""),
            "timestamp": fixture.get("timestamp", ""),
            "timezone": fixture.get("timezone", ""),
            "referee": fixture.get("referee", ""),
            "stadium": venue.get("name", ""),
            "city": venue.get("city", ""),
        }

    def get_available_dates(self, league_key=None):
        start_date = date(2026, 6, 11)
        return [
            (start_date + timedelta(days=i)).isoformat()
            for i in range(0, 40)
        ]

    def get_default_date(self, available_dates):
        today = date.today().isoformat()

        if today in available_dates:
            return today

        return available_dates[0] if available_dates else today

    def get_all_live_matches(self):
        data = self._get("fixtures", {"live": "all"})
        response = data.get("response", [])

        matches = [self._format_fixture(item) for item in response]
        supported_ids = [league["id"] for league in SUPPORTED_LEAGUES.values()]

        filtered = [
            match
            for match in matches
            if any(
                item.get("fixture", {}).get("id") == match["id"]
                and item.get("league", {}).get("id") in supported_ids
                for item in response
            )
        ]

        return sorted(filtered, key=lambda x: x.get("date", ""), reverse=True)

    def get_live_matches(self, league_key=None):
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

        table = response[0].get("league", {}).get("standings", [[]])[0]

        return [
            {
                "position": team.get("rank"),
                "team": team.get("team", {}).get("name", ""),
                "points": team.get("points", 0)
            }
            for team in table
        ]
    
        # --- ADD THE TWO NEW FUNCTIONS HERE ---
    def get_available_rounds(self, league_key="world-cup-2026"):
        """Fetch all matchdays/rounds for a league (e.g. Group Stage - 1)"""
        # Safety check: Default to World Cup if league_key is not provided or invalid
        if not league_key or league_key not in SUPPORTED_LEAGUES:
            league_key = "world-cup-2026"

        league_id = SUPPORTED_LEAGUES[league_key]["id"]
        season = SUPPORTED_LEAGUES[league_key]["season"]
        
        data = self._get("fixtures/rounds", {"league": league_id, "season": season})
        return data.get("response", [])

    def get_matches_by_round(self, league_key, round_name):
        """Fetch all matches for a specific Game Week / Round"""
        # Safety check: Default to World Cup if league_key is not provided or invalid
        if not league_key or league_key not in SUPPORTED_LEAGUES:
            league_key = "world-cup-2026"
        
        league_id = SUPPORTED_LEAGUES[league_key]["id"]
        season = SUPPORTED_LEAGUES[league_key]["season"]

        data = self._get("fixtures", {
            "league": league_id,
            "season": season,
            "round": round_name
        })
        matches = [self._format_fixture(item) for item in data.get("response", [])]
        return sorted(matches, key=lambda x: x['date']) # Sort by date for chronological order

    def get_matches_by_date(self, league_key=None, selected_date=None):
        if not selected_date:
            selected_date = date.today().isoformat()

        if not league_key:
            league_key = "world-cup-2026"

        if league_key not in SUPPORTED_LEAGUES:
            print(f"DEBUG: League {league_key} not found, defaulting to World Cup")
            league_key = "world-cup-2026"

        league_info = SUPPORTED_LEAGUES[league_key]

        data = self._get("fixtures", {
            "league": league_info["id"],
            "season": league_info["season"],
            "date": selected_date
        })

        return [
            self._format_fixture(item)
            for item in data.get("response", [])
        ]

    def get_upcoming_matches(self, league_key=None):
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

    def get_match_details(self, match_id):
        fixture_data = self._get("fixtures", {"id": match_id})
        fixture_response = fixture_data.get("response", [])

        if not fixture_response:
            return None

        item = fixture_response[0]
        match = self._format_fixture(item)

        score = item.get("score", {})

        match["score"] = {
            "halftime": score.get("halftime", {}),
            "fulltime": score.get("fulltime", {}),
            "extratime": score.get("extratime", {}),
            "penalty": score.get("penalty", {}),
        }

        events_data = self._get("fixtures/events", {"fixture": match_id})
        lineups_data = self._get("fixtures/lineups", {"fixture": match_id})
        statistics_data = self._get("fixtures/statistics", {"fixture": match_id})
        players_data = self._get("fixtures/players", {"fixture": match_id})

        match["events"] = self._format_events(events_data.get("response", []))
        match["lineups"] = {"home": [], "away": []}
        match["substitutes"] = {"home": [], "away": []}
        match["formations"] = {"home": "", "away": ""}
        match["coaches"] = {"home": "", "away": ""}
        match["statistics"] = {"home": [], "away": []}
        match["players"] = {"home": [], "away": []}

        self._attach_lineups(match, lineups_data.get("response", []))
        self._attach_statistics(match, statistics_data.get("response", []))
        self._attach_players(match, players_data.get("response", []))

        return match

    def _format_events(self, events):
        formatted_events = []

        for event in events or []:
            formatted_events.append({
                "minute": event.get("time", {}).get("elapsed"),
                "extra_minute": event.get("time", {}).get("extra"),
                "team": event.get("team", {}).get("name", ""),
                "team_logo": event.get("team", {}).get("logo", ""),
                "player": event.get("player", {}).get("name", ""),
                "assist": event.get("assist", {}).get("name", ""),
                "type": event.get("type", ""),
                "detail": event.get("detail", ""),
                "comments": event.get("comments", "")
            })

        return formatted_events

    def _format_lineup_player(self, player_item):
        player = player_item.get("player", {})

        return {
            "id": player.get("id"),
            "name": player.get("name", ""),
            "number": player.get("number", ""),
            "position": player.get("pos", ""),
            "grid": player.get("grid", "")
        }

    def _attach_lineups(self, match, lineups):
        for lineup in lineups or []:
            team_name = lineup.get("team", {}).get("name", "")

            starting_players = [
                self._format_lineup_player(player_item)
                for player_item in lineup.get("startXI", [])
            ]

            substitute_players = [
                self._format_lineup_player(player_item)
                for player_item in lineup.get("substitutes", [])
            ]

            if team_name == match["home_team"]:
                side = "home"
            elif team_name == match["away_team"]:
                side = "away"
            else:
                continue

            match["lineups"][side] = starting_players
            match["substitutes"][side] = substitute_players
            match["formations"][side] = lineup.get("formation", "")
            match["coaches"][side] = lineup.get("coach", {}).get("name", "")

    def _attach_statistics(self, match, statistics):
        for stat in statistics or []:
            team_name = stat.get("team", {}).get("name", "")

            formatted_stats = [
                {
                    "type": item.get("type", ""),
                    "value": item.get("value", "")
                }
                for item in stat.get("statistics", [])
            ]

            if team_name == match["home_team"]:
                match["statistics"]["home"] = formatted_stats
            elif team_name == match["away_team"]:
                match["statistics"]["away"] = formatted_stats

    def _format_player_stats(self, player_item):
        player = player_item.get("player", {})
        stats_list = player_item.get("statistics", [])
        stats = stats_list[0] if stats_list else {}

        return {
            "id": player.get("id"),
            "name": player.get("name", ""),
            "photo": player.get("photo", ""),
            "number": stats.get("games", {}).get("number", ""),
            "position": stats.get("games", {}).get("position", ""),
            "rating": stats.get("games", {}).get("rating", ""),
            "minutes": stats.get("games", {}).get("minutes", 0),
            "captain": stats.get("games", {}).get("captain", False),
            "substitute": stats.get("games", {}).get("substitute", False),
            "goals": stats.get("goals", {}).get("total", 0),
            "assists": stats.get("goals", {}).get("assists", 0),
            "saves": stats.get("goals", {}).get("saves", 0),
            "fouls_drawn": stats.get("fouls", {}).get("drawn", 0),
            "fouls_committed": stats.get("fouls", {}).get("committed", 0),
            "yellow_cards": stats.get("cards", {}).get("yellow", 0),
            "red_cards": stats.get("cards", {}).get("red", 0),
        }

    def _attach_players(self, match, players_data):
        for team_players in players_data or []:
            team_name = team_players.get("team", {}).get("name", "")

            formatted_players = [
                self._format_player_stats(player_item)
                for player_item in team_players.get("players", [])
            ]

            if team_name == match["home_team"]:
                match["players"]["home"] = formatted_players
            elif team_name == match["away_team"]:
                match["players"]["away"] = formatted_players