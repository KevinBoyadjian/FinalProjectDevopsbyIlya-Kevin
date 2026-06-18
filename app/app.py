from flask import Flask, render_template, request, jsonify

from config import Config
from services.football_api import FootballAPIService, SUPPORTED_LEAGUES


app = Flask(__name__)
app.config.from_object(Config)

football_service = FootballAPIService(app.config)


@app.route("/")
def index():
    selected_league = request.args.get("league", "world-cup-2026")
    selected_date = request.args.get("date")

    if selected_league not in SUPPORTED_LEAGUES:
        selected_league = "world-cup-2026"

    available_dates = []
    mode = "schedule"

    if selected_league == "world-cup-2026":
        available_dates = football_service.get_available_dates(selected_league)

        if not selected_date:
            if hasattr(football_service, "get_default_date"):
                selected_date = football_service.get_default_date(available_dates)
            elif available_dates:
                selected_date = available_dates[0]

        matches = football_service.get_matches_by_date(
            selected_league,
            selected_date
        )

    else:
        matches = football_service.get_live_matches(selected_league)
        mode = "live"

        if not matches:
            matches = football_service.get_upcoming_matches(selected_league)
            mode = "upcoming"

    return render_template(
        "index.html",
        matches=matches,
        selected_league=selected_league,
        selected_date=selected_date,
        available_dates=available_dates,
        mode=mode,
        leagues=SUPPORTED_LEAGUES
    )


@app.route("/match/<match_id>")
def match_details(match_id):
    selected_league = request.args.get("league", "world-cup-2026")
    selected_date = request.args.get("date")

    match = football_service.get_match_details(match_id)

    if match is None:
        return render_template(
            "match.html",
            match={
                "home_team": "Match",
                "away_team": "not found",
                "home_score": None,
                "away_score": None,
                "status": "N/A",
                "status_long": "Not available",
                "minute": 0,
                "date": "",
                "league": "",
                "stage": "",
                "referee": "",
                "stadium": "",
                "city": "",
                "home_logo": "",
                "away_logo": "",
                "score": {
                    "halftime": {"home": None, "away": None},
                    "fulltime": {"home": None, "away": None},
                    "extratime": {"home": None, "away": None},
                    "penalty": {"home": None, "away": None},
                },
                "events": [],
                "statistics": {"home": [], "away": []},
                "lineups": {"home": [], "away": []},
                "substitutes": {"home": [], "away": []},
                "formations": {"home": "", "away": ""},
                "coaches": {"home": "", "away": ""},
                "players": {"home": [], "away": []},
            },
            selected_league=selected_league,
            selected_date=selected_date
        ), 404

    return render_template(
        "match.html",
        match=match,
        selected_league=selected_league,
        selected_date=selected_date
    )


@app.route("/api/live/all")
def api_live_all():
    selected_league = request.args.get("league")

    if selected_league and selected_league in SUPPORTED_LEAGUES:
        matches = football_service.get_live_matches(selected_league)

        if not matches:
            matches = football_service.get_upcoming_matches(selected_league)

    else:
        matches = football_service.get_all_live_matches()

    return jsonify({
        "matches": matches
    })


@app.route("/api/matches")
def api_matches():
    selected_league = request.args.get("league", "world-cup-2026")
    selected_date = request.args.get("date")

    matches = football_service.get_matches_by_date(
        selected_league,
        selected_date
    )

    return jsonify({
        "matches": matches
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "ok"
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )