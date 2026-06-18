@app.route("/match/<match_id>")
def match_details(match_id):
    selected_league = request.args.get("league", "world-cup-2026")
    selected_date = request.args.get("date")

    match = football_service.get_match_details(match_id)

    if not match:
        return render_template(
            "match.html",
            match={
                "home_team": "Match",
                "away_team": "not found",
                "home_score": None,
                "away_score": None,
                "status": "N/A",
                "minute": 0,
                "date": "",
                "stadium": "",
                "city": "",
                "events": [],
                "lineups": {
                    "home": [],
                    "away": []
                }
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