"""Clone all 124 corpus repositories for co-evolution analysis.

Uses git clone --filter=blob:none for partial clones that preserve
full commit history without downloading all blobs upfront.

Usage:
    # Dry run - list repos to clone
    python scripts/clone_corpus.py --dry-run

    # Clone all repos to data/repos/
    python scripts/clone_corpus.py

    # Clone to custom directory
    python scripts/clone_corpus.py --output /path/to/repos

    # Resume interrupted cloning (skips already cloned)
    python scripts/clone_corpus.py --resume
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLASSIFICATION_FILE = PROJECT_ROOT / "data" / "processed" / "corpus_classification.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "repos"


def load_corpus(classification_file: Path) -> list[dict]:
    """Load corpus repos (app + lib only, exclude tutorials)."""
    with open(classification_file) as f:
        data = json.load(f)
    return [r for r in data if r["nature"] in ("app", "lib")]


def clone_repo(full_name: str, output_dir: Path, timeout: int = 300) -> dict:
    """Clone a single repo with partial clone filter.

    Returns dict with status info.
    """
    owner, repo = full_name.split("/")
    repo_dir = output_dir / f"{owner}__{repo}"

    if repo_dir.exists() and (repo_dir / ".git").exists():
        return {"full_name": full_name, "status": "skipped", "reason": "already exists"}

    url = f"https://github.com/{full_name}.git"

    try:
        result = subprocess.run(
            [
                "git", "clone",
                "--filter=blob:none",
                url,
                str(repo_dir),
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode != 0:
            # Clean up failed clone
            if repo_dir.exists():
                subprocess.run(["rm", "-rf", str(repo_dir)], capture_output=True)
            return {
                "full_name": full_name,
                "status": "failed",
                "reason": result.stderr.strip()[:200],
            }

        return {"full_name": full_name, "status": "cloned", "path": str(repo_dir)}

    except subprocess.TimeoutExpired:
        if repo_dir.exists():
            subprocess.run(["rm", "-rf", str(repo_dir)], capture_output=True)
        return {"full_name": full_name, "status": "failed", "reason": "timeout"}

    except Exception as e:
        return {"full_name": full_name, "status": "failed", "reason": str(e)[:200]}


def main():
    parser = argparse.ArgumentParser(description="Clone corpus repositories")
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT,
        help=f"Output directory (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="List repos without cloning",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Skip already cloned repos",
    )
    parser.add_argument(
        "--timeout", type=int, default=300,
        help="Timeout per clone in seconds (default: 300)",
    )
    args = parser.parse_args()

    # Load corpus
    corpus = load_corpus(CLASSIFICATION_FILE)
    apps = [r for r in corpus if r["nature"] == "app"]
    libs = [r for r in corpus if r["nature"] == "lib"]

    print(f"Corpus: {len(corpus)} repos ({len(apps)} apps, {len(libs)} libs)")
    print(f"Output: {args.output}")
    print()

    if args.dry_run:
        for i, repo in enumerate(corpus, 1):
            tag = "APP" if repo["nature"] == "app" else "LIB"
            print(f"  [{tag:3s}] {i:3d}. {repo['full_name']}")
        print(f"\nTotal: {len(corpus)} repos to clone")
        return

    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)

    # Clone
    results = {"cloned": 0, "skipped": 0, "failed": 0}
    failed = []
    start_time = time.time()

    for i, repo in enumerate(corpus, 1):
        full_name = repo["full_name"]
        tag = "APP" if repo["nature"] == "app" else "LIB"

        print(f"[{i:3d}/{len(corpus)}] [{tag}] {full_name} ... ", end="", flush=True)

        result = clone_repo(full_name, args.output, timeout=args.timeout)
        status = result["status"]
        results[status] += 1

        if status == "cloned":
            print("OK")
        elif status == "skipped":
            print("SKIP (exists)")
        else:
            print(f"FAIL: {result['reason'][:80]}")
            failed.append(result)

    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"Done in {elapsed:.0f}s ({elapsed/60:.1f}min)")
    print(f"  Cloned:  {results['cloned']}")
    print(f"  Skipped: {results['skipped']}")
    print(f"  Failed:  {results['failed']}")

    if failed:
        print(f"\nFailed repos:")
        for f in failed:
            print(f"  {f['full_name']}: {f['reason'][:100]}")

        # Save failed list for retry
        failed_file = args.output / "clone_failures.json"
        with open(failed_file, "w") as fh:
            json.dump(failed, fh, indent=2)
        print(f"\nFailed list saved to {failed_file}")


if __name__ == "__main__":
    main()
