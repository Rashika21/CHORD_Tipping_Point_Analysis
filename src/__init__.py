"""
TPI Analysis package for AircraftVerse corpus.
Implements the Topological Precariousness Index (TPI) based on the
Architectural Precariousness Measure (APM) framework.

Modules:
    graph_extraction  — parse design_tree.json into (n, m, node/edge lists)
    tpi_computation   — compute TPI, sigma_critical, ACR, fragility tiers
    visualization     — all canonical plots (12 figures)
    utils             — IO, logging, date helpers
"""
