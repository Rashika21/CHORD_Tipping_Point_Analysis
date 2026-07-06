"""
visualization.py
================
All canonical plots for TPI and architectural fragility analysis.

Figure inventory (13 plots):
  Fig 01 — TPI Distribution (histogram + KDE)
  Fig 02 — Cumulative Distribution Function (CDF) of TPI
  Fig 03 — May-Wigner Phase Space: n vs rho with stability boundary + outlier labels
  Fig 04 — TPI vs Node Count (scatter + regression + outlier labels)
  Fig 05 — TPI vs Graph Density (rho) scatter
  Fig 06 — TPI vs Hover Time (second-stage discriminator)
  Fig 07 — TPI vs Max Speed
  Fig 08 — TPI vs Max Distance
  Fig 09 — Second-Stage Discriminator Quadrant (Performance × Precariousness)
  Fig 10 — Airworthy vs Non-Airworthy TPI Comparison (violin + box)
  Fig 11 — Fragility Tier Breakdown (stacked bar)
  Fig 12 — Correlation Heatmap (TPI, n, m, rho, sigma_c, performance metrics)

Each function returns the matplotlib Figure object and also saves to FIGURES_DIR.

References for plot selection:
  - May (1972): phase-space stability boundary plot
  - Allesina & Tang (2012): stability domain visualisation
  - Sinha & de Weck (2013): complexity vs performance scatter
  - Standard network analysis: CDF, heatmap, violin comparisons
"""

import math
import warnings
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from matplotlib.colors import Normalize
from scipy import stats

import config
from src.utils import figure_path

matplotlib.use("Agg")   # non-interactive backend for script execution
warnings.filterwarnings("ignore", category=UserWarning)

# ── Shared style helper ────────────────────────────────────────────────────────

def _apply_style():
    try:
        plt.style.use(config.PLOT_STYLE)
    except OSError:
        plt.style.use("seaborn-v0_8-whitegrid")

TIER_COLORS = {
    "stable":       "#27AE60",
    "preservation": "#2ECC71",
    "precarious":   "#F39C12",
    "critical":     "#E74C3C",
    "collapse":     "#8E44AD",
}


def _save(fig: plt.Figure, fig_num: int, name: str):
    path = figure_path(fig_num, name)
    fig.savefig(path, dpi=config.FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    return path


# ── Helper: extract clean numeric arrays ──────────────────────────────────────

def _extract(results: list[dict], *keys) -> tuple:
    """
    Return aligned numpy arrays for the given keys, dropping rows with any None.
    """
    rows = [r for r in results if all(r.get(k) is not None for k in keys)]
    arrays = tuple(np.array([r[k] for r in rows], dtype=float) for k in keys)
    return arrays if len(keys) > 1 else arrays[0]


# ══════════════════════════════════════════════════════════════════════════════
# Fig 01 — TPI Distribution
# ══════════════════════════════════════════════════════════════════════════════

def plot_tpi_distribution(results: list[dict]) -> plt.Figure:
    """
    Histogram + KDE of TPI values across all designs.
    Vertical lines mark tier boundaries and the flag threshold.
    Rationale: primary sanity check; reveals the shape of the fragility landscape.
    """
    _apply_style()
    tpi = _extract(results, "tpi")

    fig, ax = plt.subplots(figsize=(9, 5))

    # Histogram
    n_bins = min(60, max(20, len(tpi) // 100))
    ax.hist(tpi, bins=n_bins, density=True, alpha=0.55,
            color=config.ACCENT_COLOR, edgecolor="white", linewidth=0.4,
            label="TPI frequency")

    # KDE overlay
    if len(tpi) > 2:
        kde = stats.gaussian_kde(tpi)
        xs  = np.linspace(tpi.min() - 0.05, min(tpi.max() + 0.05, 1.0), 300)
        ax.plot(xs, kde(xs), color=config.DANGER_COLOR, lw=2, label="KDE")

    # Tier boundary lines
    for label, (lo, hi) in config.TIERS.items():
        if 0 < hi < 1:
            ax.axvline(hi, color=TIER_COLORS[label], lw=1.2,
                       linestyle="--", alpha=0.8)
            ax.text(hi + 0.005, ax.get_ylim()[1] * 0.02,
                    label, fontsize=7, color=TIER_COLORS[label], rotation=90,
                    va="bottom")

    # Flag threshold
    ax.axvline(config.TPI_FLAG_THRESHOLD, color="black", lw=1.5,
               linestyle=":", label=f"Flag threshold ({config.TPI_FLAG_THRESHOLD})")

    ax.set_xlabel("Topological Precariousness Index (TPI)", fontsize=12)
    ax.set_ylabel("Density", fontsize=12)
    ax.set_title("Fig 01 — TPI Distribution Across AircraftVerse Designs\n"
                 f"(n = {len(tpi):,} designs)", fontsize=13, fontweight="bold")
    ax.legend(fontsize=9)
    ax.set_xlim(-0.05, 1.05)

    _save(fig, 1, "tpi_distribution")
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# Fig 02 — CDF of TPI
# ══════════════════════════════════════════════════════════════════════════════

def plot_tpi_cdf(results: list[dict]) -> plt.Figure:
    """
    Empirical CDF of TPI.
    Useful for threshold-setting: "what fraction of designs exceed TPI = X?"
    """
    _apply_style()
    tpi = np.sort(_extract(results, "tpi"))

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(tpi, np.arange(1, len(tpi) + 1) / len(tpi),
            color=config.ACCENT_COLOR, lw=2)

    ax.axvline(config.TPI_FLAG_THRESHOLD, color=config.DANGER_COLOR,
               lw=1.5, linestyle="--",
               label=f"Flag threshold ({config.TPI_FLAG_THRESHOLD})")

    frac_above = np.mean(tpi >= config.TPI_FLAG_THRESHOLD)
    ax.text(config.TPI_FLAG_THRESHOLD + 0.01, 0.5,
            f"{frac_above:.1%} flagged", fontsize=10,
            color=config.DANGER_COLOR, va="center")

    ax.set_xlabel("TPI", fontsize=12)
    ax.set_ylabel("Cumulative fraction of designs", fontsize=12)
    ax.set_title("Fig 02 — Empirical CDF of TPI", fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(0, 1.02)

    _save(fig, 2, "tpi_cdf")
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# Fig 03 — May-Wigner Phase Space (n vs rho)
# ══════════════════════════════════════════════════════════════════════════════

def plot_phase_space(results: list[dict]) -> plt.Figure:
    """
    Scatter of (n_nodes, rho) coloured by TPI.
    Overlays the May-Wigner stability boundary: rho = 1 / n
    (derived from sigma_critical = 1/sqrt(n*rho) = 1 → n*rho = 1).

    Rationale: directly shows which designs sit above/below the tipping boundary
    in the topological phase space. Core visualisation for the APM paper.
    """
    _apply_style()
    n_arr, rho_arr, tpi_arr = _extract(results, "n_nodes", "rho", "tpi")

    fig, ax = plt.subplots(figsize=(10, 7))
    sc = ax.scatter(n_arr, rho_arr, c=tpi_arr, cmap=config.COLOR_PALETTE,
                    s=4, alpha=0.6, vmin=0, vmax=1, rasterized=True)
    plt.colorbar(sc, ax=ax, label="TPI")

    # May-Wigner stability boundary: rho = 1/n  (sigma_critical = 1)
    n_range = np.linspace(max(n_arr.min(), 2), n_arr.max(), 500)
    rho_boundary = 1.0 / n_range
    ax.plot(n_range, rho_boundary, color=config.DANGER_COLOR,
            lw=2.5, linestyle="--", label=r"May-Wigner boundary: $\rho = 1/n$")

    ax.fill_between(n_range, rho_boundary, rho_arr.max() * 1.1,
                    alpha=0.07, color=config.DANGER_COLOR,
                    label="Precarious region (TPI > 0)")

    ax.set_xlabel("Number of nodes (n)", fontsize=12)
    ax.set_ylabel(r"Graph density ($\rho$)", fontsize=12)
    ax.set_title("Fig 03 — May-Wigner Phase Space\n"
                 r"Stability boundary: $\rho = 1/n$ (i.e. $\sigma\sqrt{n\rho}=1$)",
                 fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)

    _save(fig, 3, "phase_space_may_wigner")
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# Fig 04 — TPI vs Node Count
# ══════════════════════════════════════════════════════════════════════════════

def plot_tpi_vs_nodes(results: list[dict]) -> plt.Figure:
    """
    Scatter of TPI vs n_nodes with linear regression + outlier labels.
    Each point = one design. Top-5 highest and lowest TPI designs are labelled
    so individual designs can be identified directly from the plot.
    Shows whether larger designs are systematically more precarious
    (expected from TPI = 1 - 1/sqrt(n*rho)).
    """
    _apply_style()
    valid  = [r for r in results
              if r.get("n_nodes") is not None and r.get("tpi") is not None]
    n_arr  = np.array([r["n_nodes"] for r in valid], dtype=float)
    tpi_arr= np.array([r["tpi"]     for r in valid], dtype=float)
    labels = [r["design"]            for r in valid]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(n_arr, tpi_arr, s=5, alpha=0.4,
               color=config.ACCENT_COLOR, rasterized=True,
               label=f"Designs (n={len(valid):,})")

    # Regression
    slope, intercept, r_val, p, _ = stats.linregress(n_arr, tpi_arr)
    xs = np.linspace(n_arr.min(), n_arr.max(), 200)
    ax.plot(xs, slope * xs + intercept, color=config.DANGER_COLOR, lw=2,
            label=f"OLS  r²={r_val**2:.3f}  p={p:.2e}")

    ax.axhline(config.TPI_FLAG_THRESHOLD, color="black", lw=1.2,
               linestyle=":", alpha=0.7,
               label=f"Flag threshold ({config.TPI_FLAG_THRESHOLD})")

    # Label top-5 highest and lowest TPI designs
    _annotate_outliers(ax, n_arr, tpi_arr, labels, n=5)

    ax.set_xlabel("Number of nodes (n)  =  number of physical subsystems", fontsize=11)
    ax.set_ylabel("TPI", fontsize=11)
    ax.set_title("Fig 04 — TPI vs Node Count\n"
                 "Each point = one design; top/bottom 5 labelled",
                 fontsize=13, fontweight="bold")
    ax.legend(fontsize=9)

    _save(fig, 4, "tpi_vs_nodes")
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# Fig 05 — TPI vs Graph Density
# ══════════════════════════════════════════════════════════════════════════════

def plot_tpi_vs_density(results: list[dict]) -> plt.Figure:
    """
    Scatter of TPI vs rho, coloured by n_nodes.
    Disentangles the contribution of density vs size to precariousness.
    """
    _apply_style()
    rho_arr, tpi_arr, n_arr = _extract(results, "rho", "tpi", "n_nodes")

    fig, ax = plt.subplots(figsize=(9, 6))
    sc = ax.scatter(rho_arr, tpi_arr, c=n_arr, cmap="plasma",
                    s=5, alpha=0.5, rasterized=True)
    plt.colorbar(sc, ax=ax, label="Node count (n)")

    ax.axhline(config.TPI_FLAG_THRESHOLD, color=config.DANGER_COLOR,
               lw=1.5, linestyle="--",
               label=f"Flag threshold ({config.TPI_FLAG_THRESHOLD})")

    ax.set_xlabel(r"Graph density ($\rho$)", fontsize=12)
    ax.set_ylabel("TPI", fontsize=12)
    ax.set_title("Fig 05 — TPI vs Graph Density", fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)

    _save(fig, 5, "tpi_vs_density")
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# Fig 06-08 — TPI vs Performance Metrics
# ══════════════════════════════════════════════════════════════════════════════

def _plot_tpi_vs_metric(results, metric_key, metric_label,
                         fig_num, fig_name) -> plt.Figure:
    """Generic TPI vs performance scatter with airworthy colouring."""
    _apply_style()
    rows = [r for r in results
            if r.get("tpi") is not None and r.get(metric_key) is not None]
    if not rows:
        return None

    tpi_arr  = np.array([r["tpi"] for r in rows])
    met_arr  = np.array([r[metric_key] for r in rows], dtype=float)
    aw_arr   = np.array([r.get("airworthy") for r in rows])

    fig, ax  = plt.subplots(figsize=(9, 6))

    # Split airworthy / non-airworthy
    mask_aw  = aw_arr == 1
    mask_naw = aw_arr == 0
    mask_unk = ~(mask_aw | mask_naw)

    if mask_aw.any():
        ax.scatter(tpi_arr[mask_aw],  met_arr[mask_aw],
                   s=5, alpha=0.5, color=config.SAFE_COLOR,
                   label="Airworthy", rasterized=True)
    if mask_naw.any():
        ax.scatter(tpi_arr[mask_naw], met_arr[mask_naw],
                   s=5, alpha=0.5, color=config.DANGER_COLOR,
                   label="Non-airworthy", rasterized=True)
    if mask_unk.any():
        ax.scatter(tpi_arr[mask_unk], met_arr[mask_unk],
                   s=5, alpha=0.3, color="grey",
                   label="Unknown", rasterized=True)

    ax.axvline(config.TPI_FLAG_THRESHOLD, color="black", lw=1.2,
               linestyle=":", alpha=0.7,
               label=f"Flag threshold ({config.TPI_FLAG_THRESHOLD})")

    ax.set_xlabel("TPI", fontsize=12)
    ax.set_ylabel(metric_label, fontsize=12)
    ax.set_title(f"Fig {fig_num:02d} — TPI vs {metric_label}",
                 fontsize=13, fontweight="bold")
    ax.legend(fontsize=9, markerscale=3)

    _save(fig, fig_num, fig_name)
    return fig


def plot_tpi_vs_hover_time(results):
    return _plot_tpi_vs_metric(results, "hover_time", "Hover Time (s)",
                                6, "tpi_vs_hover_time")

def plot_tpi_vs_max_speed(results):
    return _plot_tpi_vs_metric(results, "max_speed", "Max Speed (m/s)",
                                7, "tpi_vs_max_speed")

def plot_tpi_vs_max_distance(results):
    return _plot_tpi_vs_metric(results, "max_distance", "Max Distance (m)",
                                8, "tpi_vs_max_distance")


# ══════════════════════════════════════════════════════════════════════════════
# Fig 09 — Second-Stage Discriminator Quadrant
# ══════════════════════════════════════════════════════════════════════════════

def plot_quadrant(results: list[dict],
                  perf_key: str   = "hover_time",
                  perf_label: str = "Hover Time (s)") -> plt.Figure:
    """
    Performance × Precariousness quadrant plot — Table 2 of APM paper.

    Quadrant definition (medians as decision boundaries):
      Q1 (top-left):  High perf, Low TPI  → Preferred
      Q2 (top-right): High perf, High TPI → Caution
      Q3 (bot-left):  Low perf,  Low TPI  → Robustness reserve
      Q4 (bot-right): Low perf,  High TPI → Eliminate
    """
    _apply_style()
    rows = [r for r in results
            if r.get("tpi") is not None and r.get(perf_key) is not None]
    if not rows:
        return None

    tpi_arr  = np.array([r["tpi"] for r in rows])
    perf_arr = np.array([r[perf_key] for r in rows], dtype=float)

    tpi_med  = np.median(tpi_arr)
    perf_med = np.median(perf_arr)

    fig, ax  = plt.subplots(figsize=(9, 7))

    # Shade quadrants
    xmin, xmax = tpi_arr.min() - 0.05, min(tpi_arr.max() + 0.05, 1.05)
    ymin, ymax = perf_arr.min(), perf_arr.max() * 1.05

    ax.fill_between([xmin, tpi_med], [perf_med, perf_med], [ymax, ymax],
                    color=config.SAFE_COLOR,   alpha=0.10)   # Q1 Preferred
    ax.fill_between([tpi_med, xmax], [perf_med, perf_med], [ymax, ymax],
                    color="#F39C12", alpha=0.10)              # Q2 Caution
    ax.fill_between([xmin, tpi_med], [ymin, ymin], [perf_med, perf_med],
                    color=config.ACCENT_COLOR, alpha=0.10)   # Q3 Reserve
    ax.fill_between([tpi_med, xmax], [ymin, ymin], [perf_med, perf_med],
                    color=config.DANGER_COLOR, alpha=0.10)   # Q4 Eliminate

    ax.scatter(tpi_arr, perf_arr, s=5, alpha=0.4,
               color="steelblue", rasterized=True)

    ax.axvline(tpi_med,  color="black", lw=1.3, linestyle="--", alpha=0.7)
    ax.axhline(perf_med, color="black", lw=1.3, linestyle="--", alpha=0.7)

    # Quadrant labels
    for x, y, txt, ha, va in [
        (xmin + 0.02, ymax * 0.97, "PREFERRED\n(High perf, Low TPI)", "left", "top"),
        (xmax - 0.02, ymax * 0.97, "CAUTION\n(High perf, High TPI)", "right", "top"),
        (xmin + 0.02, ymin * 1.03, "ROBUSTNESS\nRESERVE",            "left", "bottom"),
        (xmax - 0.02, ymin * 1.03, "ELIMINATE\n(Low perf, High TPI)","right","bottom"),
    ]:
        ax.text(x, y, txt, fontsize=8, ha=ha, va=va, alpha=0.75,
                fontweight="bold")

    ax.set_xlabel("TPI (← low precariousness     high precariousness →)", fontsize=11)
    ax.set_ylabel(perf_label, fontsize=11)
    ax.set_title("Fig 09 — Second-Stage Discriminator Quadrant\n"
                 "(Table 2, APM Paper)", fontsize=13, fontweight="bold")

    _save(fig, 9, "quadrant_discriminator")
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# Fig 10 — Airworthy vs Non-Airworthy TPI Comparison
# ══════════════════════════════════════════════════════════════════════════════

def plot_tpi_airworthy_comparison(results: list[dict]) -> plt.Figure:
    """
    Violin + strip plot comparing TPI distributions for airworthy vs non-airworthy.
    Tests hypothesis: precarious architectures are more likely to fail airworthiness.
    """
    _apply_style()
    aw_tpi  = [r["tpi"] for r in results
               if r.get("airworthy") == 1 and r.get("tpi") is not None]
    naw_tpi = [r["tpi"] for r in results
               if r.get("airworthy") == 0 and r.get("tpi") is not None]

    if not aw_tpi or not naw_tpi:
        # Fallback: just show single distribution
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.text(0.5, 0.5, "Airworthy labels not available in this subset.",
                ha="center", va="center", transform=ax.transAxes)
        _save(fig, 10, "tpi_airworthy_comparison")
        return fig

    fig, ax = plt.subplots(figsize=(7, 6))

    data   = [np.array(aw_tpi), np.array(naw_tpi)]
    labels = ["Airworthy\n(n={:,})".format(len(aw_tpi)),
              "Non-airworthy\n(n={:,})".format(len(naw_tpi))]
    colors = [config.SAFE_COLOR, config.DANGER_COLOR]

    parts  = ax.violinplot(data, positions=[1, 2], showmedians=True,
                           showextrema=True)
    for pc, color in zip(parts["bodies"], colors):
        pc.set_facecolor(color)
        pc.set_alpha(0.65)
    parts["cmedians"].set_color("black")

    # Overlay box plot
    ax.boxplot(data, positions=[1, 2], widths=0.15,
               patch_artist=False, showfliers=False,
               medianprops=dict(color="black", lw=2))

    # Mann-Whitney U test
    stat, p = stats.mannwhitneyu(aw_tpi, naw_tpi, alternative="two-sided")
    ax.text(0.5, 0.97, f"Mann-Whitney U  p = {p:.3e}",
            transform=ax.transAxes, ha="center", va="top", fontsize=10,
            style="italic")

    ax.set_xticks([1, 2])
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel("TPI", fontsize=12)
    ax.set_title("Fig 10 — TPI: Airworthy vs Non-Airworthy",
                 fontsize=13, fontweight="bold")
    ax.axhline(config.TPI_FLAG_THRESHOLD, color="black", lw=1.2,
               linestyle=":", alpha=0.7,
               label=f"Flag threshold ({config.TPI_FLAG_THRESHOLD})")
    ax.legend(fontsize=9)

    _save(fig, 10, "tpi_airworthy_comparison")
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# Fig 11 — Fragility Tier Breakdown
# ══════════════════════════════════════════════════════════════════════════════

def plot_tier_breakdown(results: list[dict]) -> plt.Figure:
    """
    Horizontal stacked bar showing proportion of designs in each fragility tier.
    Aligns directly with Table 1 (ACR regimes) of the APM paper.
    """
    _apply_style()
    tier_order  = ["stable", "preservation", "precarious", "critical", "collapse"]
    tier_labels = {
        "stable":       "Stable / Synergistic (TPI ≤ 0)",
        "preservation": "Preservation  (0 < TPI ≤ 0.3)",
        "precarious":   "Precarious  (0.3 < TPI ≤ 0.7)",
        "critical":     "Critical  (0.7 < TPI ≤ 0.9)",
        "collapse":     "Collapse / Tipping  (TPI > 0.9)",
    }

    counts = {t: sum(1 for r in results if r.get("tier") == t)
              for t in tier_order}
    total  = sum(counts.values()) or 1
    fracs  = [counts[t] / total for t in tier_order]

    fig, ax = plt.subplots(figsize=(10, 3))

    left = 0.0
    for tier, frac in zip(tier_order, fracs):
        if frac > 0:
            bar = ax.barh(0, frac, left=left, color=TIER_COLORS[tier],
                          edgecolor="white", linewidth=0.8, height=0.55)
            if frac > 0.04:
                ax.text(left + frac / 2, 0, f"{frac:.1%}",
                        ha="center", va="center", fontsize=9,
                        fontweight="bold", color="white")
            left += frac

    patches = [mpatches.Patch(color=TIER_COLORS[t],
                               label=f"{tier_labels[t]}  n={counts[t]:,}")
               for t in tier_order]
    ax.legend(handles=patches, loc="upper center",
              bbox_to_anchor=(0.5, -0.35), ncol=2, fontsize=9)

    ax.set_xlim(0, 1)
    ax.set_yticks([])
    ax.set_xlabel("Fraction of designs", fontsize=11)
    ax.set_title("Fig 11 — Fragility Tier Breakdown  (total={:,})".format(
        sum(counts.values())), fontsize=13, fontweight="bold")

    _save(fig, 11, "tier_breakdown")
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# Fig 12 — Correlation Heatmap
# ══════════════════════════════════════════════════════════════════════════════

def plot_correlation_heatmap(results: list[dict]) -> plt.Figure:
    """
    Pearson correlation heatmap across TPI metrics and performance outputs.
    Reveals which structural features predict performance fragility.
    """
    _apply_style()
    keys = ["n_nodes", "m_edges", "rho", "sigma_critical",
            "tpi", "hover_time", "max_speed", "max_distance"]

    # Build aligned data matrix (drop rows with any None)
    clean = [r for r in results
             if all(r.get(k) is not None and r.get(k) != float("inf")
                    for k in keys)]
    if len(clean) < 5:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, "Insufficient data for correlation heatmap.",
                ha="center", va="center", transform=ax.transAxes)
        _save(fig, 12, "correlation_heatmap")
        return fig

    matrix = np.array([[r[k] for k in keys] for r in clean], dtype=float)
    corr   = np.corrcoef(matrix.T)

    nice_labels = ["n nodes", "m edges", "ρ density", "σ_critical",
                   "TPI", "Hover time", "Max speed", "Max distance"]

    fig, ax = plt.subplots(figsize=(9, 8))
    im = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1, aspect="auto")
    plt.colorbar(im, ax=ax, label="Pearson r")

    ax.set_xticks(range(len(keys)))
    ax.set_yticks(range(len(keys)))
    ax.set_xticklabels(nice_labels, rotation=45, ha="right", fontsize=10)
    ax.set_yticklabels(nice_labels, fontsize=10)

    for i in range(len(keys)):
        for j in range(len(keys)):
            ax.text(j, i, f"{corr[i, j]:.2f}", ha="center", va="center",
                    fontsize=8,
                    color="white" if abs(corr[i, j]) > 0.65 else "black")

    ax.set_title(f"Fig 12 — Correlation Heatmap  (n={len(clean):,} designs)\n"
                 "TPI metrics × performance outputs",
                 fontsize=13, fontweight="bold")

    _save(fig, 12, "correlation_heatmap")
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# Fig 13 — Ranked Design TPI Chart (all designs, sorted by TPI)
# ══════════════════════════════════════════════════════════════════════════════

def plot_ranked_designs(results: list[dict], top_n: int = 30) -> plt.Figure:
    """
    Horizontal bar chart showing top-N most precarious and top-N most stable
    designs by TPI, with design IDs labeled.
    Answers: "Which specific design has highest/lowest TPI?"
    """
    _apply_style()
    valid = sorted(
        [r for r in results if r.get("tpi") is not None],
        key=lambda r: r["tpi"]
    )
    if not valid:
        return None

    most_precarious = valid[-top_n:][::-1]   # highest TPI first
    most_stable     = valid[:top_n]           # lowest TPI first

    fig, axes = plt.subplots(1, 2, figsize=(14, max(6, top_n * 0.35)))

    for ax, group, title, color in [
        (axes[0], most_precarious,
         f"Top {top_n} Most Precarious (highest TPI)", config.DANGER_COLOR),
        (axes[1], most_stable,
         f"Top {top_n} Most Stable (lowest TPI)",      config.SAFE_COLOR),
    ]:
        designs = [r["design"] for r in group]
        tpis    = [r["tpi"]    for r in group]
        ys      = range(len(designs))

        bars = ax.barh(ys, tpis, color=color, alpha=0.75, edgecolor="white")
        ax.set_yticks(ys)
        ax.set_yticklabels(designs, fontsize=7)
        ax.set_xlabel("TPI", fontsize=11)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.axvline(config.TPI_FLAG_THRESHOLD, color="black",
                   lw=1.2, linestyle=":", alpha=0.6)

        # Value labels on bars
        for bar, tpi_val in zip(bars, tpis):
            ax.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height() / 2,
                    f"{tpi_val:.3f}", va="center", fontsize=7)

        ax.set_xlim(0, 1.05)
        ax.invert_yaxis()

    fig.suptitle(f"Fig 13 — Ranked Design TPI  (total corpus = {len(valid):,})",
                 fontsize=13, fontweight="bold", y=1.01)
    plt.tight_layout()

    _save(fig, 13, "ranked_designs_tpi")
    return fig


# ── Helper: annotate outliers in scatter plots ────────────────────────────────

def _annotate_outliers(ax, x_arr, y_arr, labels, n=5):
    """Label the top-n highest and lowest TPI points with design names."""
    idx_sorted = np.argsort(y_arr)
    for idx in list(idx_sorted[:n]) + list(idx_sorted[-n:]):
        ax.annotate(
            labels[idx],
            (x_arr[idx], y_arr[idx]),
            fontsize=6, alpha=0.8,
            xytext=(4, 2), textcoords="offset points",
            color=config.DANGER_COLOR if y_arr[idx] > np.median(y_arr) else config.SAFE_COLOR,
        )


# ══════════════════════════════════════════════════════════════════════════════
# Master plot runner
# ══════════════════════════════════════════════════════════════════════════════

def generate_all_plots(results: list[dict], logger=None) -> list[str]:
    """
    Run all 12 plots in sequence. Returns list of saved file paths.
    """
    plot_fns = [
        ("Fig 01 — TPI Distribution",          lambda: plot_tpi_distribution(results)),
        ("Fig 02 — TPI CDF",                   lambda: plot_tpi_cdf(results)),
        ("Fig 03 — May-Wigner Phase Space",     lambda: plot_phase_space(results)),
        ("Fig 04 — TPI vs Node Count",          lambda: plot_tpi_vs_nodes(results)),
        ("Fig 05 — TPI vs Graph Density",       lambda: plot_tpi_vs_density(results)),
        ("Fig 06 — TPI vs Hover Time",          lambda: plot_tpi_vs_hover_time(results)),
        ("Fig 07 — TPI vs Max Speed",           lambda: plot_tpi_vs_max_speed(results)),
        ("Fig 08 — TPI vs Max Distance",        lambda: plot_tpi_vs_max_distance(results)),
        ("Fig 09 — Quadrant Discriminator",     lambda: plot_quadrant(results)),
        ("Fig 10 — Airworthy Comparison",       lambda: plot_tpi_airworthy_comparison(results)),
        ("Fig 11 — Tier Breakdown",             lambda: plot_tier_breakdown(results)),
        ("Fig 12 — Correlation Heatmap",        lambda: plot_correlation_heatmap(results)),
        ("Fig 13 — Ranked Design TPI",          lambda: plot_ranked_designs(results)),
    ]

    saved_paths = []
    for name, fn in plot_fns:
        try:
            fn()
            if logger:
                logger.info(f"  Saved: {name}")
        except Exception as e:
            if logger:
                logger.warning(f"  SKIPPED {name}: {e}")

    # Collect actual saved paths
    for i, (name, _) in enumerate(plot_fns, start=1):
        short = name.split("—")[1].strip().lower().replace(" ", "_")
        p = figure_path(i, short)
        if __import__("os").path.exists(p):
            saved_paths.append(p)

    return saved_paths
