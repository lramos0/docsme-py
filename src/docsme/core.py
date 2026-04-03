from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable

import pandas as pd


GIT_LOG_FORMAT = "\x1f".join(
    [
        "%H",   # full commit hash
        "%h",   # short hash
        "%an",  # author name
        "%ae",  # author email
        "%aI",  # author date (strict ISO 8601)
        "%cn",  # committer name
        "%ce",  # committer email
        "%s",   # subject
        "%b",   # body
    ]
) + "\x1e"


class GitCommitsDfError(RuntimeError):
    """Raised when git commit collection fails."""


def find_git_repos(root: str | Path) -> list[Path]:
    """Find git repositories recursively under *root*.

    A repository is identified by the presence of a `.git` directory.
    Nested repos are returned too.
    """
    root_path = Path(root).expanduser().resolve()
    if not root_path.exists():
        raise FileNotFoundError(f"Directory does not exist: {root_path}")
    if not root_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {root_path}")

    repos: list[Path] = []
    for git_dir in root_path.rglob(".git"):
        if git_dir.is_dir():
            repos.append(git_dir.parent)
    return sorted(set(repos))


def _run_git_log(
    repo_path: Path,
    author: str | None = None,
    since: str | None = None,
    until: str | None = None,
    branch: str | None = None,
) -> str:
    cmd = [
        "git",
        "-C",
        str(repo_path),
        "log",
        f"--pretty=format:{GIT_LOG_FORMAT}",
        "--date=iso-strict",
    ]

    if author:
        cmd.append(f"--author={author}")
    if since:
        cmd.append(f"--since={since}")
    if until:
        cmd.append(f"--until={until}")
    if branch:
        cmd.append(branch)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise GitCommitsDfError(
            f"git log failed for {repo_path}: {result.stderr.strip() or result.stdout.strip()}"
        )
    return result.stdout


def _parse_git_log(repo_path: Path, raw_log: str) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for entry in raw_log.split("\x1e"):
        if not entry.strip():
            continue
        parts = entry.split("\x1f")
        if len(parts) != 9:
            continue
        (
            commit_hash,
            short_hash,
            author_name,
            author_email,
            author_date,
            committer_name,
            committer_email,
            subject,
            body,
        ) = parts
        records.append(
            {
                "repo_name": repo_path.name,
                "repo_path": str(repo_path),
                "commit_hash": commit_hash,
                "short_hash": short_hash,
                "author_name": author_name,
                "author_email": author_email,
                "author_date": author_date,
                "committer_name": committer_name,
                "committer_email": committer_email,
                "subject": subject.strip(),
                "body": body.strip(),
            }
        )
    return records


def build_commit_dataframe(
    root: str | Path,
    author: str | None = None,
    since: str | None = None,
    until: str | None = None,
    branch: str | None = None,
) -> pd.DataFrame:
    """Build a DataFrame of commits across all git repos under *root*."""
    repos = find_git_repos(root)
    all_records: list[dict[str, object]] = []

    for repo in repos:
        raw_log = _run_git_log(
            repo_path=repo,
            author=author,
            since=since,
            until=until,
            branch=branch,
        )
        all_records.extend(_parse_git_log(repo, raw_log))

    df = pd.DataFrame(all_records)
    if df.empty:
        return pd.DataFrame(
            columns=[
                "repo_name",
                "repo_path",
                "commit_hash",
                "short_hash",
                "author_name",
                "author_email",
                "author_date",
                "committer_name",
                "committer_email",
                "subject",
                "body",
            ]
        )

    df["author_date"] = pd.to_datetime(df["author_date"], utc=True, errors="coerce")
    df = df.sort_values(["author_date", "repo_name"], ascending=[False, True]).reset_index(drop=True)
    return df


def export_dataframe(df: pd.DataFrame, output_path: str | Path) -> Path:
    """Export DataFrame to csv, parquet, or json based on file extension."""
    path = Path(output_path).expanduser().resolve()
    suffix = path.suffix.lower()

    if suffix == ".csv":
        df.to_csv(path, index=False)
    elif suffix == ".parquet":
        df.to_parquet(path, index=False)
    elif suffix == ".json":
        df.to_json(path, orient="records", indent=2, date_format="iso")
    else:
        raise ValueError("Output file must end with .csv, .parquet, or .json")

    return path
