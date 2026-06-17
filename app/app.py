from flask import Flask, jsonify, render_template, request

from config import Config
from services.football_api import FootballAPIService

app = Flask(__name__)
app.config.from_object(Config)

football_service = FootballAPIService(app.config)


@app.route("/health")
def health_check():
    """
    Health check endpoint for Kubernetes liveness and readiness probes.
    Returns 200 OK to indicate that the container is running.
    """
    return "OK", 200


@app.route("/")
def index():
    league = request.args.get("league")
    selected_date = request.args.get("date")

    matches = []
    mode = None
    available_dates = []

    if league == "world-cup-2026":
    # This will now fetch from your Pro API since we changed the 'source' to 'api-football'
        matches = football_service.get_live_matches("world-cup-2026")
        if not matches:
            matches = football_service.get_upcoming_matches("world-cup-2026")
        mode = "live"
        
    else:
        if selected_date:
                matches = football_service.get_matches_by_date(
                    league_key=league,
                    selected_date=selected_date,
                )
                mode = "date"
        else:
                matches = football_service.get_live_matches(league)
                mode = "live"

                if not matches:
                    matches = football_service.get_upcoming_matches(league)
                    mode = "upcoming"

    return render_template(
        "index.html",
        matches=matches,
        mode=mode,
        selected_league=league,
        selected_date=selected_date,
        available_dates=available_dates,
    )


@app.route("/match/<match_id>")
def match_details(match_id):
    selected_league = request.args.get("league")
    selected_date = request.args.get("date")

    match = football_service.get_match_details(match_id)

    if match is None:
        return "Match not found", 404

    return render_template(
        "match.html",
        match=match,
        selected_league=selected_league,
        selected_date=selected_date,
    )


@app.route("/api/live/all")
def api_live():
    league = request.args.get("league")
    selected_date = request.args.get("date")

    # NEW: If no league is specified, get ALL live matches across all competitions
    if not league:
        all_live_matches = football_service.get_all_live_matches()
        return jsonify({
            "mode": "all_live",
            "total": len(all_live_matches),
            "matches": all_live_matches,
        })

    # EXISTING: If a league is specified, use the old logic
    if selected_date:
        matches = football_service.get_matches_by_date(
            league_key=league,
            selected_date=selected_date,
        )
        mode = "date"
    else:
        matches = football_service.get_live_matches(league)
        mode = "live"

        if not matches:
            matches = football_service.get_upcoming_matches(league)
            mode = "upcoming"

    return jsonify({
        "mode": mode,
        "matches": matches,
    })

@app.route("/api/standings/<league_key>")
def api_standings(league_key):
    """Fetch the final league table from the service."""
    standings = football_service.get_standings(league_key)
    return jsonify(standings)



if __name__ == "__main__":
    # We set debug=False for security.
    # The 0.0.0.0 bind is intentional for Docker/Kubernetes usage.
    app.run(host="0.0.0.0", port=5000, debug=False)  # nosec B104
