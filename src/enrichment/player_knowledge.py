"""
Player knowledge base for data enrichment.

Contains approximate T20 statistics for well-known players based on publicly
available career data up to early 2025. For players not in this database,
the enrichment modules generate plausible stats using role + price tier heuristics.

Each entry uses the EXACT Player_ID from players_master.csv.
Stats represent aggregated 5-year performance windows.
"""

# ---------------------------------------------------------------------------
# IPL 5-Year Stats Knowledge Base
# ---------------------------------------------------------------------------
# Format: Player_ID → {stat_dict}
# Stats are approximate aggregated values over the player's most recent
# 5 IPL seasons. Not all players appear here — only those with enough
# public data for reasonable estimates.

IPL_KNOWN_STATS = {
    # ── BATSMEN ──────────────────────────────────────────────────────────
    "BAT001": {  # Abhishek Sharma
        "matches": 52, "runs": 1320, "batting_average": 28.7, "strike_rate": 155.8,
        "fifties": 8, "hundreds": 2, "wickets": 5, "economy": 8.9, "bowling_strike_rate": 36.0,
        "powerplay_sr": 162.0, "middle_sr": 145.0, "death_sr": 170.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "BAT002": {  # SKY (Suryakumar Yadav)
        "matches": 68, "runs": 2150, "batting_average": 33.6, "strike_rate": 153.2,
        "fifties": 15, "hundreds": 1, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 142.0, "middle_sr": 155.0, "death_sr": 168.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "BAT003": {  # Tilak Varma
        "matches": 40, "runs": 1150, "batting_average": 34.8, "strike_rate": 148.5,
        "fifties": 8, "hundreds": 0, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 130.0, "middle_sr": 150.0, "death_sr": 165.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "BAT004": {  # Ruturaj Gaikwad
        "matches": 62, "runs": 1900, "batting_average": 35.2, "strike_rate": 138.5,
        "fifties": 14, "hundreds": 1, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 140.0, "middle_sr": 135.0, "death_sr": 148.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "BAT005": {  # Rohit Sharma
        "matches": 60, "runs": 1750, "batting_average": 30.5, "strike_rate": 140.2,
        "fifties": 12, "hundreds": 1, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 150.0, "middle_sr": 132.0, "death_sr": 155.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "BAT006": {  # Virat Kohli
        "matches": 70, "runs": 2600, "batting_average": 42.5, "strike_rate": 138.8,
        "fifties": 18, "hundreds": 2, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 140.0, "middle_sr": 138.0, "death_sr": 142.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "BAT007": {  # Shubman Gill
        "matches": 60, "runs": 1950, "batting_average": 36.1, "strike_rate": 142.5,
        "fifties": 14, "hundreds": 2, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 145.0, "middle_sr": 138.0, "death_sr": 152.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "BAT008": {  # Sai Sudharsan
        "matches": 35, "runs": 1050, "batting_average": 34.0, "strike_rate": 140.2,
        "fifties": 7, "hundreds": 1, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 135.0, "middle_sr": 142.0, "death_sr": 148.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "BAT009": {  # Markram (Aiden Markram)
        "matches": 30, "runs": 680, "batting_average": 25.4, "strike_rate": 138.0,
        "fifties": 4, "hundreds": 0, "wickets": 3, "economy": 8.2, "bowling_strike_rate": 30.0,
        "powerplay_sr": 132.0, "middle_sr": 140.0, "death_sr": 145.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "BAT010": {  # Mitchell Marsh
        "matches": 32, "runs": 620, "batting_average": 24.0, "strike_rate": 145.5,
        "fifties": 3, "hundreds": 0, "wickets": 8, "economy": 9.2, "bowling_strike_rate": 28.0,
        "powerplay_sr": 140.0, "middle_sr": 148.0, "death_sr": 155.0,
        "powerplay_econ": 9.5, "middle_econ": 8.8, "death_econ": 10.2,
    },
    "BAT011": {  # Travis Head
        "matches": 28, "runs": 750, "batting_average": 29.0, "strike_rate": 158.5,
        "fifties": 5, "hundreds": 1, "wickets": 2, "economy": 8.5, "bowling_strike_rate": 32.0,
        "powerplay_sr": 165.0, "middle_sr": 150.0, "death_sr": 168.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "BAT012": {  # David Miller
        "matches": 60, "runs": 1350, "batting_average": 32.8, "strike_rate": 148.0,
        "fifties": 8, "hundreds": 0, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 120.0, "middle_sr": 142.0, "death_sr": 175.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "BAT014": {  # Faf du Plessis
        "matches": 65, "runs": 1850, "batting_average": 31.5, "strike_rate": 140.5,
        "fifties": 13, "hundreds": 0, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 148.0, "middle_sr": 135.0, "death_sr": 145.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "BAT017": {  # Shreyas Iyer
        "matches": 55, "runs": 1600, "batting_average": 33.5, "strike_rate": 132.5,
        "fifties": 11, "hundreds": 0, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 125.0, "middle_sr": 135.0, "death_sr": 148.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "BAT018": {  # Shimron Hetmyer
        "matches": 45, "runs": 950, "batting_average": 28.5, "strike_rate": 155.0,
        "fifties": 4, "hundreds": 0, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 130.0, "middle_sr": 145.0, "death_sr": 180.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "BAT022": {  # David Warner
        "matches": 58, "runs": 1850, "batting_average": 34.0, "strike_rate": 142.0,
        "fifties": 14, "hundreds": 1, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 155.0, "middle_sr": 135.0, "death_sr": 140.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "BAT024": {  # Yashasvi Jaiswal
        "matches": 42, "runs": 1450, "batting_average": 36.2, "strike_rate": 158.0,
        "fifties": 10, "hundreds": 1, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 168.0, "middle_sr": 148.0, "death_sr": 162.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "BAT031": {  # Kane Williamson
        "matches": 42, "runs": 1100, "batting_average": 30.8, "strike_rate": 122.5,
        "fifties": 8, "hundreds": 0, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 118.0, "middle_sr": 125.0, "death_sr": 130.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "BAT039": {  # Ajinkya Rahane
        "matches": 35, "runs": 700, "batting_average": 22.0, "strike_rate": 125.0,
        "fifties": 3, "hundreds": 0, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 128.0, "middle_sr": 122.0, "death_sr": 130.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },

    # ── WICKETKEEPERS ────────────────────────────────────────────────────
    "WK001": {  # MSD (MS Dhoni)
        "matches": 50, "runs": 1100, "batting_average": 32.5, "strike_rate": 152.0,
        "fifties": 4, "hundreds": 0, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 120.0, "middle_sr": 140.0, "death_sr": 185.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "WK002": {  # Rishabh Pant
        "matches": 55, "runs": 1650, "batting_average": 35.0, "strike_rate": 150.5,
        "fifties": 10, "hundreds": 0, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 145.0, "middle_sr": 148.0, "death_sr": 165.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "WK003": {  # KL Rahul
        "matches": 62, "runs": 2200, "batting_average": 40.5, "strike_rate": 136.5,
        "fifties": 18, "hundreds": 1, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 135.0, "middle_sr": 134.0, "death_sr": 148.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "WK004": {  # Nicolas Pooran
        "matches": 42, "runs": 1050, "batting_average": 28.5, "strike_rate": 155.0,
        "fifties": 6, "hundreds": 0, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 140.0, "middle_sr": 148.0, "death_sr": 178.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "WK005": {  # Heinrich Klaasen
        "matches": 35, "runs": 1100, "batting_average": 36.5, "strike_rate": 162.0,
        "fifties": 7, "hundreds": 1, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 135.0, "middle_sr": 155.0, "death_sr": 190.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "WK006": {  # Sanju Samson
        "matches": 65, "runs": 1800, "batting_average": 30.0, "strike_rate": 145.0,
        "fifties": 10, "hundreds": 2, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 148.0, "middle_sr": 140.0, "death_sr": 155.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "WK007": {  # Ishan Kishan
        "matches": 50, "runs": 1350, "batting_average": 28.5, "strike_rate": 140.0,
        "fifties": 8, "hundreds": 0, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 148.0, "middle_sr": 135.0, "death_sr": 145.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "WK008": {  # Phil Salt
        "matches": 22, "runs": 680, "batting_average": 32.5, "strike_rate": 168.0,
        "fifties": 5, "hundreds": 1, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 178.0, "middle_sr": 158.0, "death_sr": 170.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "WK010": {  # QDK (Quinton de Kock)
        "matches": 55, "runs": 1700, "batting_average": 33.0, "strike_rate": 142.0,
        "fifties": 12, "hundreds": 1, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 155.0, "middle_sr": 135.0, "death_sr": 140.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },
    "WK011": {  # Jos Buttler
        "matches": 52, "runs": 1800, "batting_average": 38.0, "strike_rate": 152.0,
        "fifties": 12, "hundreds": 3, "wickets": 0, "economy": 0, "bowling_strike_rate": 0,
        "powerplay_sr": 155.0, "middle_sr": 148.0, "death_sr": 165.0,
        "powerplay_econ": 0, "middle_econ": 0, "death_econ": 0,
    },

    # ── ALL ROUNDERS ─────────────────────────────────────────────────────
    "AR001": {  # Hardik Pandya
        "matches": 58, "runs": 1400, "batting_average": 28.5, "strike_rate": 150.0,
        "fifties": 6, "hundreds": 0, "wickets": 42, "economy": 8.8, "bowling_strike_rate": 22.5,
        "powerplay_sr": 135.0, "middle_sr": 148.0, "death_sr": 172.0,
        "powerplay_econ": 8.2, "middle_econ": 8.5, "death_econ": 10.5,
    },
    "AR002": {  # Andre Russell
        "matches": 55, "runs": 1200, "batting_average": 28.0, "strike_rate": 175.0,
        "fifties": 5, "hundreds": 0, "wickets": 35, "economy": 9.5, "bowling_strike_rate": 24.0,
        "powerplay_sr": 155.0, "middle_sr": 165.0, "death_sr": 200.0,
        "powerplay_econ": 8.8, "middle_econ": 9.2, "death_econ": 11.0,
    },
    "AR003": {  # Sunil Narine
        "matches": 65, "runs": 1100, "batting_average": 22.0, "strike_rate": 172.0,
        "fifties": 4, "hundreds": 1, "wickets": 55, "economy": 6.5, "bowling_strike_rate": 18.5,
        "powerplay_sr": 185.0, "middle_sr": 155.0, "death_sr": 160.0,
        "powerplay_econ": 6.2, "middle_econ": 6.4, "death_econ": 7.5,
    },
    "AR004": {  # Shivam Dube
        "matches": 50, "runs": 1100, "batting_average": 28.5, "strike_rate": 145.0,
        "fifties": 5, "hundreds": 0, "wickets": 8, "economy": 9.5, "bowling_strike_rate": 32.0,
        "powerplay_sr": 128.0, "middle_sr": 140.0, "death_sr": 172.0,
        "powerplay_econ": 9.0, "middle_econ": 9.2, "death_econ": 10.8,
    },
    "AR005": {  # Ravindra Jadeja
        "matches": 65, "runs": 1250, "batting_average": 26.0, "strike_rate": 135.0,
        "fifties": 5, "hundreds": 0, "wickets": 52, "economy": 7.2, "bowling_strike_rate": 20.5,
        "powerplay_sr": 120.0, "middle_sr": 128.0, "death_sr": 162.0,
        "powerplay_econ": 7.0, "middle_econ": 7.0, "death_econ": 8.2,
    },
    "AR006": {  # Marcus Stoinis
        "matches": 45, "runs": 950, "batting_average": 26.5, "strike_rate": 145.0,
        "fifties": 4, "hundreds": 0, "wickets": 18, "economy": 9.0, "bowling_strike_rate": 26.0,
        "powerplay_sr": 140.0, "middle_sr": 142.0, "death_sr": 160.0,
        "powerplay_econ": 8.5, "middle_econ": 8.8, "death_econ": 10.5,
    },
    "AR008": {  # Ben Stokes
        "matches": 30, "runs": 650, "batting_average": 24.5, "strike_rate": 138.0,
        "fifties": 3, "hundreds": 0, "wickets": 18, "economy": 8.8, "bowling_strike_rate": 24.0,
        "powerplay_sr": 132.0, "middle_sr": 135.0, "death_sr": 155.0,
        "powerplay_econ": 8.2, "middle_econ": 8.5, "death_econ": 10.0,
    },
    "AR011": {  # Sam Curran
        "matches": 45, "runs": 650, "batting_average": 22.0, "strike_rate": 140.0,
        "fifties": 2, "hundreds": 0, "wickets": 35, "economy": 8.5, "bowling_strike_rate": 21.5,
        "powerplay_sr": 125.0, "middle_sr": 135.0, "death_sr": 158.0,
        "powerplay_econ": 7.8, "middle_econ": 8.2, "death_econ": 10.2,
    },
    "AR013": {  # Glenn Maxwell
        "matches": 52, "runs": 1200, "batting_average": 25.0, "strike_rate": 158.0,
        "fifties": 5, "hundreds": 1, "wickets": 22, "economy": 7.8, "bowling_strike_rate": 22.0,
        "powerplay_sr": 148.0, "middle_sr": 155.0, "death_sr": 175.0,
        "powerplay_econ": 7.5, "middle_econ": 7.8, "death_econ": 8.8,
    },
    "AR014": {  # Pat Cummins
        "matches": 30, "runs": 350, "batting_average": 18.0, "strike_rate": 145.0,
        "fifties": 0, "hundreds": 0, "wickets": 35, "economy": 8.5, "bowling_strike_rate": 18.0,
        "powerplay_sr": 130.0, "middle_sr": 140.0, "death_sr": 165.0,
        "powerplay_econ": 7.8, "middle_econ": 8.2, "death_econ": 10.0,
    },
    "AR015": {  # Axar Patel
        "matches": 55, "runs": 800, "batting_average": 22.0, "strike_rate": 140.0,
        "fifties": 3, "hundreds": 0, "wickets": 42, "economy": 7.0, "bowling_strike_rate": 20.0,
        "powerplay_sr": 125.0, "middle_sr": 135.0, "death_sr": 162.0,
        "powerplay_econ": 7.2, "middle_econ": 6.8, "death_econ": 7.8,
    },
    "AR017": {  # Ravi Ashwin
        "matches": 40, "runs": 350, "batting_average": 15.0, "strike_rate": 118.0,
        "fifties": 0, "hundreds": 0, "wickets": 38, "economy": 6.8, "bowling_strike_rate": 19.5,
        "powerplay_sr": 110.0, "middle_sr": 118.0, "death_sr": 130.0,
        "powerplay_econ": 6.5, "middle_econ": 6.5, "death_econ": 8.0,
    },

    # ── FAST BOWLERS ─────────────────────────────────────────────────────
    "PACE001": {  # Boom Boom (Jasprit Bumrah)
        "matches": 60, "runs": 30, "batting_average": 5.0, "strike_rate": 90.0,
        "fifties": 0, "hundreds": 0, "wickets": 85, "economy": 6.5, "bowling_strike_rate": 15.5,
        "powerplay_sr": 0, "middle_sr": 0, "death_sr": 0,
        "powerplay_econ": 6.2, "middle_econ": 6.0, "death_econ": 7.2,
    },
    "PACE002": {  # Arshdeep Singh
        "matches": 50, "runs": 20, "batting_average": 4.0, "strike_rate": 80.0,
        "fifties": 0, "hundreds": 0, "wickets": 62, "economy": 8.5, "bowling_strike_rate": 17.5,
        "powerplay_sr": 0, "middle_sr": 0, "death_sr": 0,
        "powerplay_econ": 7.5, "middle_econ": 8.2, "death_econ": 9.8,
    },
    "PACE004": {  # Mohammed Siraj
        "matches": 55, "runs": 15, "batting_average": 3.0, "strike_rate": 75.0,
        "fifties": 0, "hundreds": 0, "wickets": 60, "economy": 8.8, "bowling_strike_rate": 19.0,
        "powerplay_sr": 0, "middle_sr": 0, "death_sr": 0,
        "powerplay_econ": 7.8, "middle_econ": 8.5, "death_econ": 10.5,
    },
    "PACE005": {  # Mohammed Shami
        "matches": 45, "runs": 10, "batting_average": 3.0, "strike_rate": 70.0,
        "fifties": 0, "hundreds": 0, "wickets": 58, "economy": 8.2, "bowling_strike_rate": 17.0,
        "powerplay_sr": 0, "middle_sr": 0, "death_sr": 0,
        "powerplay_econ": 7.2, "middle_econ": 8.0, "death_econ": 9.8,
    },
    "PACE006": {  # Bhuvneshwar Kumar
        "matches": 48, "runs": 50, "batting_average": 8.0, "strike_rate": 100.0,
        "fifties": 0, "hundreds": 0, "wickets": 50, "economy": 7.5, "bowling_strike_rate": 19.5,
        "powerplay_sr": 0, "middle_sr": 0, "death_sr": 0,
        "powerplay_econ": 6.8, "middle_econ": 7.5, "death_econ": 8.8,
    },
    "PACE008": {  # Mitchell Starc
        "matches": 18, "runs": 15, "batting_average": 5.0, "strike_rate": 110.0,
        "fifties": 0, "hundreds": 0, "wickets": 22, "economy": 9.2, "bowling_strike_rate": 16.5,
        "powerplay_sr": 0, "middle_sr": 0, "death_sr": 0,
        "powerplay_econ": 8.0, "middle_econ": 8.8, "death_econ": 11.0,
    },
    "PACE012": {  # Trent Boult
        "matches": 50, "runs": 20, "batting_average": 4.0, "strike_rate": 85.0,
        "fifties": 0, "hundreds": 0, "wickets": 55, "economy": 8.0, "bowling_strike_rate": 18.0,
        "powerplay_sr": 0, "middle_sr": 0, "death_sr": 0,
        "powerplay_econ": 7.0, "middle_econ": 7.8, "death_econ": 9.5,
    },
    "PACE014": {  # Kagiso Rabada
        "matches": 45, "runs": 25, "batting_average": 5.0, "strike_rate": 95.0,
        "fifties": 0, "hundreds": 0, "wickets": 55, "economy": 8.2, "bowling_strike_rate": 17.5,
        "powerplay_sr": 0, "middle_sr": 0, "death_sr": 0,
        "powerplay_econ": 7.5, "middle_econ": 8.0, "death_econ": 9.5,
    },
    "PACE016": {  # Matheesha Pathirana
        "matches": 25, "runs": 10, "batting_average": 3.0, "strike_rate": 80.0,
        "fifties": 0, "hundreds": 0, "wickets": 32, "economy": 8.0, "bowling_strike_rate": 16.0,
        "powerplay_sr": 0, "middle_sr": 0, "death_sr": 0,
        "powerplay_econ": 7.5, "middle_econ": 7.8, "death_econ": 8.8,
    },
    "PACE039": {  # Harshal Patel
        "matches": 55, "runs": 100, "batting_average": 10.0, "strike_rate": 125.0,
        "fifties": 0, "hundreds": 0, "wickets": 60, "economy": 8.8, "bowling_strike_rate": 18.0,
        "powerplay_sr": 0, "middle_sr": 0, "death_sr": 0,
        "powerplay_econ": 7.5, "middle_econ": 8.2, "death_econ": 10.5,
    },

    # ── SPINNERS ─────────────────────────────────────────────────────────
    "SPIN001": {  # Ravi Bishnoi
        "matches": 45, "runs": 15, "batting_average": 4.0, "strike_rate": 70.0,
        "fifties": 0, "hundreds": 0, "wickets": 48, "economy": 7.2, "bowling_strike_rate": 18.0,
        "powerplay_sr": 0, "middle_sr": 0, "death_sr": 0,
        "powerplay_econ": 7.5, "middle_econ": 6.8, "death_econ": 8.0,
    },
    "SPIN002": {  # Rashid Khan
        "matches": 60, "runs": 350, "batting_average": 15.0, "strike_rate": 155.0,
        "fifties": 0, "hundreds": 0, "wickets": 68, "economy": 6.5, "bowling_strike_rate": 16.0,
        "powerplay_sr": 0, "middle_sr": 0, "death_sr": 0,
        "powerplay_econ": 6.8, "middle_econ": 6.2, "death_econ": 7.0,
    },
    "SPIN004": {  # Varun Chakravarthy
        "matches": 42, "runs": 10, "batting_average": 3.0, "strike_rate": 60.0,
        "fifties": 0, "hundreds": 0, "wickets": 52, "economy": 7.0, "bowling_strike_rate": 17.0,
        "powerplay_sr": 0, "middle_sr": 0, "death_sr": 0,
        "powerplay_econ": 7.2, "middle_econ": 6.5, "death_econ": 7.8,
    },
    "SPIN005": {  # Yuzi Chahal
        "matches": 58, "runs": 20, "batting_average": 4.0, "strike_rate": 60.0,
        "fifties": 0, "hundreds": 0, "wickets": 62, "economy": 7.5, "bowling_strike_rate": 17.5,
        "powerplay_sr": 0, "middle_sr": 0, "death_sr": 0,
        "powerplay_econ": 7.8, "middle_econ": 7.0, "death_econ": 8.2,
    },
    "SPIN006": {  # Kuldeep Yadav
        "matches": 45, "runs": 30, "batting_average": 5.0, "strike_rate": 80.0,
        "fifties": 0, "hundreds": 0, "wickets": 50, "economy": 7.8, "bowling_strike_rate": 18.5,
        "powerplay_sr": 0, "middle_sr": 0, "death_sr": 0,
        "powerplay_econ": 7.5, "middle_econ": 7.5, "death_econ": 8.8,
    },
}

# ---------------------------------------------------------------------------
# T20 League Stats Knowledge Base (Other Leagues)
# ---------------------------------------------------------------------------
# Format: Player_ID → list of {league, matches, runs, avg, sr, wickets, economy}

T20_KNOWN_STATS = {
    "BAT002": [  # SKY
        {"league": "International T20", "matches": 70, "runs": 2500, "batting_average": 42.0, "strike_rate": 168.0, "wickets": 0, "economy": 0},
    ],
    "BAT005": [  # Rohit Sharma
        {"league": "International T20", "matches": 80, "runs": 2800, "batting_average": 32.0, "strike_rate": 142.0, "wickets": 0, "economy": 0},
    ],
    "BAT006": [  # Virat Kohli
        {"league": "International T20", "matches": 75, "runs": 2600, "batting_average": 48.0, "strike_rate": 140.0, "wickets": 0, "economy": 0},
    ],
    "BAT011": [  # Travis Head
        {"league": "International T20", "matches": 40, "runs": 1100, "batting_average": 30.0, "strike_rate": 155.0, "wickets": 1, "economy": 8.0},
        {"league": "Big Bash League", "matches": 65, "runs": 1800, "batting_average": 32.0, "strike_rate": 148.0, "wickets": 2, "economy": 8.5},
    ],
    "BAT012": [  # David Miller
        {"league": "International T20", "matches": 55, "runs": 1400, "batting_average": 35.0, "strike_rate": 142.0, "wickets": 0, "economy": 0},
        {"league": "SA20", "matches": 20, "runs": 550, "batting_average": 32.0, "strike_rate": 148.0, "wickets": 0, "economy": 0},
    ],
    "BAT022": [  # David Warner
        {"league": "International T20", "matches": 65, "runs": 2100, "batting_average": 34.0, "strike_rate": 142.0, "wickets": 0, "economy": 0},
        {"league": "Big Bash League", "matches": 55, "runs": 1600, "batting_average": 35.0, "strike_rate": 140.0, "wickets": 0, "economy": 0},
    ],
    "WK004": [  # Nicolas Pooran
        {"league": "International T20", "matches": 50, "runs": 1100, "batting_average": 25.0, "strike_rate": 145.0, "wickets": 0, "economy": 0},
        {"league": "Caribbean Premier League", "matches": 60, "runs": 1500, "batting_average": 30.0, "strike_rate": 148.0, "wickets": 0, "economy": 0},
        {"league": "SA20", "matches": 15, "runs": 420, "batting_average": 30.0, "strike_rate": 155.0, "wickets": 0, "economy": 0},
    ],
    "WK005": [  # Heinrich Klaasen
        {"league": "International T20", "matches": 45, "runs": 1200, "batting_average": 32.0, "strike_rate": 158.0, "wickets": 0, "economy": 0},
        {"league": "SA20", "matches": 22, "runs": 700, "batting_average": 38.0, "strike_rate": 162.0, "wickets": 0, "economy": 0},
    ],
    "WK008": [  # Phil Salt
        {"league": "International T20", "matches": 35, "runs": 1050, "batting_average": 35.0, "strike_rate": 172.0, "wickets": 0, "economy": 0},
        {"league": "Big Bash League", "matches": 12, "runs": 350, "batting_average": 30.0, "strike_rate": 165.0, "wickets": 0, "economy": 0},
    ],
    "WK011": [  # Jos Buttler
        {"league": "International T20", "matches": 55, "runs": 1600, "batting_average": 35.0, "strike_rate": 148.0, "wickets": 0, "economy": 0},
        {"league": "The Hundred", "matches": 20, "runs": 600, "batting_average": 38.0, "strike_rate": 155.0, "wickets": 0, "economy": 0},
    ],
    "AR001": [  # Hardik Pandya
        {"league": "International T20", "matches": 65, "runs": 1200, "batting_average": 28.0, "strike_rate": 145.0, "wickets": 30, "economy": 8.5},
    ],
    "AR002": [  # Andre Russell
        {"league": "Caribbean Premier League", "matches": 55, "runs": 1100, "batting_average": 28.0, "strike_rate": 165.0, "wickets": 25, "economy": 9.2},
        {"league": "Big Bash League", "matches": 15, "runs": 350, "batting_average": 25.0, "strike_rate": 170.0, "wickets": 8, "economy": 9.5},
    ],
    "AR003": [  # Sunil Narine
        {"league": "Caribbean Premier League", "matches": 65, "runs": 800, "batting_average": 18.0, "strike_rate": 155.0, "wickets": 72, "economy": 5.8},
        {"league": "Big Bash League", "matches": 10, "runs": 120, "batting_average": 15.0, "strike_rate": 145.0, "wickets": 12, "economy": 6.5},
    ],
    "PACE001": [  # Bumrah
        {"league": "International T20", "matches": 65, "runs": 5, "batting_average": 2.0, "strike_rate": 50.0, "wickets": 85, "economy": 6.2},
    ],
    "PACE008": [  # Mitchell Starc
        {"league": "International T20", "matches": 50, "runs": 10, "batting_average": 4.0, "strike_rate": 80.0, "wickets": 60, "economy": 7.5},
        {"league": "Big Bash League", "matches": 20, "runs": 15, "batting_average": 5.0, "strike_rate": 90.0, "wickets": 28, "economy": 7.2},
    ],
    "PACE012": [  # Trent Boult
        {"league": "International T20", "matches": 55, "runs": 8, "batting_average": 3.0, "strike_rate": 70.0, "wickets": 65, "economy": 7.8},
        {"league": "Big Bash League", "matches": 12, "runs": 5, "batting_average": 2.0, "strike_rate": 60.0, "wickets": 15, "economy": 7.5},
    ],
    "PACE014": [  # Kagiso Rabada
        {"league": "International T20", "matches": 45, "runs": 10, "batting_average": 4.0, "strike_rate": 75.0, "wickets": 50, "economy": 7.8},
        {"league": "SA20", "matches": 15, "runs": 10, "batting_average": 3.0, "strike_rate": 70.0, "wickets": 20, "economy": 7.5},
    ],
    "SPIN002": [  # Rashid Khan
        {"league": "International T20", "matches": 75, "runs": 400, "batting_average": 12.0, "strike_rate": 150.0, "wickets": 130, "economy": 6.0},
        {"league": "Big Bash League", "matches": 50, "runs": 250, "batting_average": 15.0, "strike_rate": 145.0, "wickets": 65, "economy": 6.2},
        {"league": "SA20", "matches": 15, "runs": 80, "batting_average": 10.0, "strike_rate": 140.0, "wickets": 22, "economy": 6.5},
    ],
}

# ---------------------------------------------------------------------------
# News & Sentiment Knowledge Base
# ---------------------------------------------------------------------------
# Format: Player_ID → {injury_risk, sentiment_score, news_summary}

NEWS_KNOWN = {
    "BAT005": {"injury_risk": "Medium", "sentiment_score": 82, "news_summary": "Stepped down as India T20I captain after 2024 WC win. Strong IPL form continues."},
    "BAT006": {"injury_risk": "Low", "sentiment_score": 95, "news_summary": "Consistent run-machine. Strong IPL 2024 season with century in final. Fan favorite."},
    "BAT002": {"injury_risk": "Low", "sentiment_score": 90, "news_summary": "India T20I captain. Phenomenal 360-degree batting. Global T20 star."},
    "BAT024": {"injury_risk": "Low", "sentiment_score": 88, "news_summary": "Young explosive opener. Breakthrough IPL seasons. Consistent run-scorer."},
    "WK001": {"injury_risk": "High", "sentiment_score": 98, "news_summary": "Legendary captain. Semi-retired but enormous fan following. Fitness concerns due to age."},
    "WK002": {"injury_risk": "Medium", "sentiment_score": 85, "news_summary": "Returned from serious car accident. Strong comeback form. Captaincy material."},
    "WK003": {"injury_risk": "Low", "sentiment_score": 78, "news_summary": "Reliable anchor bat. Struggles with strike rate criticism but averages highly."},
    "WK005": {"injury_risk": "Low", "sentiment_score": 88, "news_summary": "Destructive middle-order bat. 2024 T20 WC semi-final heroics. Global T20 demand."},
    "AR001": {"injury_risk": "High", "sentiment_score": 75, "news_summary": "Fitness remains primary concern. When fit, one of the best T20 all-rounders. Captaincy stint at MI."},
    "AR002": {"injury_risk": "Medium", "sentiment_score": 82, "news_summary": "IPL icon and KKR legend. Age-related workload concerns but still impactful."},
    "AR003": {"injury_risk": "Low", "sentiment_score": 80, "news_summary": "KKR legend. Opened batting successfully in 2024. Mystery spin remains effective."},
    "AR005": {"injury_risk": "Low", "sentiment_score": 80, "news_summary": "CSK stalwart. Consistent all-round contributions with bat and left-arm spin."},
    "AR013": {"injury_risk": "Medium", "sentiment_score": 72, "news_summary": "Inconsistent IPL form. Can be devastating on his day. International retirement from ODIs."},
    "PACE001": {"injury_risk": "Medium", "sentiment_score": 95, "news_summary": "World's best T20 fast bowler. Workload management crucial. 2024 T20 WC final hero."},
    "PACE004": {"injury_risk": "Low", "sentiment_score": 70, "news_summary": "Dependable pacer for RCB. Occasional expensive spells but picks wickets."},
    "PACE005": {"injury_risk": "High", "sentiment_score": 72, "news_summary": "Returning from long injury layoff. When fit, one of India's best death bowlers."},
    "PACE014": {"injury_risk": "Low", "sentiment_score": 85, "news_summary": "Elite death bowler. Consistently among top IPL wicket-takers each season."},
    "SPIN002": {"injury_risk": "Low", "sentiment_score": 92, "news_summary": "Best T20 spinner globally. Match-winner for any franchise. Exceptional economy rate."},
    "SPIN004": {"injury_risk": "Low", "sentiment_score": 78, "news_summary": "Strong comeback seasons with KKR. Mystery spin highly effective in middle overs."},
    "SPIN005": {"injury_risk": "Low", "sentiment_score": 68, "news_summary": "Experienced leg-spinner. Recent IPL form inconsistent. Still capable of match-winning spells."},
}
