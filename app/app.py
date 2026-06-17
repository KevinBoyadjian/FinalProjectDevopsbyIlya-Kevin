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
CACHE_DURATION = 60

def add_cache_headers(response, max_age):
    """Helper function to add Cache-Control headers"""
    response.headers["Cache-Control"] = f"public, max-age={max_age}"
    return response

@app.route("/health")
def health_check():
    return "OK", 200

@app.route("/")
def index():
    global cache_data, last_fetch_time
    
    league = request.args.get("league", "world-cup-2026")
    selected_date = request.args.get("date")
    available_dates = football_service.get_available_dates(league)

    current_time = time.time()

    # Cache homepage World Cup data
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
            return add_cache_headers(resp, 60)  # Cache for 60 seconds

    if selected_date:
        matches = football_service.get_matches_by_date(league, selected_date)
        mode = "date"
    else:
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
    return add_cache_headers(resp, 30)  # Short cache for live data

@app.route("/api/live/all")
def api_live():
    global cache_data, last_fetch_time
    
    league = request.args.get("league")
    selected_date = request.args.get("date")
    current_time = time.time()

    # Cache the main live endpoint
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
        cache_data = {
            "matches": all_live_matches,
            "total": len(all_live_matches)
        }
        last_fetch_time = current_time
        
        resp = make_response(jsonify({
            "mode": "all_live",
            "total": len(all_live_matches),
            "matches": all_live_matches,
            "cached": False
        }))
        return add_cache_headers(resp, 60)

    # Non-cached responses for specific leagues/dates
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
    return add_cache_headers(resp, 86400)  # Cache standings for 24 hours

@app.route("/match/<match_id>")
def match_details(match_id):
    selected_league = request.args.get("league")
    selected_date = request.args.get("date")
    match = football_service.get_match_details(match_id)
    if match is None:
        return "Match not found", 404
    return render_template("match.html", match=match, selected_league=selected_league, selected_date=selected_date)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
