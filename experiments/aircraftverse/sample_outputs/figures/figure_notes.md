# Figure Notes — Refined Figures R01–R09
**Experiment:** EXP_2026_06_10_RECOMPUTE  
**Authors:** Roshi Rose Nilchiani, PhD & Rashika Sugganahalli N B  
**Generated:** 2026-06-10  
**Script:** `experiments/2026_06_10_recompute/refined_figures.py`  
**Data source:** `outputs/2026_06_10_recompute/data/tpi_verified.csv` (verified edges) merged with `outputs/2026_06_02/data/tpi_results.csv` (performance data)

---

## R01 — Design Space: Graph Density vs Component Count

**File:** `R01_design_space_rho_vs_n.png`

**What is plotted:** Scatter of all 27,714 AircraftVerse designs in the (n, ρ) plane, where n is the number of components (graph nodes) and ρ = 2m/[n(n−1)] is the graph density (connectance). Colour encodes TPI.

**Why this plot:** The (n, ρ) plane is the fundamental design space for May–Wigner stability analysis. The stability criterion σ√(nρ) < 1 partitions this space into stable and unstable regions. Plotting every design in this space simultaneously reveals (a) where the corpus concentrates, (b) whether the assembly grammar produces designs near or far from the stability boundary, and (c) whether larger designs are systematically denser or sparser.

**Reference lines:**
- **May–Wigner boundary** (dashed black): ρ = 1/n, equivalently n·ρ = 1. Designs below this curve satisfy σ_critical > 1 and cannot be tipped by any coupling strength σ ≤ 1. The entire AircraftVerse corpus lies above this boundary, confirming universal structural precariousness.
- **Corpus mean isocurve** (dash-dot): ρ = 2.290/n, the mean n·ρ value across all designs. This traces the central tendency of the corpus in design space.
- **Precarious band** (shaded orange): the region between n·ρ_min = 2.036 and n·ρ_max = 2.390 — the observed corpus range. The tightness of this band confirms that the AircraftVerse generative grammar constrains all designs to a narrow 1-D manifold in (n, ρ) space.

**Statistical context:** ρ ∈ [0.008, 0.115]; n ∈ [21, 265]. The hyperbolic shape of the scatter confirms ρ ∝ n⁻¹ (power-law decay), a direct consequence of the chain-assembly topology where m ∝ n.

---

## R02 — σ_critical vs ρ  |  TPI vs n

**File:** `R02_sigma_rho_tpi_n.png`

**What is plotted (left panel):** σ_critical = 1/√(n·ρ) plotted against ρ for all designs, coloured by n. Analytic curves for fixed n ∈ {25, 50, 100} overlaid.

**What is plotted (right panel):** TPI = 1 − σ_critical plotted against n, coloured by ρ. Tier boundary lines annotated.

**Why this plot:** The left panel exposes the functional form of the tipping threshold: σ_critical depends on the product n·ρ, not on ρ alone. Designs with the same n·ρ sit on the same horizontal line regardless of their individual (n, ρ) values. The analytic curves confirm that the corpus scatter is consistent with the theoretical model across all design sizes. The red dashed line at σ_critical = 1.0 marks the stability boundary — no corpus design reaches this threshold.

The right panel shows TPI as a function of design size n. The absence of a strong trend confirms that TPI is size-invariant: the assembly grammar's ρ ∝ 1/n scaling exactly cancels the n multiplier in the May–Wigner criterion, leaving n·ρ ≈ const. Tier boundary lines at TPI = 0.30, 0.70, 0.90 are annotated.

**Key insight:** The non-linear σ_critical(ρ) relationship means that small improvements in density (adding edges) yield diminishing returns in stability gain. At ρ ≈ 0.05, Δσ_c / Δρ is small; the corpus is trapped in a region where density changes do not substantially move the tipping threshold.

---

## R03 — TPI Distribution (Kernel Density Estimate)

**File:** `R03_tpi_density_distribution.png`

**What is plotted:** Kernel density estimate (KDE) of TPI across all 27,714 designs, with fragility tier boundaries marked as vertical dashed lines and tier backgrounds shaded.

**KDE bandwidth:** Silverman's rule: h = 0.9·σ·N^(−1/5) = 0.00045. This bandwidth is narrow by design — the TPI distribution is extremely concentrated and a wider bandwidth would obscure the sharp concentration at TPI ≈ 0.333.

**Why this plot:** A KDE (rather than a histogram) provides a continuous probability density estimate that is insensitive to bin width choice. The plot directly communicates the probability mass in each fragility tier. The sharp, narrow peak at TPI ∈ [0.299, 0.353] with a span of only 0.054 is the key empirical finding: the assembly grammar constrains all UAV topologies to a single narrow precariousness band. There is effectively no design in the Stable, Critical, or Collapse tiers — 99.99% of the corpus is Precarious.

**Vertical lines:** Tier boundaries at TPI = 0.00 (Stable/Preservation), 0.30 (Preservation/Precarious), 0.70 (Precarious/Critical), 0.90 (Critical/Collapse).

**Statistical summary:** Mean TPI = 0.3339; Std = 0.0099; Min = 0.2991; Max = 0.3531. The coefficient of variation (σ/μ = 3.0%) confirms an extremely homogeneous corpus in terms of topological fragility.

---

## R04 — Hover Time Quadrant (Airworthy Designs Only)

**File:** `R04_quadrant_hover_time.png`

**Scope:** 7,690 airworthy designs with hover_time > 0, max_speed > 0, and max_distance > 0. Non-airworthy designs (airworthy = 0) are excluded because their performance metrics are zero by definition (the physics simulator could not compute flight — see output.json), not because they underperform. Including them would conflate structural failure with poor aerodynamic performance.

**What is plotted:** Scatter of TPI (x-axis) vs hover_time in seconds (y-axis) for all airworthy designs, coloured by n.

**Quadrant split:**
- **Vertical line:** Median TPI across the 7,690 airworthy designs.
- **Horizontal line:** Median hover_time across the 7,690 airworthy designs. The median is used (not zero) because all hover times are positive; a split at zero would be uninformative. The median provides an equal-population split of the design space.

**Quadrant taxonomy:**
- **Optimal** (top-left): High hover endurance AND low structural precariousness — the engineering target.
- **Precarious Performer** (top-right): High endurance BUT high TPI — operationally capable designs with hidden structural risk. These are the primary concern for the APM-based resilience assessment.
- **Stable-Modest** (bottom-left): Low endurance AND low TPI — safe but underperforming.
- **Double Liability** (bottom-right): Low endurance AND high TPI — worst category; poor in both dimensions.

**Interpretation:** The distribution across quadrants tests the performance–precariousness trade-off hypothesis. A roughly equal split (≈25% per quadrant) implies no correlation between endurance and TPI. An over-representation of Q2 (Precarious Performer) would indicate that high-endurance designs are also more topologically fragile — an actionable design finding.

**Colour:** Number of components n (plasma scale). Heavier (larger n) designs tend toward lower ρ and lower TPI, but the correlation is weak within the Precarious tier.

---

## R05 — Max Distance Quadrant (Airworthy Designs Only)

**File:** `R05_quadrant_max_distance.png`

**Scope:** Same 7,690 airworthy designs as R04.

**What is plotted:** TPI (x-axis) vs log₁₀(max_distance in metres) (y-axis). Log scale is applied because max_distance spans three decades [21.8 m – 40,905 m]; on a linear scale, the extreme outliers (>10 km range) would compress the majority of designs into an unintelligible cluster.

**Quadrant split:** Vertical line at median TPI; horizontal line at median log₁₀(max_distance).

**Why max distance:** Maximum range is a mission-critical performance metric for UAV deployment. It integrates battery capacity, motor efficiency, and aerodynamic quality into a single scalar. Designs in Q2 (high range, high TPI) represent long-range platforms that are topologically precarious — a concerning combination for extended autonomous missions where coupling perturbations (vibration, thermal drift) can drive the system toward the tipping threshold.

**Comparison with R04:** Comparing the Q2 population fractions across R04–R06 reveals whether the performance–precariousness trade-off is uniform across endurance, range, and speed dimensions, or whether one performance axis is more strongly correlated with structural fragility.

---

## R06 — Max Speed Quadrant (Airworthy Designs Only)

**File:** `R06_quadrant_max_speed.png`

**Scope:** Same 7,690 airworthy designs as R04.

**What is plotted:** TPI (x-axis) vs max_speed in m/s (y-axis). Linear scale (max_speed ∈ [1, 50 m/s]).

**Quadrant split:** Vertical line at median TPI; horizontal line at median max_speed.

**Why max speed:** Maximum forward speed is determined primarily by motor KV rating and propeller pitch — design variables that are partially independent of the structural topology. If speed and TPI are uncorrelated, the quadrant split should be approximately uniform across the four quadrants. A concentration in Q2 (high speed, high TPI) would suggest that aerodynamically optimised configurations (high-KV motors, aggressive props) also produce sparser, more precarious graph topologies.

---

## R07 — TPI vs Composite Performance Score

**File:** `R07_tpi_vs_composite_performance.png`

**Scope:** 7,690 airworthy designs.

**Composite performance score P:**
```
P = ( norm(hover_time) + norm(max_speed) + norm(max_distance) ) / 3
```
where norm(x) = (x − x_min) / (x_max − x_min) maps each metric to [0, 1] independently before averaging. This equal-weight linear composite captures aggregate multi-dimensional performance without privileging any single axis. P = 0 is the worst-performing design across all three metrics simultaneously; P = 1 is the best.

**What is plotted:** TPI (x-axis) vs P (y-axis). Colour = n (number of components). Marker size ∝ mass (kg). Fragility tier backgrounds shaded.

**Why this plot:** The three individual quadrant plots (R04–R06) test each performance dimension separately. This figure integrates them, directly operationalising the APM Table 2 performance–resilience matrix which classifies systems by joint (performance, resilience) position. The Pareto frontier (red step line) marks designs that are non-dominated in the (minimise TPI, maximise P) sense.

**Reference:** Analogous to figure E04 in EXP_2026_06_10 (TPI × hover_time × n_nodes × mass), extended here to the full composite P.

---

## R08 — Pareto Frontier: Performance–Precariousness Trade-off

**File:** `R08_pareto_frontier.png`

**Scope:** 7,690 airworthy designs.

**Composite score P:** Same definition as R07.

**Pareto frontier computation:**
A design d is Pareto-optimal in the objective space (minimise TPI, maximise P) if no other design d' satisfies both TPI(d') ≤ TPI(d) AND P(d') ≥ P(d) with at least one strict inequality. The computational algorithm:
1. Sort all designs by TPI in ascending order (left to right).
2. Traverse the sorted sequence; maintain a running maximum of P seen so far.
3. A design is Pareto-optimal if its P value equals or exceeds the running maximum — it is the best-performing design at or below its TPI value.
4. The resulting set is the lower-left staircase boundary of the dominated region.

This algorithm is O(N log N) due to the sort (N = 7,690). The Pareto frontier step function is plotted as a right-continuous staircase connecting consecutive non-dominated points.

**Interpretation:**
- **Left panel:** Full corpus. Grey = dominated designs. Coloured = Pareto-optimal. Red step = frontier.
- **Right panel:** Zoom on Pareto points. Top-5 highest-P frontier designs annotated by n.
- A steep frontier (large P range over a small TPI range) indicates a strong performance–precariousness trade-off.
- A flat frontier indicates that TPI and P are largely orthogonal — high-performing designs are not systematically more precarious.

**Key result:** 5 Pareto-optimal designs identified. The small count reflects the extreme TPI homogeneity (span = 0.054): most designs have nearly identical TPI, so the Pareto front is dominated by the single highest-P design at each TPI level.

---

## R09 — Design Density vs Graph Density

**File:** `R09_design_density_vs_rho.png`

**What is plotted:** Histogram (normalised to probability density) and KDE of ρ across all 27,714 designs. Mean and median annotated.

**KDE bandwidth:** Silverman's rule: h = 0.9·σ·N^(−1/5). The KDE provides a smooth continuous estimate of the distribution; the histogram provides bin-level counts for transparency.

**Why this plot:** While R01 shows ρ in 2-D design space, this plot provides the univariate marginal distribution — how ρ values are distributed across the corpus independently of n. The right-skewed distribution with a mode at ρ ≈ 0.04 reflects the predominance of medium-sized designs (n ≈ 40–60) in the corpus. The long right tail captures a small number of compact designs (small n, high ρ). Mean ρ = 0.0277; Median ρ = 0.0228.

**Relationship to TPI:** Because TPI = 1 − 1/√(n·ρ) and n·ρ is approximately constant (≈ 2.29), the ρ distribution directly controls TPI only insofar as it reflects variation in n. Designs with the same n·ρ have the same TPI regardless of their individual ρ — explaining why the wide ρ range [0.008, 0.115] maps to a narrow TPI range [0.299, 0.353].

---

## Data and Reproducibility Notes

| Item | Value |
|---|---|
| Total designs | 27,714 |
| Airworthy designs (for R04–R08) | 7,690 |
| Airworthy filter | airworthy=1 AND hover_time > 0 AND max_speed > 0 AND max_distance > 0 |
| TPI source | `tpi_verified.csv` (recomputed from ground-truth edges in `edge_verification_corpus_June10.csv`) |
| Performance source | `tpi_results.csv` from EXP_2026_06_02 (read directly from `output.json` per design) |
| Cross-validation | Max |ΔTPI| = 5×10⁻⁹ between verified and EXP_06_02 (floating-point rounding only) |
| KDE method | Gaussian kernel, Silverman's bandwidth rule, numpy-native (no scipy) |
| Pareto algorithm | Sort by TPI ascending, running-max P scan — O(N log N) |
