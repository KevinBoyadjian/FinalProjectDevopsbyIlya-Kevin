/**
 * main.js - Optimized for World Cup 2026 Pro API
 */

async function refreshAllLiveMatches() {
    const container = document.getElementById("matches-container");
    if (!container) return;

    try {
        const response = await fetch(`/api/live/all`);

        if (response.status === 429) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">⏳</div>
                    <h3>API limit reached</h3>
                    <p>Our Pro API is currently throttled. Please try again in a minute.</p>
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
                    <p>Check the tournament schedule for upcoming games.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = "";

        matches.forEach(match => {
            const card = document.createElement("article");
            card.className = `match-card ${match.status === 'FT' ? 'finished' : 'live'}`;

            // Check if match is live to add a badge
            const isLive = ['1H', '2H', 'HT', 'ET', 'P'].includes(match.status);

            card.innerHTML = `
                <div class="match-status">
                    <span class="live-badge ${isLive ? 'pulsing' : ''}">${match.status}</span>
                    <span class="minute">${isLive ? match.minute + "'" : ''}</span>
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
                    <a class="details-link" href="/match/${match.id}">Match stats</a>
                </div>
            `;

            container.appendChild(card);
        });

    } catch (error) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">✖</div>
                <h3>Connection Error</h3>
                <p>Unable to reach the live score server.</p>
            </div>
        `;
        console.error("Live Fetch Error:", error);
    }
}

async function showFinalStandings(leagueKey) {
    const container = document.getElementById("matches-container");
    if (!container) return;
    
    container.innerHTML = "<div class='loading'>Calculating Final Standings...</div>";

    try {
        const response = await fetch(`/api/standings/${leagueKey}`);
        const standings = await response.json();

        if (!standings || !standings.length) {
            container.innerHTML = "<div class='empty-state'>Standings currently unavailable for this league.</div>";
            return;
        }

        let html = `
            <div class="standings-header">
                <h2>${leagueKey.replace(/-/g, ' ').toUpperCase()}</h2>
                <p class="off-season-note">🏆 2025/26 Season Finished</p>
            </div>
            <div class="table-responsive">
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
                    <td><strong>${row.team}</strong></td>
                    <td>${row.points}</td>
                </tr>
            `;
        });

        html += `</tbody></table></div>`;
        container.innerHTML = html;

    } catch (error) {
        container.innerHTML = "<p>Error loading standings.</p>";
        console.error("Standings Fetch Error:", error);
    }
}

/**
 * Page Logic Initialization
 */
document.addEventListener("DOMContentLoaded", () => {
    const params = new URLSearchParams(window.location.search);
    const league = params.get("league");
    const dateParam = params.get("date");

    // 1. ROUTING LOGIC
    if (league && league !== "world-cup-2026") {
        // Mode: OFF-SEASON STANDINGS
        showFinalStandings(league);
    } 
    else if (dateParam) {
        // Mode: HISTORICAL DATA
        // We do nothing here because the Python backend (app.py) 
        // already rendered the correct matches into the HTML.
        console.log("Showing matches for: " + dateParam);
    } 
    else {
        // Mode: LIVE WORLD CUP
        refreshAllLiveMatches();
        // Update live scores every 60 seconds (Matches server cache)
        setInterval(refreshAllLiveMatches, 60000);
    }

    // 2. REFRESH BUTTON LOGIC
    const refreshButton = document.getElementById("refresh-btn");
    if (refreshButton) {
        refreshButton.addEventListener("click", () => {
            const currentParams = new URLSearchParams(window.location.search);
            const currentLeague = currentParams.get("league");
            const currentDate = currentParams.get("date");

            if (currentLeague && currentLeague !== "world-cup-2026") {
                showFinalStandings(currentLeague);
            } else if (currentDate) {
                // If on a specific date, reload the whole page to get fresh server data
                window.location.reload();
            } else {
                refreshAllLiveMatches();
            }
        });
    }
});
