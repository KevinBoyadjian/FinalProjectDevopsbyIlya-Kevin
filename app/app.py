@app.route("/match/<match_id>")
def match_details(match_id):
    selected_league = request.args.get("league")
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