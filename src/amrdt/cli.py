"""Command-line interface."""

from __future__ import annotations

import argparse

from amrdt.config import load_config
from amrdt.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="amrdt",
        description="Atlanta Mobility Resilience Digital Twin Version 1",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="Run baseline and disruption scenarios")
    run.add_argument("--config", required=True, help="Path to YAML configuration")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "run":
        config = load_config(args.config)
        summary = run_pipeline(config)
        print("\nRun completed. Scenario summary:\n")
        print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
