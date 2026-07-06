"""
graph_extraction.py
===================
Extract coupling graph from AircraftVerse design_low_level.json.

WHY design_low_level.json (NOT design_tree.json)
─────────────────────────────────────────────────
design_tree.json is a high-level abstraction that:
  - Uses symmetric shorthand (1 arm represents 4 identical arms)
  - Omits many components: Flanges, BatteryController, Sensors as
    individual nodes, Cargo, CargoCase, Orient reference
  - Only encodes parent-child hierarchy (Layer P, incomplete)
  - Maximum node count across 27k designs: 48  ← too low

design_low_level.json is the full engineering bill of materials:
  - Lists EVERY physical component individually (each arm, each flange,
    each motor, each sensor as a separate named instance)
  - Lists EVERY interface connection explicitly (structural AND power AND
    sensor/data connections)
  - Directly maps to APM Layer M + E + I + P multiplex
  - No inference required — connections are ground truth from design tool

Example (4-arm quad, DataDemo design):
  design_tree.json   → 6 nodes  (hub, 1 arm, motor, prop, fuselage, battery)
  design_low_level   → 29 nodes (hub, 4 arms, 4 flanges, 4 motors, 4 propellers,
                                  fuselage, battery, BatteryController, 6 sensors,
                                  Cargo, CargoCase, Orient)

For complex designs (8-arm + wings + dual battery + full sensor suite),
node counts of 80–120 are expected.

GRAPH CONSTRUCTION
──────────────────
Nodes: every entry in design_low_level.json["components"]
       n = len(components)

Edges: every unique undirected pair in design_low_level.json["connections"]
       (connections list contains both directions; we deduplicate)
       m = len(unique undirected edges)

This gives the TRUE Layer P + E + I graph from AircraftVerse data.
σ_critical = 1/√(n·ρ) and TPI = 1 − σ_critical are then computed
exactly from these empirically grounded n and m values.

ASSUMPTIONS
───────────
A1. Every entry in "components" is one physical subsystem (node).
A2. Every entry in "connections" is one interface coupling (edge).
A3. Connections are undirected (physical interfaces are bidirectional).
A4. Duplicate connections (both A→B and B→A listed) are deduplicated.
A5. If design_low_level.json is absent, fall back to design_tree.json
    (flagged in output as low_level=False).
"""

import json
from pathlib import Path


# ── Component role classification (for functional coupling reference) ──────────

def _role_from_type(component_type: str) -> str:
    """Map AircraftVerse component_type to APM functional role."""
    ct = component_type.lower()
    if "motor"            in ct: return "motor"
    if "propeller"        in ct: return "prop"
    if "battery"          in ct and "controller" not in ct: return "battery"
    if "batterycontroller" in ct: return "esc"
    if "sensor"           in ct: return "sensor"
    if "hub"              in ct: return "hub"
    if "tube"             in ct: return "arm"
    if "flange"           in ct: return "flange"
    if "fuselage"         in ct: return "fuselage"
    if "wing"             in ct: return "wing"
    if "cargo"            in ct: return "cargo"
    if "orient"           in ct: return "orient"
    return "other"


# ── Core extraction from design_low_level.json ────────────────────────────────

def extract_graph_low_level(low_level: dict) -> dict:
    """
    Build the coupling graph from design_low_level.json.

    Returns:
        n        — node count (one per component instance)
        m        — edge count (unique undirected connections)
        nodes    — list of component instance names
        edges    — list of (u_idx, v_idx) undirected pairs
        labels   — component_instance names
        roles    — functional role per node
        types    — component_type per node
        source   — "low_level"
    """
    components  = low_level.get("components", [])
    connections = low_level.get("connections", [])

    # Build node index: component_instance → integer ID
    node_index: dict[str, int] = {}
    labels: list[str] = []
    roles:  list[str] = []
    types:  list[str] = []

    for i, comp in enumerate(components):
        name = comp.get("component_instance", f"comp_{i}")
        ctype = comp.get("component_type", "unknown")
        node_index[name] = i
        labels.append(name)
        types.append(ctype)
        roles.append(_role_from_type(ctype))

    # Build edges — deduplicate undirected pairs
    edge_set: set[tuple[int, int]] = set()
    edges: list[tuple[int, int]] = []

    for conn in connections:
        u_name = conn.get("from_ci", "")
        v_name = conn.get("to_ci",   "")
        u = node_index.get(u_name)
        v = node_index.get(v_name)
        if u is None or v is None or u == v:
            continue
        key = (min(u, v), max(u, v))
        if key not in edge_set:
            edge_set.add(key)
            edges.append(key)

    return {
        "n":       len(components),
        "m":       len(edges),
        "m_struct": len(edges),   # all connections are ground-truth (no inference)
        "m_func":  0,             # 0 inferred — all edges are explicit
        "nodes":   list(range(len(components))),
        "edges":   edges,
        "labels":  labels,
        "roles":   roles,
        "types":   types,
        "source":  "low_level",
    }


# ── Fallback: design_tree.json (kept for completeness) ────────────────────────

_NODE_KEYS = {
    "node_type", "motorType", "propType", "batteryType",
    "servoType", "gpsType", "escType", "sensorType",
    "receiverType", "autopilotType", "wingType",
}

def _is_node(d: dict) -> bool:
    return isinstance(d, dict) and bool(_NODE_KEYS.intersection(d.keys()))

def _infer_node_label(d: dict) -> str:
    for key in ("node_type", "motorType", "propType", "batteryType",
                "servoType", "gpsType", "escType", "sensorType",
                "receiverType", "autopilotType", "wingType"):
        if key in d:
            return str(d[key])
    return "unknown"

def _role_from_label(label: str) -> str:
    lo = label.lower()
    if "proparm" in lo:                                    return "arm"
    if any(k in lo for k in ("fuselage",)):               return "fuselage"
    if any(k in lo for k in ("hub", "connectedhub")):     return "hub"
    if "arm" in lo:                                        return "arm"
    if any(k in lo for k in ("motortype","t_motor","_motor","kv")): return "motor"
    if "motor" in lo:                                      return "motor"
    if any(k in lo for k in ("proptype","apc_prop","propeller","apc_")): return "prop"
    if any(k in lo for k in ("battery","turnigy","graphene","mah","lipo")): return "battery"
    if any(k in lo for k in ("autopilot","pixhawk")):      return "autopilot"
    if "gps" in lo:                                        return "gps"
    if any(k in lo for k in ("esc","hobbywing")):          return "esc"
    if any(k in lo for k in ("sensor","vario","baro")):    return "sensor"
    if "wing" in lo:                                       return "wing"
    return "other"

def _traverse(node, parent_id, nodes, edges, labels, counter):
    if isinstance(node, dict):
        if _is_node(node):
            cid = counter[0]; counter[0] += 1
            nodes.append(cid)
            labels.append(_infer_node_label(node))
            if parent_id is not None:
                edges.append((parent_id, cid))
            for v in node.values():
                _traverse(v, cid, nodes, edges, labels, counter)
        else:
            for v in node.values():
                _traverse(v, parent_id, nodes, edges, labels, counter)
    elif isinstance(node, list):
        for item in node:
            _traverse(item, parent_id, nodes, edges, labels, counter)

def extract_graph_tree(tree: dict) -> dict:
    """Fallback: extract from design_tree.json (less complete)."""
    nodes, edges, labels = [], [], []
    counter = [0]
    _traverse(tree, None, nodes, edges, labels, counter)
    return {
        "n": len(nodes), "m": len(edges),
        "m_struct": len(edges), "m_func": 0,
        "nodes": nodes, "edges": edges,
        "labels": labels,
        "roles": [_role_from_label(lb) for lb in labels],
        "types": ["unknown"] * len(nodes),
        "source": "tree",
    }


# ── File loaders ───────────────────────────────────────────────────────────────

def load_json(path) -> dict | None:
    p = Path(path)
    if not p.exists():
        return None
    with open(p, "r") as f:
        return json.load(f)


# ── Public API ─────────────────────────────────────────────────────────────────

def extract_graph_from_folder(design_folder) -> dict | None:
    """
    Full extraction for one design folder.
    Prefers design_low_level.json; falls back to design_tree.json.
    Returns flat result dict with graph metrics + physics outputs.
    """
    folder = Path(design_folder)

    # --- Graph extraction (prefer low_level) ---
    low_level = load_json(folder / "design_low_level.json")
    if low_level and low_level.get("components"):
        graph = extract_graph_low_level(low_level)
    else:
        tree = load_json(folder / "design_tree.json")
        if tree is None:
            return None
        graph = extract_graph_tree(tree)

    # --- Physics outputs ---
    output = load_json(folder / "output.json") or {}

    hover_time   = output.get("Hover_Time")
    max_speed    = output.get("Max_Speed")
    max_distance = output.get("Max_Distance")
    mass         = output.get("Mass")
    airworthy    = 1 if hover_time else (0 if output else None)

    return {
        "design":      folder.name,
        "n_nodes":     graph["n"],
        "m_edges":     graph["m"],
        "m_struct":    graph["m_struct"],
        "m_func":      graph["m_func"],
        "source":      graph["source"],
        "labels":      graph["labels"],
        "hover_time":  hover_time,
        "max_speed":   max_speed,
        "max_distance":max_distance,
        "mass":        mass,
        "airworthy":   airworthy,
    }
