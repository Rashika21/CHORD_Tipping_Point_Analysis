# Experiment: SRI New Designs — GA-Optimised UAV Corpus (17,387 Designs)

**Date:** 2026-06-18  
**Dataset:** SRI TRADES genetic-algorithm optimised UAV designs  
**Input file:** `ga_designs.json` (from SRI TRADES generator)  
**Designs processed:** 17,387  
**Airworthy:** 100% (all GA-optimised designs have valid physics outputs)  

---

## Input Data

| Item | Description |
|---|---|
| **Source** | SRI TRADES GA optimisation output |
| **Format** | Single JSON file: `ga_designs.json` |
| **Structure** | List of records, each with `target_metrics` + `designs` (list of variants) |
| **Components per design** | 9 – 22 nodes (strict hierarchical trees) |

### ga_designs.json structure

```json
[
  {
    "target_metrics": {
      "hover_time": <float>,
      "max_speed": <float>,
      "max_distance": <float>
    },
    "designs": [
      {
        "name": "design_<id>",
        "hub": {
          "node_type": "ConnectedHub6_Sym",
          "mainSegment": {
            "node_type": "PropArm",
            "armLength": <float>,
            "motor": {"motorType": "<motor_id>"},
            "prop":  {"propType":  "<prop_id>"},
            "flange": {"offset": <float>, "angle": <float>}
          }
        },
        "fuselageWithComponents": {
          "node_type": "SingleBatteryFuselageWithComponents",
          "battery": {"batteryType": "<battery_id>"},
          "fuselage": {"length": <float>, ...}
        }
      }
    ]
  }
]
```

### Component counting in SRI designs

| Component | Node? | Why |
|---|---|---|
| Fuselage body | Yes | Structural subsystem |
| Hub | Yes | Central coupling node |
| Battery (×1 or ×2) | Yes | Dedicated power subsystem |
| Each arm (PropArm) | Yes | Physical arm instance |
| Motor per arm | Yes | Propulsion node |
| Propeller per arm | Yes | Terminal node |
| Flange (`{offset, angle}`) | No | Geometry parameter only |
| Sensor positions (rpmX/Y, etc.) | No | Coordinate pairs in fuselage dict |

Resulting node counts: 9 (2-arm/1-bat), 10 (2-arm/2-bat), 15 (4-arm/1-bat), 16 (4-arm/2-bat), 21 (6-arm/1-bat), 22 (6-arm/2-bat).

---

## How to Run

```bash
# From TPI_Analysis/ root:
python experiments/sri_new_designs/sri_tpi_experiment.py \
    --data /path/to/ga_designs.json
```

The script is self-contained and does not use `config.py` or `main.py`. It reads the JSON directly and outputs results alongside the script or to a specified output directory.

---

## Sample Outputs

| File | Description |
|---|---|
| `sample_outputs/data/sri_tpi_results.csv` | Per-design TPI, n, m, ρ, tier |
| `sample_outputs/data/sri_summary_stats.csv` | Summary by hub type group |
| `sample_outputs/figures/S1_design_space_rho_vs_n.png` | Design space (n, ρ) — 6 discrete points |
| `sample_outputs/figures/S2a_tpi_vs_graph_density.png` | TPI vs ρ |
| `sample_outputs/figures/S2b_tpi_vs_component_count.png` | TPI vs n |
| `sample_outputs/figures/S3_tpi_density_distribution.png` | TPI distribution (single spike) |
| `sample_outputs/figures/S4–S6_quadrant_*.png` | Performance quadrants |
| `sample_outputs/figures/S7_tpi_vs_composite_performance.png` | Composite performance vs TPI |
| `sample_outputs/figures/S8_tpi_by_hub_type.png` | TPI breakdown by hub configuration |
| `sample_outputs/figures/S9_design_density_vs_rho.png` | Graph density distribution |
| `sample_outputs/figures/S_component_count_distribution.png` | Component count histogram |
| `sample_outputs/figures/S_why_tpi_constant_explained.png` | Analytical explanation of constant TPI |
| `sample_outputs/figures/S_performance_distributions.png` | Performance metric distributions |
| `sample_outputs/figures/CAD_design1_hexrotor.png` | CAD diagram: 6-arm hexrotor |
| `sample_outputs/figures/CAD_design2_quadrotor.png` | CAD diagram: 4-arm quadrotor |

---

## Key Findings

| Metric | Value |
|---|---|
| Total designs | 17,387 |
| Component count per design | 9 – 22 nodes (6 discrete values) |
| Graph density ρ | 2/n for each design |
| n·ρ (product) | **2.000 exactly** (all designs are strict trees) |
| TPI | **0.2929 constant** for all 17,387 designs |
| Fragility tier | 100% Preservation (TPI < 0.30) |
| Airworthy | 100% (all designs have valid physics outputs) |

### Why TPI is constant

For any strict tree (m = n − 1):

```
ρ = 2(n−1) / [n(n−1)] = 2/n
n·ρ = 2.000
σ_critical = 1/√2
TPI = 1 − 1/√2 ≈ 0.2929
```

The TRADES generator produces strictly hierarchical designs (each child has exactly one parent), which are mathematically guaranteed to produce n·ρ = 2 regardless of size or hub type.

---

## Hub Types Present

| Hub Type | Arms | Designs |
|---|---|---|
| ConnectedHub6_Sym | 6 | 13,104 |
| ConnectedHub4_2_2 | 4 | 1,577 |
| ConnectedHub6_Sym_Aligned | 6 | 922 |
| ConnectedHub4_Sym | 4 | 700 |
| ConnectedHub6_2_2_2 | 6 | 476 |
| ConnectedHub4_Sym_Aligned | 4 | 372 |
| ConnectedHub2_Sym_Wide | 2 | 109 |
| ConnectedHub4_1_2_1 | 4 | 83 |
| ConnectedHub6_1_2_2_1 | 6 | 44 |
