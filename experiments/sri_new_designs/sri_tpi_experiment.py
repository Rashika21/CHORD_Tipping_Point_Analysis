"""
TPI Experiment — SRI New Designs
Date: 2026-06-18
Dataset: ga_designs.json (17,387 GA-optimised UAV designs across 200 target groups)
Pipeline mirrors the AircraftVerse 7-stage analysis.
"""

import json
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import os
from collections import Counter

# ── Paths ──────────────────────────────────────────────────────────────────
INPUT_JSON  = "/sessions/clever-vibrant-euler/mnt/outputs/ga_designs.json"
OUTPUT_DIR  = "/sessions/clever-vibrant-euler/mnt/Tipping point/TPI_Analysis/outputs/2026_06_18_SRI_new_designs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Hub configuration: (segment_key, replication_count) ───────────────────
HUB_ARMS = {
    "ConnectedHub6_Sym":        [("mainSegment",       6)],
    "ConnectedHub6_Sym_Aligned":[("mainSegment",       6)],
    "ConnectedHub4_Sym":        [("mainSegment",       4)],
    "ConnectedHub4_Sym_Aligned":[("mainSegment",       4)],
    "ConnectedHub2_Sym_Wide":   [("mainSegment",       2)],
    "ConnectedHub4_2_2":        [("frontSegment",      2), ("rearSegment",        2)],
    "ConnectedHub4_1_2_1":      [("frontSegment",      1), ("middleSegment",      2), ("rearSegment",  1)],
    "ConnectedHub6_2_2_2":      [("frontSegment",      2), ("middleSegment",      2), ("rearSegment",  2)],
    "ConnectedHub6_1_2_2_1":    [("frontCenterSegment",1), ("frontSegment",       2),
                                 ("rearSegment",       2), ("rearCenterSegment",  1)],
}

def extract_graph(design: dict):
    """
    Build the coupling graph for a single design.
    Returns (n_nodes, n_edges).

    Node taxonomy
    ─────────────
    fuselage  : central body
    hub       : arm attachment point (parent: fuselage)
    battery   : 1 or 2 (parent: fuselage)
    per arm instance:
      arm     : PropArm / AngledPropArm / AngledWingArm (parent: hub)
      motor   : if PropArm or AngledPropArm (parent: arm)
      prop    : if PropArm or AngledPropArm (parent: motor)
      wing    : if AngledWingArm (parent: arm)
      servo   : if AngledWingArm (parent: arm)
    """
    n_nodes = 0
    n_edges = 0

    # fuselage + hub + fuselage–hub edge
    n_nodes += 2
    n_edges += 1

    # batteries
    fuse_type = design["fuselageWithComponents"]["node_type"]
    n_bat = 2 if "Dual" in fuse_type else 1
    n_nodes += n_bat
    n_edges += n_bat   # fuselage → battery (×n_bat)

    # arms
    hub_type = design["hub"]["node_type"]
    arm_configs = HUB_ARMS.get(hub_type, [])

    for seg_key, count in arm_configs:
        seg_data = design["hub"].get(seg_key, {})
        arm_node_type = seg_data.get("node_type", "PropArm")

        for _ in range(count):
            n_nodes += 1          # arm node
            n_edges += 1          # hub → arm

            if arm_node_type == "AngledWingArm":
                n_nodes += 2      # wing + servo
                n_edges += 2      # arm → wing, arm → servo
            else:                 # PropArm, AngledPropArm
                n_nodes += 2      # motor + prop
                n_edges += 2      # arm → motor → prop

    return n_nodes, n_edges


def compute_tpi(n: int, m: int) -> tuple:
    """Returns (rho, sigma_critical, TPI)."""
    if n < 2:
        return (0.0, 1.0, 0.0)
    rho = 2 * m / (n * (n - 1))
    if rho <= 0:
        return (rho, 1.0, 0.0)
    sigma_crit = 1.0 / math.sqrt(n * rho)
    tpi = 1.0 - sigma_crit
    return (rho, sigma_crit, tpi)


def fragility_tier(tpi: float) -> str:
    if tpi <= 0.00: return "Stable"
    if tpi <= 0.30: return "Preservation"
    if tpi <= 0.70: return "Precarious"
    if tpi <= 0.90: return "Critical"
    return "Collapse"


# ── Stage 1–4: Load, extract graph, compute TPI ───────────────────────────
print("Loading ga_designs.json ...")
with open(INPUT_JSON) as f:
    raw = json.load(f)

records = []
for group in raw:
    tm = group["target_metrics"]
    for d in group["designs"]:
        n, m = extract_graph(d)
        rho, sigma_crit, tpi = compute_tpi(n, m)
        records.append({
            "name":          d["name"],
            "hub_type":      d["hub"]["node_type"],
            "fuselage_type": d["fuselageWithComponents"]["node_type"],
            "n":             n,
            "m":             m,
            "rho":           rho,
            "sigma_critical":sigma_crit,
            "TPI":           tpi,
            "tier":          fragility_tier(tpi),
            "hover_time":    tm["hover_time"],
            "max_speed":     tm["max_speed"],
            "max_distance":  tm["max_distance"],
        })

df = pd.DataFrame(records)
total = len(df)
print(f"Total designs processed: {total}")
print(f"\nTPI stats:\n{df['TPI'].describe()}")
print(f"\nTier distribution:\n{df['tier'].value_counts()}")
print(f"\nHub type distribution:\n{df['hub_type'].value_counts()}")
print(f"\nn range: {df['n'].min()}–{df['n'].max()}, median={df['n'].median()}")
print(f"rho range: {df['rho'].min():.4f}–{df['rho'].max():.4f}")
print(f"n×rho stats: min={( df['n']*df['rho']).min():.3f}, max={(df['n']*df['rho']).max():.3f}, mean={(df['n']*df['rho']).mean():.3f}")

# Save CSV
csv_path = os.path.join(OUTPUT_DIR, "sri_tpi_results.csv")
df.to_csv(csv_path, index=False)
print(f"\nResults saved: {csv_path}")

# ── Plot helpers ───────────────────────────────────────────────────────────
TIER_COLORS = {
    "Stable":       "#2ecc71",
    "Preservation": "#3498db",
    "Precarious":   "#e67e22",
    "Critical":     "#e74c3c",
    "Collapse":     "#8e44ad",
}
TIER_ORDER   = ["Stable","Preservation","Precarious","Critical","Collapse"]
TIER_BOUNDS  = [0.00, 0.30, 0.70, 0.90, 1.00]

FIG_DPI  = 150
SAVEKW   = dict(dpi=FIG_DPI, bbox_inches="tight")

def save(fig, name):
    p = os.path.join(OUTPUT_DIR, name)
    fig.savefig(p, **SAVEKW)
    plt.close(fig)
    print(f"  Saved: {name}")


# ── S1: Design Space — rho vs n ────────────────────────────────────────────
print("\nGenerating figures ...")
fig, ax = plt.subplots(figsize=(8, 5))
sc = ax.scatter(df["n"], df["rho"], c=df["TPI"], cmap="coolwarm",
                alpha=0.4, s=8, linewidths=0)
cb = fig.colorbar(sc, ax=ax)
cb.set_label("TPI", fontsize=11)
ax.set_xlabel("Component Count (n)", fontsize=12)
ax.set_ylabel("Graph Density (ρ)", fontsize=12)
ax.set_title("Design Space: Graph Density vs Component Count\n(SRI New Designs, n=17,387)", fontsize=12)
ax.grid(True, alpha=0.3)
save(fig, "S1_design_space_rho_vs_n.png")


# ── S2a: TPI vs Graph Density with analytic curves ────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))

# Unique n values in corpus for curves
n_vals   = sorted(df["n"].unique())
n_curve_candidates = [min(n_vals), int(np.median(n_vals)),
                      int(np.percentile(n_vals, 75)), max(n_vals)]
n_curves = sorted(set(n_curve_candidates))

curve_styles = [(":",  "#2ecc71"),("-.", "#3498db"),("--","#e74c3c"),("-","#9b59b6")]
rho_range = np.linspace(0.001, df["rho"].max()*1.1, 400)

ax.scatter(df["rho"], df["TPI"], c=df["n"], cmap="plasma",
           alpha=0.35, s=8, linewidths=0)
sm = plt.cm.ScalarMappable(cmap="plasma",
     norm=plt.Normalize(vmin=df["n"].min(), vmax=df["n"].max()))
sm.set_array([])
cb = fig.colorbar(sm, ax=ax)
cb.set_label("Component Count (n)", fontsize=10)

for (ls, col), nv in zip(curve_styles, n_curves):
    tpi_curve = 1 - 1/np.sqrt(nv * rho_range)
    tpi_curve = np.clip(tpi_curve, -1, 1)
    ax.plot(rho_range, tpi_curve, ls=ls, color=col, lw=1.8,
            label=f"$n={nv}$")

for tb in [0.0, 0.30, 0.70, 0.90]:
    ax.axhline(tb, color="grey", lw=0.7, ls="--", alpha=0.5)

ax.set_xlabel("Graph Density (ρ)", fontsize=12)
ax.set_ylabel("Topological Precariousness Index (TPI)", fontsize=12)
ax.set_title("TPI vs Graph Density\n(SRI New Designs)", fontsize=12)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)
save(fig, "S2a_tpi_vs_graph_density.png")


# ── S2b: TPI vs Component Count ────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
sc = ax.scatter(df["n"], df["TPI"], c=df["rho"], cmap="viridis",
                alpha=0.4, s=8, linewidths=0)
cb = fig.colorbar(sc, ax=ax)
cb.set_label("Graph Density (ρ)", fontsize=10)
for tb, lbl in zip([0.0, 0.30, 0.70, 0.90],
                   ["Stable|Preservation","Preservation|Precarious",
                    "Precarious|Critical","Critical|Collapse"]):
    ax.axhline(tb, color="grey", lw=0.7, ls="--", alpha=0.6)
    ax.text(df["n"].max()*0.97, tb+0.01, lbl, ha="right",
            fontsize=7, color="grey")
ax.set_xlabel("Component Count (n)", fontsize=12)
ax.set_ylabel("Topological Precariousness Index (TPI)", fontsize=12)
ax.set_title("TPI vs Component Count\n(SRI New Designs)", fontsize=12)
ax.grid(True, alpha=0.3)
save(fig, "S2b_tpi_vs_component_count.png")


# ── S3: TPI Distribution ───────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# TPI histogram coloured by tier
ax = axes[0]
tpi_vals = df["TPI"].values
bins = np.linspace(tpi_vals.min()-0.005, tpi_vals.max()+0.005, 40)
for tier in TIER_ORDER:
    sub = df[df["tier"] == tier]["TPI"].values
    if len(sub):
        ax.hist(sub, bins=bins, color=TIER_COLORS[tier],
                alpha=0.8, label=tier, edgecolor="white", linewidth=0.3)
ax.set_xlabel("TPI", fontsize=12)
ax.set_ylabel("Count", fontsize=12)
ax.set_title("TPI Distribution by Fragility Tier", fontsize=12)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# rho distribution
ax = axes[1]
ax.hist(df["rho"].values, bins=40, color="#3498db", alpha=0.8, edgecolor="white")
ax.set_xlabel("Graph Density (ρ)", fontsize=12)
ax.set_ylabel("Count", fontsize=12)
ax.set_title("Graph Density Distribution", fontsize=12)
ax.grid(True, alpha=0.3)

fig.suptitle("SRI New Designs — TPI and Density Distributions", fontsize=13, y=1.02)
save(fig, "S3_tpi_density_distribution.png")


# ── S4–S6: Quadrant analysis (hover, distance, speed) ─────────────────────
med_tpi   = df["TPI"].median()
med_hover = df["hover_time"].median()
med_dist  = df["max_distance"].median()
med_speed = df["max_speed"].median()

print(f"\nMedians — TPI:{med_tpi:.4f}  hover:{med_hover:.1f}s  "
      f"dist:{med_dist:.0f}m  speed:{med_speed:.1f}m/s")

QUAD_COLORS = {
    "Optimal":             "#27ae60",
    "Precarious Performer":"#e74c3c",
    "Stable Modest":       "#3498db",
    "Double Liability":    "#95a5a6",
}

def quadrant_label(tpi, perf, med_tpi, med_perf):
    lo_tpi  = tpi  <= med_tpi
    hi_perf = perf >  med_perf
    if lo_tpi and hi_perf:     return "Optimal"
    if (not lo_tpi) and hi_perf: return "Precarious Performer"
    if lo_tpi and (not hi_perf): return "Stable Modest"
    return "Double Liability"

def quad_plot(ax, x_vals, y_vals, n_vals, med_x, med_y,
              xlabel, ylabel, title, log_y=False):
    q_labels = [quadrant_label(xi, yi, med_x, med_y)
                for xi, yi in zip(x_vals, y_vals)]
    for ql, col in QUAD_COLORS.items():
        mask = [l == ql for l in q_labels]
        ax.scatter(x_vals[mask], y_vals[mask], c=n_vals[mask],
                   cmap="plasma", alpha=0.4, s=8, linewidths=0,
                   vmin=df["n"].min(), vmax=df["n"].max())
    ax.axvline(med_x, color="black", lw=1.2, ls="--")
    ax.axhline(med_y, color="black", lw=1.2, ls="--")
    if log_y:
        ax.set_yscale("log")
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.set_title(title, fontsize=11)
    ax.grid(True, alpha=0.3)
    counts = Counter(q_labels)
    legend_entries = [
        plt.scatter([], [], c=QUAD_COLORS[ql], s=30, label=f"{ql} (n={counts.get(ql,0)})")
        for ql in QUAD_COLORS
    ]
    ax.legend(handles=legend_entries, fontsize=7, loc="upper left")

n_arr    = df["n"].values
tpi_arr  = df["TPI"].values
hover_arr = df["hover_time"].values
dist_arr  = df["max_distance"].values
speed_arr = df["max_speed"].values

# S4 — hover
fig, ax = plt.subplots(figsize=(8, 6))
quad_plot(ax, tpi_arr, hover_arr, n_arr, med_tpi, med_hover,
          "TPI", "Hover Time (s)",
          "Hover Time vs TPI\n(SRI New Designs, all designs)")
sm = plt.cm.ScalarMappable(cmap="plasma",
     norm=plt.Normalize(vmin=df["n"].min(), vmax=df["n"].max()))
sm.set_array([]); fig.colorbar(sm, ax=ax, label="Component Count (n)")
save(fig, "S4_quadrant_hover_time.png")

# S5 — max distance (log scale)
fig, ax = plt.subplots(figsize=(8, 6))
quad_plot(ax, tpi_arr, dist_arr, n_arr, med_tpi, med_dist,
          "TPI", "Max Distance (m)",
          "Maximum Range vs TPI\n(SRI New Designs, all designs)", log_y=True)
sm = plt.cm.ScalarMappable(cmap="plasma",
     norm=plt.Normalize(vmin=df["n"].min(), vmax=df["n"].max()))
sm.set_array([]); fig.colorbar(sm, ax=ax, label="Component Count (n)")
save(fig, "S5_quadrant_max_distance.png")

# S6 — max speed
fig, ax = plt.subplots(figsize=(8, 6))
quad_plot(ax, tpi_arr, speed_arr, n_arr, med_tpi, med_speed,
          "TPI", "Max Speed (m/s)",
          "Maximum Speed vs TPI\n(SRI New Designs, all designs)")
sm = plt.cm.ScalarMappable(cmap="plasma",
     norm=plt.Normalize(vmin=df["n"].min(), vmax=df["n"].max()))
sm.set_array([]); fig.colorbar(sm, ax=ax, label="Component Count (n)")
save(fig, "S6_quadrant_max_speed.png")


# ── S7: Composite Performance Score ────────────────────────────────────────
def minmax(arr):
    lo, hi = arr.min(), arr.max()
    return (arr - lo) / (hi - lo) if hi > lo else arr * 0.0

norm_hover = minmax(hover_arr)
norm_speed = minmax(speed_arr)
norm_dist  = minmax(dist_arr)
composite  = (norm_hover + norm_speed + norm_dist) / 3.0

med_comp = np.median(composite)
print(f"Composite score range: {composite.min():.3f}–{composite.max():.3f}, median={med_comp:.3f}")

fig, ax = plt.subplots(figsize=(8, 6))
sc = ax.scatter(tpi_arr, composite, c=n_arr, cmap="coolwarm",
                alpha=0.35, s=8, linewidths=0,
                vmin=df["n"].min(), vmax=df["n"].max())
ax.axvline(med_tpi,  color="black", lw=1.2, ls="--", label=f"Median TPI={med_tpi:.3f}")
ax.axhline(med_comp, color="navy",  lw=1.2, ls="--", label=f"Median P={med_comp:.3f}")
fig.colorbar(sc, ax=ax, label="Component Count (n)")
ax.set_xlabel("TPI", fontsize=12)
ax.set_ylabel("Composite Performance Score (P)", fontsize=12)
ax.set_title("Composite Performance vs TPI\n(SRI New Designs)", fontsize=12)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)
save(fig, "S7_tpi_vs_composite_performance.png")


# ── S8: Hub-Type TPI comparison ────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))
hub_order = df.groupby("hub_type")["TPI"].median().sort_values().index.tolist()
data_by_hub = [df[df["hub_type"] == ht]["TPI"].values for ht in hub_order]
bp = ax.boxplot(data_by_hub, labels=[h.replace("ConnectedHub","Hub") for h in hub_order],
                patch_artist=True, notch=False,
                boxprops=dict(facecolor="#3498db", alpha=0.6),
                medianprops=dict(color="red", lw=2))
ax.axhline(0.30, color="orange", lw=1.2, ls="--", label="Precarious threshold (0.30)")
ax.axhline(0.00, color="green",  lw=1.0, ls=":",  label="Stable threshold (0.00)")
ax.set_xlabel("Hub Type", fontsize=11)
ax.set_ylabel("TPI", fontsize=12)
ax.set_title("TPI Distribution by Hub Type\n(SRI New Designs)", fontsize=12)
ax.legend(fontsize=9)
ax.tick_params(axis='x', rotation=25)
ax.grid(True, alpha=0.3, axis='y')
save(fig, "S8_tpi_by_hub_type.png")


# ── S9: TPI vs n×rho scatter (assembly constraint) ────────────────────────
n_rho = df["n"].values * df["rho"].values
fig, ax = plt.subplots(figsize=(8, 5))
sc = ax.scatter(df["rho"].values, n_rho, c=df["TPI"].values,
                cmap="coolwarm", alpha=0.4, s=8, linewidths=0)
fig.colorbar(sc, ax=ax, label="TPI")
ax.axhline(2.0,  color="green",  lw=1.5, ls="--", label="Perfect tree (n·ρ = 2.0)")
ax.axhline(2.29, color="orange", lw=1.5, ls="--", label="AircraftVerse corpus (n·ρ ≈ 2.29)")
ax.set_xlabel("Graph Density (ρ)", fontsize=12)
ax.set_ylabel("n × ρ", fontsize=12)
ax.set_title("Design Topology Constraint: n·ρ vs Graph Density\n(SRI New Designs vs AircraftVerse)", fontsize=12)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)
save(fig, "S9_design_density_vs_rho.png")


# ── Summary statistics CSV ──────────────────────────────────────────────────
summary = {
    "total_designs":        total,
    "n_min":                int(df["n"].min()),
    "n_max":                int(df["n"].max()),
    "n_median":             float(df["n"].median()),
    "rho_min":              float(df["rho"].min()),
    "rho_max":              float(df["rho"].max()),
    "TPI_min":              float(df["TPI"].min()),
    "TPI_max":              float(df["TPI"].max()),
    "TPI_median":           float(df["TPI"].median()),
    "TPI_range":            float(df["TPI"].max() - df["TPI"].min()),
    "n_rho_min":            float((df["n"]*df["rho"]).min()),
    "n_rho_max":            float((df["n"]*df["rho"]).max()),
    "n_rho_mean":           float((df["n"]*df["rho"]).mean()),
    "tier_Stable":          int((df["tier"]=="Stable").sum()),
    "tier_Preservation":    int((df["tier"]=="Preservation").sum()),
    "tier_Precarious":      int((df["tier"]=="Precarious").sum()),
    "tier_Critical":        int((df["tier"]=="Critical").sum()),
    "tier_Collapse":        int((df["tier"]=="Collapse").sum()),
    "composite_median":     float(med_comp),
    "hover_median_s":       float(med_hover),
    "max_dist_median_m":    float(med_dist),
    "max_speed_median_ms":  float(med_speed),
}
pd.DataFrame([summary]).to_csv(
    os.path.join(OUTPUT_DIR, "sri_summary_stats.csv"), index=False)

print("\n=== Summary ===")
for k, v in summary.items():
    print(f"  {k}: {v}")

print(f"\nAll outputs in: {OUTPUT_DIR}")
print("Done.")
