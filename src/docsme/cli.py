from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .core import GitCommitsDfError, build_commit_dataframe, export_dataframe, find_git_repos


CONFIG_DIR = Path.home() / ".config" / "docsme"
CONFIG_PATH = CONFIG_DIR / "config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")


def apply_config_to_env(config: dict) -> None:
    if config.get("github_username"):
        os.environ["DOCSME_GITHUB_USERNAME"] = config["github_username"]
    if config.get("projects_root"):
        os.environ["DOCSME_PROJECTS_ROOT"] = config["projects_root"]
    if config.get("ai_elaboration"):
        os.environ["DOCSME_AI_ELABORATION"] = config["ai_elaboration"]


def prompt_input(prompt: str) -> str:
    return input(prompt).strip()


def prompt_yes_no(prompt: str) -> bool:
    while True:
        value = input(prompt).strip().lower()
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Please answer yes or no.")


def prompt_choice(prompt: str, valid: set[str]) -> str:
    while True:
        value = input(prompt).strip().lower()
        if value in valid:
            return value
        print(f"Please choose one of: {', '.join(sorted(valid))}")


def find_project_dirs() -> list[Path]:
    home = Path.home()
    results: list[Path] = []

    for path in home.rglob("projects"):
        try:
            if path.is_dir():
                results.append(path)
        except PermissionError:
            continue

    return sorted(set(p.resolve() for p in results))


def choose_projects_root() -> str:
    auto_find = prompt_yes_no("want me to find where your projects are stored? [y/n]\n> ")

    if auto_find:
        candidates = find_project_dirs()
        if not candidates:
            print("I couldn't find any directories named 'projects'.")
        else:
            print("\nI found these directories named 'projects':")
            for idx, path in enumerate(candidates, start=1):
                try:
                    display = f"~/{path.relative_to(Path.home())}"
                except ValueError:
                    display = str(path)
                print(f"{idx}. {display}")

            while True:
                selection = input("\nSelect one by number: \n> ").strip()
                if selection.isdigit():
                    num = int(selection)
                    if 1 <= num <= len(candidates):
                        return str(candidates[num - 1])
                print("Please enter a valid number.")

    while True:
        relative = input("let the user input the projects with respect to `~/`\n> ~/").strip().lstrip("/")
        full = Path.home() / relative
        if full.exists() and full.is_dir():
            return str(full.resolve())
        print(f"That directory does not exist or is not a directory: {full}")


def run_interactive_setup() -> dict:
    print("Thank you for using docsme, proceed with this interactive setup.\n")

    github_username = prompt_input("what is your github user_name?\n> ")
    projects_root = choose_projects_root()

    print("\nplease let me know your preferences for AI elaboration:")
    print("a. do not elaborate unless I pass `--use-agent`")
    print("b. elaborate with cursor by default")
    print("c. elaborate with claude by default")

    elaboration_choice = prompt_choice("> ", {"a", "b", "c"})
    ai_elaboration = {
        "a": "manual",
        "b": "cursor",
        "c": "claude",
    }[elaboration_choice]

    config = {
        "github_username": github_username,
        "projects_root": projects_root,
        "ai_elaboration": ai_elaboration,
    }
    save_config(config)
    apply_config_to_env(config)

    print(f"\nSaved configuration to {CONFIG_PATH}")
    return config


def resolve_root(args_root: str | None, config: dict) -> str | None:
    if args_root:
        return args_root
    return config.get("projects_root")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="docsme",
        description="Generate a yearly work summary from git commits across repositories.",
    )
    parser.add_argument("root", nargs="?", help="Root directory to scan, e.g. ~/projects")
    parser.add_argument("--author", help="Filter git log by author name or email")
    parser.add_argument("--since", help="Only include commits after this date/expression")
    parser.add_argument("--until", help="Only include commits before this date/expression")
    parser.add_argument("--branch", help="Optional branch/rev to run git log against")
    parser.add_argument("--output", help="Write results to .csv, .parquet, or .json")
    parser.add_argument("--preview", type=int, default=20, help="Number of rows to print to stdout")
    parser.add_argument("--use-agent", action="store_true", help="Enable AI elaboration for this run")
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run interactive first-time setup",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        config = load_config()

        if args.setup or (args.root is None and not config):
            config = run_interactive_setup()

        apply_config_to_env(config)

        root = resolve_root(args.root, config)
        if not root:
            print("Error: no projects root configured. Run `docsme --setup`.", file=sys.stderr)
            return 2

        repos = find_git_repos(root)
        if not repos:
            print(f"No git repositories found under: {Path(root).expanduser().resolve()}", file=sys.stderr)
            return 1

        df = build_commit_dataframe(
            root=root,
            author=args.author or config.get("github_username"),
            since=args.since or "January 1",
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

        use_agent = args.use_agent or config.get("ai_elaboration") in {"cursor", "claude"}
        if use_agent:
            provider = config.get("ai_elaboration", "manual")
            print(f"\nAI elaboration enabled: {provider}")

        return 0
    except (FileNotFoundError, NotADirectoryError, GitCommitsDfError, ValueError, KeyboardInterrupt) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
