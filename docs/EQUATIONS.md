# TPI Equations, Derivations, and Verification

**Framework:** Architectural Precariousness Measure (APM)  
**Theoretical basis:** May–Wigner random matrix stability criterion  

---

## 1. Graph Density (Connectance)

```
ρ = 2m / [n(n − 1)]
```

Where:
- n = number of nodes (components)
- m = number of undirected edges (interface connections)
- n(n−1)/2 = maximum possible edges in an undirected graph
- ρ ∈ [0, 1]: proportion of all possible pairings that are connected

Implementation: `src/tpi_computation.py → graph_density(n, m)`

**Edge cases:**
- n ≤ 1 or m = 0 → ρ = 0.0 (degenerate/isolated design)

---

## 2. May–Wigner Critical Coupling Strength

```
σ_critical = 1 / √(n · ρ)
```

**Derivation:**  
May (1972) showed that a random n×n interaction matrix with entry variance σ² and connectance ρ has maximum eigenvalue λ_max ≈ σ√(n·ρ) for large n. The system transitions from stable to unstable when:

```
σ · √(n · ρ) = 1
```

Solving for the critical coupling strength:

```
σ_critical = 1 / √(n · ρ)
```

Implementation: `src/tpi_computation.py → sigma_critical(n, rho)`

**Edge cases:**
- n·ρ ≤ 0 → σ_critical = ∞ (no coupling risk; isolated system)

---

## 3. Topological Precariousness Index (TPI)

```
TPI = 1 − σ_critical = 1 − 1/√(n · ρ)
```

TPI measures how far below the tipping threshold the current topology sits:
- TPI = 0 → σ_critical = 1 → exactly at the tipping boundary
- TPI < 0 → σ_critical > 1 → cannot be tipped (Stable tier)
- TPI > 0 → σ_critical < 1 → any coupling σ > σ_critical can tip the system
- TPI → 1 → σ_critical → 0 → already past the tipping threshold

Implementation: `src/tpi_computation.py → compute_tpi(n, m)`

---

## 4. Internal Verification (May–Wigner Check)

```
σ_critical · √(n · ρ) = 1.0   (always, by construction)
```

This identity is computed for every design as a floating-point verification.  
Maximum observed deviation: < 10⁻⁹ (double-precision rounding only).

---

## 5. Fragility Tier Boundaries

| Tier | Condition | σ_critical range |
|---|---|---|
| Stable | TPI ≤ 0 | σ_c ≥ 1 |
| Preservation | 0 < TPI ≤ 0.30 | 0.70 ≤ σ_c < 1 |
| Precarious | 0.30 < TPI ≤ 0.70 | 0.30 ≤ σ_c < 0.70 |
| Critical | 0.70 < TPI ≤ 0.90 | 0.10 ≤ σ_c < 0.30 |
| Collapse | TPI > 0.90 | σ_c < 0.10 |

Configuration: `config.py → TIERS`

---

## 6. Tree Topology Special Case

For any strict hierarchical tree (each component has exactly one parent):

```
m = n − 1   (by tree definition)
ρ = 2(n−1) / [n(n−1)] = 2/n
n · ρ = n · (2/n) = 2.000   (exact, independent of n)
σ_critical = 1/√2 ≈ 0.7071
TPI = 1 − 1/√2 ≈ 0.2929   (constant)
```

All SRI TRADES GA-optimised designs are strict trees → TPI = 0.2929 for all 17,387 designs.

Proof of correctness: `n·ρ = 2.000000` confirmed for all 6 design groups (n ∈ {9, 10, 15, 16, 21, 22}).

---

## 7. Composite Performance Score (for Quadrant/Pareto Analysis)

```
P = [ norm(hover_time) + norm(max_speed) + norm(max_distance) ] / 3
```

Where:
```
norm(x) = (x − x_min) / (x_max − x_min)
```

Each metric is independently normalised to [0, 1] before equal-weight averaging.  
Scope: airworthy designs only (hover_time > 0, max_speed > 0, max_distance > 0).

---

## 8. Pareto Optimality Criterion

A design d* is Pareto-optimal in objective space (minimise TPI, maximise P) if no design d satisfies:

```
TPI(d) ≤ TPI(d*)   AND   P(d) ≥ P(d*)   with at least one strict inequality
```

Algorithm: sort by TPI ascending, O(N log N) running-maximum scan.  
Applied to: 7,690 airworthy AircraftVerse designs.  
Result: 5 Pareto-optimal designs identified.

---

## 9. Numerical Verification Results

### AircraftVerse corpus

| Metric | Value |
|---|---|
| n range | 21 – 265 |
| m range | 23 – 260 |
| ρ range | 0.008 – 0.115 |
| n·ρ range | 2.036 – 2.390 |
| n·ρ mean | 2.290 |
| TPI range | 0.2991 – 0.3531 |
| TPI mean ± std | 0.3339 ± 0.0099 |
| Max May–Wigner deviation | < 5×10⁻⁹ |

### SRI GA corpus

| Metric | Value |
|---|---|
| n values | {9, 10, 15, 16, 21, 22} |
| n·ρ | 2.000000 (exact for all groups) |
| TPI | 0.292893 (= 1 − 1/√2) for all 17,387 designs |
| Max May–Wigner deviation | < 10⁻¹⁵ |
