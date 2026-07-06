"""
utils.py
========
IO helpers, logging, directory management, and summary serialisation.
"""

import os
import json
import csv
import logging
from datetime import datetime
from pathlib import Path

import config


# ── Logging ────────────────────────────────────────────────────────────────────

def setup_logger(name: str = "tpi") -> logging.Logger:
    """Configure and return a logger that writes to stdout + dated log file."""
    log_path = os.path.join(config.EXPERIMENT_LOG, "run.log")
    os.makedirs(config.EXPERIMENT_LOG, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    fmt = logging.Formatter("[%(asctime)s] %(levelname)s — %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File handler
    fh = logging.FileHandler(log_path)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


# ── Directory helpers ──────────────────────────────────────────────────────────

def ensure_output_dirs():
    """Create all output directories required by config."""
    for path in [config.OUTPUT_DIR, config.FIGURES_DIR,
                 config.DATA_OUTPUT_DIR, config.EXPERIMENT_LOG]:
        os.makedirs(path, exist_ok=True)


def figure_path(fig_num: int, name: str) -> str:
    """
    Return a standardised figure file path.
    Example: figure_path(3, "phase_space") → .../figures/fig_03_phase_space.png
    """
    filename = f"fig_{fig_num:02d}_{name}.{config.FIGURE_FORMAT}"
    return os.path.join(config.FIGURES_DIR, filename)


# ── Data IO ────────────────────────────────────────────────────────────────────

def save_results_csv(results: list[dict], path: str = None):
    """Write list-of-dicts to CSV. Uses config.TPI_RESULTS_CSV by default."""
    path = path or config.TPI_RESULTS_CSV
    if not results:
        return
    fieldnames = list(results[0].keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def load_results_csv(path: str = None) -> list[dict]:
    """Load TPI results CSV back into a list of dicts."""
    path = path or config.TPI_RESULTS_CSV
    results = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Cast numeric fields
            for key in ["n_nodes", "m_edges"]:
                if row.get(key) not in (None, ""):
                    row[key] = int(row[key])
            for key in ["rho", "sigma_critical", "tpi",
                        "hover_time", "max_speed", "max_distance"]:
                if row.get(key) not in (None, "", "None"):
                    row[key] = float(row[key])
                else:
                    row[key] = None
            if row.get("airworthy") not in (None, "", "None"):
                row["airworthy"] = int(float(row["airworthy"]))
            else:
                row["airworthy"] = None
            results.append(row)
    return results


def save_summary_json(summary: dict, path: str = None):
    """Persist summary statistics as JSON."""
    path = path or config.SUMMARY_STATS_JSON
    with open(path, "w") as f:
        json.dump(summary, f, indent=2, default=str)


# ── Summary statistics ─────────────────────────────────────────────────────────

def save_ranked_csv(results: list[dict], path: str = None):
    """
    Save designs sorted by TPI descending (most precarious first).
    Includes rank, design ID, n, m, rho, sigma_critical, TPI, tier,
    and all performance metrics.
    Answers Q5 & Q6: "Which specific design has the highest/lowest TPI?"
    """
    path = path or os.path.join(config.DATA_OUTPUT_DIR, "tpi_ranked.csv")
    ranked = sorted(
        [r for r in results if r.get("tpi") is not None],
        key=lambda r: r["tpi"],
        reverse=True
    )
    if not ranked:
        return
    fieldnames = ["rank"] + [k for k in ranked[0].keys() if k != "labels"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for i, row in enumerate(ranked, start=1):
            writer.writerow({"rank": i, **{k: row.get(k) for k in fieldnames[1:]}})


def compute_summary(results: list[dict]) -> dict:
    """Compute descriptive statistics over TPI results."""
    tpi   = [r["tpi"] for r in results if r.get("tpi") is not None]
    n     = [r["n_nodes"] for r in results if r.get("n_nodes") is not None]
    rho   = [r["rho"] for r in results if r.get("rho") is not None]
    sigma = [r["sigma_critical"] for r in results
             if r.get("sigma_critical") is not None and r["sigma_critical"] != float("inf")]

    def _stats(lst):
        if not lst:
            return {}
        return {
            "count":  len(lst),
            "min":    round(min(lst), 6),
            "max":    round(max(lst), 6),
            "mean":   round(sum(lst) / len(lst), 6),
            "median": round(sorted(lst)[len(lst) // 2], 6),
        }

    tier_counts = {}
    for label, (lo, hi) in config.TIERS.items():
        tier_counts[label] = sum(1 for t in tpi if lo < t <= hi)

    flagged = sum(1 for t in tpi if t >= config.TPI_FLAG_THRESHOLD)

    return {
        "experiment_id":   config.EXPERIMENT_ID,
        "generated_at":    datetime.now().isoformat(),
        "total_designs":   len(results),
        "tpi_stats":       _stats(tpi),
        "n_nodes_stats":   _stats(n),
        "rho_stats":       _stats(rho),
        "sigma_critical_stats": _stats(sigma),
        "tier_counts":     tier_counts,
        "flagged_for_review": flagged,
        "flag_threshold":  config.TPI_FLAG_THRESHOLD,
    }
