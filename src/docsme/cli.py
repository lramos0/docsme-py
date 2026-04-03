from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import GitCommitsDfError, build_commit_dataframe, export_dataframe, find_git_repos


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="git-commits-df",
        description="Build a pandas DataFrame from git commits across repositories in a directory.",
    )
    parser.add_argument("root", help="Root directory to scan, e.g. projects/")
    parser.add_argument("--author", help="Filter git log by author name or email")
    parser.add_argument("--since", help="Only include commits after this date/expression")
    parser.add_argument("--until", help="Only include commits before this date/expression")
    parser.add_argument("--branch", help="Optional branch/rev to run git log against")
    parser.add_argument(
        "--output",
        help="Write results to .csv, .parquet, or .json",
    )
    parser.add_argument(
        "--preview",
        type=int,
        default=20,
        help="Number of rows to print to stdout (default: 20)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        repos = find_git_repos(args.root)
        if not repos:
            print(f"No git repositories found under: {Path(args.root).expanduser().resolve()}", file=sys.stderr)
            return 1

        df = build_commit_dataframe(
            root=args.root,
            author=args.author,
            since=args.since,
            until=args.until,
            branch=args.branch,
        )

        print(f"Found {len(repos)} repositories and {len(df)} commits.")
        if not df.empty and args.preview > 0:
            preview_cols = ["repo_name", "short_hash", "author_name", "author_date", "subject"]
            print(df[preview_cols].head(args.preview).to_string(index=False))

        if args.output:
            output_path = export_dataframe(df, args.output)
            print(f"\nWrote DataFrame to {output_path}")

        return 0
    except (FileNotFoundError, NotADirectoryError, GitCommitsDfError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
