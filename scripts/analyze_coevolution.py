"""Analyze co-evolution between Django migrations and application code.

For each migration in a cloned repository, finds the commit that introduced it,
measures which code files changed in that commit, and computes impact metrics.

Usage:
    # Analyze a single repo
    python scripts/analyze_coevolution.py /path/to/repo

    # Analyze all repos in a directory, save results
    python scripts/analyze_coevolution.py /path/to/repos/ --batch --output data/processed/coevolution.json

    # Filter outlier commits (>50 files)
    python scripts/analyze_coevolution.py /path/to/repos/ --batch --max-commit-files 50
"""

import argparse
import ast
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Reuse the migration parser
sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_migrations import extract_operations, find_migration_files


def run(cmd, cwd=None, timeout=120):
    """Run a git command and return stdout."""
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                       timeout=timeout, encoding="utf-8", errors="replace")
    return r.stdout or "", r.stderr or "", r.returncode


def find_migration_commit(repo_path, rel_path):
    """Find the commit that first added a migration file."""
    out, _, rc = run(
        ["git", "log", "--diff-filter=A", "--format=%H|%aI|%s",
         "--follow", "--", rel_path],
        cwd=repo_path
    )
    if rc != 0 or not out.strip():
        return None
    lines = [l for l in out.strip().split("\n") if "|" in l]
    if not lines:
        return None
    # Last line = earliest commit that added the file
    parts = lines[-1].split("|", 2)
    return {
        "sha": parts[0],
        "date": parts[1],
        "message": parts[2] if len(parts) > 2 else "",
    }


def get_commit_file_stats(repo_path, sha):
    """Get files changed in a commit with line counts."""
    out, _, rc = run(
        ["git", "diff-tree", "--no-commit-id", "-r", "--numstat", sha],
        cwd=repo_path
    )
    if rc != 0:
        return []
    files = []
    for line in out.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 3:
            added = int(parts[0]) if parts[0] != "-" else 0
            removed = int(parts[1]) if parts[1] != "-" else 0
            files.append({
                "file": parts[2],
                "lines_added": added,
                "lines_removed": removed,
            })
    return files


def classify_file(filepath):
    """Classify a file by its role in a Django project."""
    if "/migrations/" in filepath:
        return "migration"
    bn = os.path.basename(filepath)
    if bn == "models.py" or "/models/" in filepath:
        return "model"
    if bn == "views.py" or "/views/" in filepath:
        return "view"
    if bn == "serializers.py" or "/serializers/" in filepath:
        return "serializer"
    if bn == "forms.py" or "/forms/" in filepath:
        return "form"
    if bn == "admin.py":
        return "admin"
    if "test" in filepath.lower():
        return "test"
    if bn == "urls.py":
        return "url"
    if filepath.endswith(".html"):
        return "template"
    if filepath.endswith(".py"):
        return "other_python"
    return "other"


def analyze_repo(repo_path, max_commit_files=None):
    """Run the full co-evolution pipeline on one repository.

    For each migration file:
    1. Parse its operations (AST)
    2. Find the commit that introduced it (git log)
    3. Measure what else changed in that commit (git diff-tree)
    4. Classify the changed files by Django role
    """
    repo_path = Path(repo_path)
    repo_name = repo_path.name

    migration_files = find_migration_files(repo_path)
    if not migration_files:
        return []

    results = []
    for mf in migration_files:
        # 1. Parse operations
        ops = extract_operations(mf["abs_path"])
        if not ops:
            continue

        # 2. Find introducing commit
        commit = find_migration_commit(repo_path, mf["rel_path"])
        if not commit:
            continue

        # 3. Get files changed in that commit
        changed_files = get_commit_file_stats(repo_path, commit["sha"])

        # Optional: skip outlier commits
        if max_commit_files and len(changed_files) > max_commit_files:
            continue

        # 4. Classify and compute metrics
        code_files = [f for f in changed_files if classify_file(f["file"]) != "migration"]
        categories = defaultdict(int)
        for f in changed_files:
            categories[classify_file(f["file"])] += 1

        total_added = sum(f["lines_added"] for f in code_files)
        total_removed = sum(f["lines_removed"] for f in code_files)

        results.append({
            "repository": repo_name,
            "app": mf["app"],
            "migration": mf["filename"],
            "operations": ops,
            "operation_types": [o["type"] for o in ops],
            "commit_sha": commit["sha"][:12],
            "commit_date": commit["date"],
            "commit_message": commit["message"][:200],
            "total_files_in_commit": len(changed_files),
            "code_files_changed": len(code_files),
            "lines_added": total_added,
            "lines_removed": total_removed,
            "total_churn": total_added + total_removed,
            "file_categories": dict(categories),
        })

    return results


def print_summary(all_results):
    """Print aggregate statistics."""
    total = len(all_results)
    if not total:
        print("No results.")
        return

    with_code = sum(1 for r in all_results if r["code_files_changed"] > 0)
    avg_files = sum(r["code_files_changed"] for r in all_results) / total
    avg_churn = sum(r["total_churn"] for r in all_results) / total

    # Operation distribution
    op_counts = Counter()
    for r in all_results:
        for op_type in r["operation_types"]:
            op_counts[op_type] += 1

    # Category distribution
    cat_counts = Counter()
    for r in all_results:
        for cat, n in r["file_categories"].items():
            cat_counts[cat] += n

    # Churn by operation type
    churn_by_op = defaultdict(list)
    for r in all_results:
        for op in r["operations"]:
            churn_by_op[op["type"]].append(r["total_churn"])

    sep = "=" * 60
    print(f"\n{sep}")
    print("CO-EVOLUTION ANALYSIS SUMMARY")
    print(sep)
    print(f"  Migration-commit pairs: {total}")
    print(f"  With code changes: {with_code} ({100*with_code/total:.0f}%)")
    print(f"  Avg code files changed: {avg_files:.1f}")
    print(f"  Avg total churn (LOC): {avg_churn:.1f}")

    print(f"\n  Operation types:")
    for op, n in op_counts.most_common():
        avg = sum(churn_by_op[op]) / len(churn_by_op[op]) if churn_by_op[op] else 0
        print(f"    {op}: {n} (avg churn: {avg:.0f} LOC)")

    print(f"\n  File categories changed alongside migrations:")
    for cat, n in cat_counts.most_common():
        print(f"    {cat}: {n}")

    # Co-evolution ratio by repo
    repos = defaultdict(lambda: {"total": 0, "with_code": 0})
    for r in all_results:
        repos[r["repository"]]["total"] += 1
        if r["code_files_changed"] > 0:
            repos[r["repository"]]["with_code"] += 1

    print(f"\n  Per-repo co-evolution ratio:")
    for repo, counts in sorted(repos.items()):
        ratio = counts["with_code"] / counts["total"] if counts["total"] else 0
        print(f"    {repo}: {counts['with_code']}/{counts['total']} ({100*ratio:.0f}%)")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", help="Path to repo or directory of repos")
    parser.add_argument("--batch", action="store_true",
                        help="Treat path as directory containing multiple repos")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--max-commit-files", type=int, default=None,
                        help="Skip commits with more than N files (outlier filter)")
    args = parser.parse_args()

    path = Path(args.path)
    all_results = []

    if args.batch:
        for d in sorted(path.iterdir()):
            if d.is_dir() and (d / ".git").exists():
                print(f"Analyzing {d.name}...")
                results = analyze_repo(d, args.max_commit_files)
                all_results.extend(results)
                print(f"  {len(results)} migration-commit pairs")
    else:
        all_results = analyze_repo(path, args.max_commit_files)

    print_summary(all_results)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(all_results, indent=2, default=str), encoding="utf-8")
        print(f"\nSaved {len(all_results)} results to {out}")


if __name__ == "__main__":
    main()
