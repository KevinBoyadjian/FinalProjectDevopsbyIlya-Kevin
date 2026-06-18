import time
from flask import Flask, jsonify, render_template, request, make_response
from config import Config
from services.football_api import FootballAPIService

app = Flask(__name__)
app.config.from_object(Config)
football_service = FootballAPIService(app.config)

# --- GLOBAL CACHE VARIABLES ---
cache_data = None
last_fetch_time = 0
CACHE_DURATION = 60 # 60 seconds

def add_cache_headers(response, max_age):
    response.headers["Cache-Control"] = f"public, max-age={max_age}"
    return response

@app.route("/")
def index():
    global cache_data, last_fetch_time
    
    # 1. Get Parameters
    league = request.args.get("league", "world-cup-2026")
    selected_date = request.args.get("date")
    available_dates = football_service.get_available_dates(league)
    current_time = time.time()

    # 2. CACHE LOGIC: Only apply to the default Live World Cup view
    if not selected_date and league == "world-cup-2026":
        if cache_data and (current_time - last_fetch_time < CACHE_DURATION):
            print("DEBUG: Serving Homepage from Cache")
            resp = make_response(render_template(
                "index.html",
                matches=cache_data["matches"],
                mode="live",
                selected_league=league,
                selected_date=None,
                available_dates=available_dates,
            ))
            return add_cache_headers(resp, 60)

    # 3. DATA FETCHING (If not cached or if viewing a specific date)
    if selected_date:
        # This calls the fixed function in football_api.py (No 500 error)
        matches = football_service.get_matches_by_date(league, selected_date)
        mode = "date"
    else:
        matches = football_service.get_all_live_matches()
        mode = "live"
        # Update the cache for the next user
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
    current_time = time.time()

    # Serve AJAX requests from the same cache
    if cache_data and (current_time - last_fetch_time < CACHE_DURATION):
        return jsonify({"mode": "all_live", "matches": cache_data["matches"], "cached": True})

    # If cache expired, fetch fresh
    all_live_matches = football_service.get_all_live_matches()
    cache_data = {"matches": all_live_matches, "total": len(all_live_matches)}
    last_fetch_time = current_time
    
    return jsonify({"mode": "all_live", "matches": all_live_matches, "cached": False})

@app.route("/api/standings/<league_key>")
def api_standings(league_key):
    # Standings don't change often, so we use a long 24-hour cache
    standings = football_service.get_standings(league_key)
    resp = make_response(jsonify(standings))
    return add_cache_headers(resp, 86400)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
