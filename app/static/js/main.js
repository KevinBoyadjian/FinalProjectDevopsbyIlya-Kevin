async function refreshAllLiveMatches() {
    const container = document.getElementById("matches-container");
    if (!container) return;

    try {
        // Call the NEW endpoint that shows ALL competitions
        const response = await fetch(`/api/live/all`);

        if (response.status === 429) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">⏳</div>
                    <h3>API limit reached</h3>
                    <p>Too many requests. Please wait a moment.</p>
                </div>
            `;
            return;
        }

        const data = await response.json();
        const matches = data.matches || [];

        if (!matches.length) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">⚽</div>
                    <h3>No live matches right now</h3>
                    <p>All 900+ competitions covered. Check back soon!</p>
                </div>
            `;
            return;
        }

        container.innerHTML = "";

        matches.forEach(match => {
            const card = document.createElement("article");
            card.className = "match-card";

            card.innerHTML = `
                <div class="match-status">
                    <span class="live-badge">${match.status}</span>
                    <span class="minute">${match.minute || 0}'</span>
                </div>

                <div class="teams">
                    <div class="team-row">
                        <span class="team-name">${match.home_team}</span>
                        <span class="team-score">${match.home_score ?? 0}</span>
                    </div>
                    <div class="team-row">
                        <span class="team-name">${match.away_team}</span>
                        <span class="team-score">${match.away_score ?? 0}</span>
                    </div>
                </div>

                <p class="match-league">${match.league}</p>

                <div class="card-footer">
                    <a class="details-link" href="/match/${match.id}">Match details</a>
                </div>
            `;

            container.appendChild(card);
        });

    } catch (error) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">✖</div>
                <h3>Failed to load matches</h3>
                <p>Please try again later.</p>
            </div>
        `;
        console.error(error);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const params = new URLSearchParams(window.location.search);
    const league = params.get("league");

    // 1. Logic Switch: Standings for Leagues, Live for World Cup
    if (league && league !== "world-cup-2026") {
        // If a specific league (like Premier League) is selected, show its final table
        showFinalStandings(league);
    } else {
        // Otherwise (Homepage or World Cup), show the Live World Cup matches
        refreshAllLiveMatches();
        
        // Only auto-refresh if we are looking at live matches
        setInterval(refreshAllLiveMatches, 30000);
    }

    // 2. Keep the Refresh Button logic (it will work for whatever is on screen)
    const refreshButton = document.getElementById("refresh-btn");
    if (refreshButton) {
        refreshButton.addEventListener("click", () => {
            if (league && league !== "world-cup-2026") {
                showFinalStandings(league);
            } else {
                refreshAllLiveMatches();
            }
        });
    }
});


async function showFinalStandings(leagueKey) {
    const container = document.getElementById("matches-container");
    if (!container) return;
    
    container.innerHTML = "<div class='loading'>Loading Final Standings...</div>";

    try {
        const response = await fetch(`/api/standings/${leagueKey}`);
        const standings = await response.json();

        if (!standings.length) {
            container.innerHTML = "<p>Standings not available for this league.</p>";
            return;
        }

        let html = `
            <div class="standings-header">
                <h2>${leagueKey.replace(/-/g, ' ').toUpperCase()}</h2>
                <p class="off-season-note">🏆 Season Finished. Focus moved to World Cup 2026.</p>
            </div>
            <table class="standings-table">
                <thead>
                    <tr>
                        <th>Pos</th>
                        <th>Team</th>
                        <th>Pts</th>
                    </tr>
                </thead>
                <tbody>
        `;

        standings.forEach(row => {
            html += `
                <tr class="${row.position <= 4 ? 'ucl-spot' : ''}">
                    <td>${row.position}</td>
                    <td>${row.team}</td>
                    <td><strong>${row.points}</strong></td>
                </tr>
            `;
        });

        html += `</tbody></table>`;
        container.innerHTML = html;

    } catch (error) {
        container.innerHTML = "<p>Error loading standings. Please try again.</p>";
        console.error("Error:", error);
    }
}
