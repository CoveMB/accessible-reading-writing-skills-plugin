#!/usr/bin/env python3
"""Evaluate outputs against deterministic semantic-preservation contracts."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import semantic_preservation


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases",
        required=True,
        type=Path,
        help="Path to semantic preservation cases JSON.",
    )
    parser.add_argument(
        "--outputs",
        type=Path,
        help=(
            "Path to model or reference outputs as JSON or JSONL. "
            "If omitted, embedded gold_output values are evaluated."
        ),
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Allow the outputs file to cover only a subset of cases.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        cases = semantic_preservation.load_cases(args.cases)
        output_records = (
            semantic_preservation.load_output_records(args.outputs)
            if args.outputs
            else semantic_preservation.reference_output_records(cases)
        )
    except Exception as exc:
        print(f"Unable to load semantic preservation data: {exc}", file=sys.stderr)
        return 2

    evaluations = semantic_preservation.evaluate_output_records(
        cases,
        output_records,
        require_all=not args.allow_missing,
    )
    for line in semantic_preservation.diagnostic_lines(evaluations):
        print(line)
    print(semantic_preservation.summary_line(evaluations))
    return 0 if all(evaluation["passed"] for evaluation in evaluations) else 1


if __name__ == "__main__":
    raise SystemExit(main())
