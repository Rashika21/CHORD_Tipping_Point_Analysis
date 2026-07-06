# Experiment: AircraftVerse Corpus (27,714 UAV Designs)

**Date:** 2026-06-10 (recompute)  
**Dataset:** AircraftVerse — Zenodo record 6525446  
**Designs processed:** 27,714  
**Airworthy designs:** 7,690  

---

## Input Data

| Item | Description |
|---|---|
| **Source** | AircraftVerse corpus (SRI International / DARPA TRADES) |
| **Download** | https://zenodo.org/record/6525446 |
| **Folder** | `data_full/` — one subfolder per design (`design_1/`, `design_2/`, ...) |
| **Key file per design** | `design_low_level.json` — full bill of materials and connection list |
| **Physics file** | `output.json` — hover time, max speed, max distance, mass |

### data_full/ folder structure

```
data_full/
├── design_1/
│   ├── design_low_level.json   ← graph source (components + connections)
│   ├── design_tree.json        ← fallback (less complete)
│   └── output.json             ← physics simulation outputs
├── design_2/
│   └── ...
└── design_27714/
    └── ...
```

### Why design_low_level.json?

This file contains every physical component as a named instance and every interface connection explicitly. A 4-arm quad has 29 nodes in `design_low_level.json` vs 6 in `design_tree.json`. The low-level file is the ground-truth bill of materials used for the APM coupling graph.

---

## How to Run

### Step 1: Set DATA_DIR

Edit `config.py` in the project root:
```python
DATA_DIR = "/path/to/your/data_full"
```

Or pass it at runtime (no config edit needed):
```bash
python main.py --data-dir /path/to/your/data_full
```

### Step 2: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Run the pipeline

```bash
# Full corpus (all 27,714 designs):
python main.py

# Quick test (first 100 designs):
python main.py --max 100

# Regenerate plots only from existing CSV:
python main.py --from-csv --plots-only
```

### Step 4: Outputs

Results are saved to `outputs/YYYY_MM_DD/`:
- `data/tpi_results.csv` — per-design TPI values
- `data/summary_stats.json` — corpus statistics
- `data/tpi_ranked.csv` — designs sorted by TPI descending
- `figures/fig_01_*` through `fig_12_*` — 12 analysis plots

---

## Sample Outputs (this run)

The `sample_outputs/` folder contains the final verified results from 2026-06-10:

| Folder | Contents |
|---|---|
| `sample_outputs/data/tpi_verified.csv` | Ground-truth TPI values for all 27,714 designs |
| `sample_outputs/figures/R01_*.png` | Design space: graph density vs component count |
| `sample_outputs/figures/R02_*.png` | σ_critical vs ρ, TPI vs n |
| `sample_outputs/figures/R03_*.png` | TPI kernel density distribution |
| `sample_outputs/figures/R04–R06_*.png` | Performance quadrants (hover time, distance, speed) |
| `sample_outputs/figures/R07_*.png` | TPI vs composite performance score |
| `sample_outputs/figures/R08_*.png` | Pareto frontier: performance–precariousness trade-off |
| `sample_outputs/figures/R09_*.png` | Graph density distribution |
| `sample_outputs/figures/figure_notes.md` | Full methodology notes for each figure |

---

## Key Findings

| Metric | Value |
|---|---|
| Total designs | 27,714 |
| Component count per design | 21 – 265 nodes |
| Graph density ρ | 0.008 – 0.115 |
| n·ρ (product) | 2.036 – 2.390 (mean 2.29) |
| TPI range | 0.2991 – 0.3531 |
| TPI mean ± std | 0.3339 ± 0.0099 |
| Fragility tier | 100% Precarious (0.30 < TPI < 0.70) |
| Airworthy designs | 7,690 / 27,714 (27.8%) |
| Pareto-optimal designs | 5 |
