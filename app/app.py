import time
from flask import Flask, jsonify, render_template, request, make_response
from config import Config
from services.football_api import FootballAPIService

app = Flask(__name__)
app.config.from_object(Config)

football_service = FootballAPIService(app.config)

# Server-side cache variables
cache_data = None
last_fetch_time = 0
CACHE_DURATION = 60 # Seconds

def add_cache_headers(response, max_age):
    """Helper function to add Cache-Control headers for CloudFront"""
    response.headers["Cache-Control"] = f"public, max-age={max_age}"
    return response

@app.route("/health")
def health_check():
    return "OK", 200

@app.route("/api/leagues")
def api_leagues():
    """Returns supported leagues for dynamic navigation tabs"""
    leagues = football_service.get_supported_leagues()
    resp = make_response(jsonify(leagues))
    return add_cache_headers(resp, 3600) # Cache list for 1 hour

@app.route("/")
def index():
    global cache_data, last_fetch_time
    
    league = request.args.get("league", "world-cup-2026")
    selected_date = request.args.get("date")
    available_dates = football_service.get_available_dates(league)

    current_time = time.time()

    # 1. Server-Side Cache for default World Cup view
    if not selected_date and league == "world-cup-2026":
        if cache_data and (current_time - last_fetch_time < CACHE_DURATION):
            resp = make_response(render_template(
                "index.html",
                matches=cache_data["matches"],
                mode="live",
                selected_league=league,
                selected_date=None,
                available_dates=available_dates,
            ))
            return add_cache_headers(resp, 60)

    # 2. Data Fetching
    if selected_date:
        # Fetches finished matches for a specific date
        matches = football_service.get_matches_by_date(league, selected_date)
        mode = "date"
    else:
        # Fetches live matches and updates cache
        matches = football_service.get_all_live_matches()
        mode = "live"
        if league == "world-cup-2026":
            cache_data = {"matches": matches, "total": len(matches)}
            last_fetch_time = current_time

    resp = make_response(render_template(
        "index.html",
        matches=matches,
        mode=mode,
        selected_league=league,
        selected_date=selected_date,
        available_dates=available_dates,
    ))
    return add_cache_headers(resp, 30)

@app.route("/api/live/all")
def api_live():
    global cache_data, last_fetch_time
    league = request.args.get("league")
    selected_date = request.args.get("date")
    current_time = time.time()

    # Cache the main "All Live" AJAX endpoint
    if not league and not selected_date:
        if cache_data and (current_time - last_fetch_time < CACHE_DURATION):
            resp = make_response(jsonify({
                "mode": "all_live",
                "total": cache_data["total"],
                "matches": cache_data["matches"],
                "cached": True
            }))
            return add_cache_headers(resp, 60)

        all_live_matches = football_service.get_all_live_matches()
        cache_data = {"matches": all_live_matches, "total": len(all_live_matches)}
        last_fetch_time = current_time
        
        resp = make_response(jsonify({"mode": "all_live", "total": len(all_live_matches), "matches": all_live_matches}))
        return add_cache_headers(resp, 60)

    # Handle filtered requests (Leagues/Dates)
    if selected_date:
        matches = football_service.get_matches_by_date(league_key=league, selected_date=selected_date)
        mode = "date"
    else:
        matches = football_service.get_live_matches(league)
        mode = "live"
        if not matches:
            matches = football_service.get_upcoming_matches(league)
            mode = "upcoming"

    resp = make_response(jsonify({"mode": mode, "matches": matches}))
    return add_cache_headers(resp, 30)

@app.route("/api/standings/<league_key>")
def api_standings(league_key):
    standings = football_service.get_standings(league_key)
    resp = make_response(jsonify(standings))
    return add_cache_headers(resp, 86400) # 24 Hour Cache for standings

@app.route("/match/<match_id>")
def match_details(match_id):
    match = football_service.get_match_details(match_id)
    if match is None:
        return "Match not found", 404
    return render_template("match.html", match=match)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
