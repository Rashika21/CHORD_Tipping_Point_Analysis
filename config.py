"""
config.py
=========
Central configuration for the TPI Analysis pipeline.
All paths, parameters, and experiment metadata are defined here.
Modify DATA_DIR to point to your AircraftVerse data_full folder.
"""

import os
from datetime import date

# ── Experiment identity ────────────────────────────────────────────────────────
EXPERIMENT_DATE   = date.today().strftime("%Y_%m_%d")   # e.g. "2026_06_01"
EXPERIMENT_ID     = f"EXP_{EXPERIMENT_DATE}_TPI_v1"
EXPERIMENT_NOTES  = "Baseline TPI computation on AircraftVerse corpus using May-Wigner criterion."

# ── Root paths ─────────────────────────────────────────────────────────────────
ROOT_DIR        = os.path.dirname(os.path.abspath(__file__))
DATA_DIR        = "/Users/RashikaSN/Rashika/01 Education/01 Education/03 Stevens/00 Research/11 Complexity/Aircraft Copter Data/AircraftVerse Github/AircraftVerse/data_full"
CORPUS_PATH     = "/Users/RashikaSN/Rashika/01 Education/01 Education/03 Stevens/00 Research/11 Complexity/Aircraft Copter Data/AircraftVerse Github/AircraftVerse/data/corpus_dic"

OUTPUT_DIR      = os.path.join(ROOT_DIR, "outputs", EXPERIMENT_DATE)
FIGURES_DIR     = os.path.join(OUTPUT_DIR, "figures")
DATA_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "data")
EXPERIMENT_LOG  = os.path.join(ROOT_DIR, "experiments", EXPERIMENT_DATE)

# ── Output files ───────────────────────────────────────────────────────────────
TPI_RESULTS_CSV      = os.path.join(DATA_OUTPUT_DIR, "tpi_results.csv")
SUMMARY_STATS_JSON   = os.path.join(DATA_OUTPUT_DIR, "summary_stats.json")

# ── May-Wigner / TPI parameters ───────────────────────────────────────────────
# Fragility tier boundaries (based on ACR regimes in Table 1 of APM paper)
TIERS = {
    "stable":       (float("-inf"), 0.0),   # TPI <= 0  (ACR >= 1, synergistic)
    "preservation": (0.0,           0.3),   # low precariousness
    "precarious":   (0.3,           0.7),   # moderate precariousness
    "critical":     (0.7,           0.9),   # high precariousness
    "collapse":     (0.9,           1.0),   # near tipping point
}

# TPI threshold for flagging designs for architectural review
TPI_FLAG_THRESHOLD = 0.8

# ── Plot style ─────────────────────────────────────────────────────────────────
PLOT_STYLE      = "seaborn-v0_8-whitegrid"
FIGURE_DPI      = 150
FIGURE_FORMAT   = "png"
COLOR_PALETTE   = "viridis"     # used for continuous coloring
ACCENT_COLOR    = "#2C6FAC"     # Stevens blue
DANGER_COLOR    = "#C0392B"     # red for high-TPI
SAFE_COLOR      = "#27AE60"     # green for low-TPI

# ── Processing ─────────────────────────────────────────────────────────────────
MAX_DESIGNS     = None          # None = process all; set integer for quick tests
LOG_INTERVAL    = 500           # print progress every N designs
