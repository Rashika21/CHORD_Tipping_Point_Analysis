"""
tpi_computation.py
==================
Core mathematical computations for the Architectural Precariousness Measure (APM).

Implements:
  - Graph density (rho)
  - Critical coupling strength (sigma_critical) — May-Wigner threshold
  - Topological Precariousness Index (TPI)
  - Fragility tier classification (Table 1 of APM paper)
  - Corpus-level batch processing

Mathematical foundation (APM paper, Sec 6.2):
  rho            = 2m / [n(n-1)]          (graph density = connectance C)
  sigma_critical = 1 / sqrt(n * rho)      (May-Wigner stability margin)
  TPI            = 1 - sigma_critical      (precariousness index ∈ [0,1])

  May-Wigner tipping condition: sigma * sqrt(n * C) = 1
  → TPI → 1 means architecture is near/past the tipping point.
  → TPI = 0 means maximum structural slack (sigma_critical → ∞).

References:
  May, R.M. (1972). Will a Large Complex System Be Stable? Nature, 238, 413–414.
  Nilchiani & Sugganahalli N B (2026). Architectural Precariousness Measure (APM).
"""

import math
from pathlib import Path

import config
from src.graph_extraction import extract_graph_from_folder


# ── Scalar computations ────────────────────────────────────────────────────────

def graph_density(n: int, m: int) -> float:
    """
    rho = 2m / [n(n-1)]
    Returns 0.0 for degenerate cases (n <= 1 or m == 0).
    """
    if n <= 1 or m == 0:
        return 0.0
    return (2 * m) / (n * (n - 1))


def sigma_critical(n: int, rho: float) -> float:
    """
    sigma_critical = 1 / sqrt(n * rho)
    Returns inf for degenerate cases (zero density → no coupling risk).
    """
    product = n * rho
    if product <= 0:
        return float("inf")
    return 1.0 / math.sqrt(product)


def compute_tpi(n: int, m: int) -> dict:
    """
    Compute all TPI-related metrics for a single design.

    Returns:
        {
            "rho":            float,  graph density
            "sigma_critical": float,  May-Wigner critical coupling strength
            "tpi":            float,  Topological Precariousness Index
            "may_wigner":     float,  sigma_c * sqrt(n*rho) — should = 1.0 always
            "tier":           str,    fragility tier label
        }
    """
    rho_val  = graph_density(n, m)
    sc       = sigma_critical(n, rho_val)
    tpi_val  = 1.0 - sc if sc != float("inf") else 0.0
    mw_check = sc * math.sqrt(n * rho_val) if rho_val > 0 else 0.0  # should ≈ 1

    return {
        "rho":            round(rho_val, 8),
        "sigma_critical": round(sc, 8) if sc != float("inf") else float("inf"),
        "tpi":            round(tpi_val, 8),
        "may_wigner":     round(mw_check, 8),
        "tier":           classify_tier(tpi_val),
    }


def classify_tier(tpi_val: float) -> str:
    """
    Assign a fragility tier label based on TPI value.
    Tier boundaries are defined in config.TIERS.
    """
    for label, (lo, hi) in config.TIERS.items():
        if lo < tpi_val <= hi:
            return label
    if tpi_val <= 0.0:
        return "stable"
    return "collapse"


# ── Batch processing ───────────────────────────────────────────────────────────

def process_design(design_folder: str | Path) -> dict | None:
    """
    Full pipeline for a single design folder:
      1. Extract graph from design_tree.json
      2. Compute TPI metrics
      3. Merge with physics outputs

    Returns a flat result dict, or None if design_tree.json is missing.
    """
    raw = extract_graph_from_folder(design_folder)
    if raw is None:
        return None

    n = raw["n_nodes"]
    m = raw["m_edges"]
    tpi_metrics = compute_tpi(n, m)

    # Drop verbose labels from final output (kept for debugging if needed)
    result = {
        "design":          raw["design"],
        "source":          raw.get("source", "unknown"),  # low_level or tree
        "n_nodes":         n,
        "m_edges":         m,
        "m_struct":        raw.get("m_struct", m),
        "m_func":          raw.get("m_func",   0),
        "rho":             tpi_metrics["rho"],
        "sigma_critical":  tpi_metrics["sigma_critical"],
        "tpi":             tpi_metrics["tpi"],
        "tier":            tpi_metrics["tier"],
    }

    # Append physics outputs (keys verified against AircraftVerse output.json)
    for key in ("hover_time", "max_speed", "max_distance", "mass", "airworthy"):
        result[key] = raw.get(key)

    return result


def run_corpus(data_dir: str | Path, logger=None, max_designs: int = None) -> list[dict]:
    """
    Process all design folders in data_dir.

    Args:
        data_dir:    Path to AircraftVerse data folder (contains design_N subfolders).
        logger:      Optional logger instance.
        max_designs: If set, stop after processing this many designs (for testing).

    Returns:
        List of result dicts, one per design.
    """
    data_path = Path(data_dir)
    folders   = sorted([
        d for d in data_path.iterdir()
        if d.is_dir() and d.name.startswith("design")
    ])

    if max_designs:
        folders = folders[:max_designs]

    results    = []
    n_skipped  = 0

    for i, folder in enumerate(folders):
        result = process_design(folder)
        if result is None:
            n_skipped += 1
            continue
        results.append(result)

        if logger and (i + 1) % config.LOG_INTERVAL == 0:
            logger.info(f"  Processed {i + 1:,} / {len(folders):,} designs "
                        f"— {n_skipped} skipped")

    if logger:
        logger.info(f"Corpus processing complete: "
                    f"{len(results):,} designs, {n_skipped} skipped.")
    return results
