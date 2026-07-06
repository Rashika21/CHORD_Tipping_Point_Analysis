"""
main.py
=======
Entry point for the TPI Analysis pipeline.

Usage:
    # Full corpus (set DATA_DIR in config.py first):
    python main.py

    # Quick test on N designs:
    python main.py --max 100

    # Use pre-computed CSV (skip corpus processing):
    python main.py --from-csv

    # Plots only (from existing CSV):
    python main.py --from-csv --plots-only

Pipeline:
    1. Validate data directory and output dirs
    2. Process all design folders → compute TPI metrics
    3. Save tpi_results.csv + summary_stats.json
    4. Generate all 12 plots → save to outputs/YYYY_MM_DD/figures/
    5. Write experiment log entry
"""

import sys
import os
import argparse
import time

# ── Make src/ importable from root ────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from src.utils import (setup_logger, ensure_output_dirs,
                        save_results_csv, load_results_csv,
                        save_summary_json, save_ranked_csv, compute_summary)
from src.tpi_computation import run_corpus
from src.visualization   import generate_all_plots


# ── CLI arguments ──────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="TPI Analysis pipeline for AircraftVerse corpus.")
    parser.add_argument("--max",         type=int,  default=None,
                        help="Process only first N designs (for testing).")
    parser.add_argument("--from-csv",    action="store_true",
                        help="Skip corpus processing; load existing CSV.")
    parser.add_argument("--plots-only",  action="store_true",
                        help="Only regenerate plots from existing CSV.")
    parser.add_argument("--data-dir",    type=str,  default=None,
                        help="Override DATA_DIR from config.")
    return parser.parse_args()


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    args   = parse_args()
    logger = setup_logger("tpi")
    ensure_output_dirs()

    logger.info("=" * 60)
    logger.info(f"Experiment: {config.EXPERIMENT_ID}")
    logger.info(f"Output dir: {config.OUTPUT_DIR}")
    logger.info("=" * 60)

    data_dir = args.data_dir or config.DATA_DIR

    # ── Step 1: Corpus processing ──────────────────────────────────────────────
    if not args.from_csv and not args.plots_only:
        if not os.path.isdir(data_dir):
            logger.error(
                f"DATA_DIR not found: {data_dir}\n"
                "  → Set DATA_DIR in config.py or pass --data-dir <path>\n"
                "  → Download AircraftVerse from: "
                "https://zenodo.org/record/6525446"
            )
            sys.exit(1)

        logger.info(f"Processing corpus: {data_dir}")
        t0      = time.time()
        results = run_corpus(data_dir, logger=logger,
                             max_designs=args.max or config.MAX_DESIGNS)
        elapsed = time.time() - t0
        logger.info(f"Corpus done in {elapsed:.1f}s — {len(results):,} designs")

        save_results_csv(results)
        logger.info(f"Saved: {config.TPI_RESULTS_CSV}")

        summary = compute_summary(results)
        save_summary_json(summary)
        logger.info(f"Saved: {config.SUMMARY_STATS_JSON}")

        save_ranked_csv(results)
        logger.info(f"Saved: ranked CSV → outputs/.../data/tpi_ranked.csv")

        _print_summary(summary, logger)

    else:
        if not os.path.exists(config.TPI_RESULTS_CSV):
            logger.error(f"CSV not found: {config.TPI_RESULTS_CSV}")
            sys.exit(1)
        logger.info(f"Loading from CSV: {config.TPI_RESULTS_CSV}")
        results = load_results_csv()
        logger.info(f"Loaded {len(results):,} designs")

    # ── Step 2: Visualisation ──────────────────────────────────────────────────
    logger.info("Generating plots ...")
    saved = generate_all_plots(results, logger=logger)
    logger.info(f"{len(saved)} figures saved to: {config.FIGURES_DIR}")

    logger.info("Pipeline complete.")
    logger.info(f"Results : {config.TPI_RESULTS_CSV}")
    logger.info(f"Summary : {config.SUMMARY_STATS_JSON}")
    logger.info(f"Figures : {config.FIGURES_DIR}")


def _print_summary(summary: dict, logger):
    tpi = summary.get("tpi_stats", {})
    logger.info("─" * 40)
    logger.info("TPI Summary Statistics:")
    logger.info(f"  Total designs : {summary['total_designs']:,}")
    logger.info(f"  TPI min       : {tpi.get('min', 'N/A')}")
    logger.info(f"  TPI mean      : {tpi.get('mean', 'N/A')}")
    logger.info(f"  TPI max       : {tpi.get('max', 'N/A')}")
    logger.info(f"  Flagged ≥{config.TPI_FLAG_THRESHOLD} : {summary['flagged_for_review']:,}")
    logger.info("  Tier counts:")
    for tier, count in summary.get("tier_counts", {}).items():
        logger.info(f"    {tier:<14} {count:,}")
    logger.info("─" * 40)


if __name__ == "__main__":
    main()
