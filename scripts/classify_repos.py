"""Automated heuristic classification of Django repositories as app, lib, or exclude.

Part of the TCC methodology for cross-validating manual corpus classification.
Applies structural heuristics to each repository and compares results with
the manual classification in corpus_classification.json.

Heuristic signals detected per repository:
  - Packaging: setup.py, setup.cfg with [metadata], pyproject.toml with
    [build-system], MANIFEST.in
  - Deployment: Dockerfile, docker-compose, Procfile, fly.toml, k8s/,
    deploy/ directories
  - Templates: .html files under templates/ directories (Django convention)
  - Testing tools: tox.ini (common in libraries for multi-version testing)
  - PyPI: package published on pypi.org (optional, --check-pypi)
  - Name keywords: tutorial, demo, sample, etc.

Classification rules (applied in priority order, first match wins):
  R1: Repository name contains exclude keywords -> exclude
  R2: Has packaging config, no manage.py at root -> lib
  R3: Has deployment artifacts, no packaging config -> app
  R4: Has both deployment and packaging -> app (R4a) unless on PyPI with
      few templates (R4b, lib)
  R5: Has packaging, no deployment, <=10 templates -> lib
  R6: manage.py at root with >10 templates -> app
  R7: Has packaging config (fallback) -> lib
  R8: manage.py at root (fallback) -> app
  R9: Default -> app

Agreement metrics reported:
  - Overall accuracy (% agreement with manual classification)
  - Cohen's kappa (chance-corrected agreement, Landis & Koch 1977)
  - Per-class precision, recall, F1-score
  - Confusion matrix (rows=manual, cols=automated)
  - Detailed disagreement list with rule and reason

Usage:
    # Classify and compare (requires GITHUB_TOKEN)
    python scripts/classify_repos.py

    # Include PyPI lookup for improved lib detection
    python scripts/classify_repos.py --check-pypi

    # Estimate API usage without executing
    python scripts/classify_repos.py --dry-run

    # Custom paths
    python scripts/classify_repos.py \\
        --candidates data/raw/candidates_full.json \\
        --manual data/processed/corpus_classification.json \\
        --output data/processed/corpus_classification_auto.json

Requires GITHUB_TOKEN env var (or .env file at project root).
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

try:
    import requests
    from dotenv import load_dotenv
except ImportError:
    print("Install dependencies: pip install requests python-dotenv",
          file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GITHUB_API = "https://api.github.com"
PYPI_API = "https://pypi.org/pypi"
REST_PACING = 0.4  # seconds between GitHub API calls

EXCLUDE_KEYWORDS = frozenset({
    "tutorial", "sample", "example", "demo", "course",
    "exercise", "specialization", "styleguide", "boilerplate",
    "starter", "skeleton",
})

# Directories where manage.py indicates testing/example setup, not the main app
TEST_EXAMPLE_DIRS = frozenset({
    "tests", "test", "testing", "example", "examples",
    "testapp", "sandbox", "demo", "sample",
})

# Kappa interpretation thresholds (Landis & Koch, 1977)
KAPPA_INTERPRETATION = [
    (0.81, "almost perfect"),
    (0.61, "substantial"),
    (0.41, "moderate"),
    (0.21, "fair"),
    (0.01, "slight"),
    (-1.0, "less than chance"),
]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class RepoSignals:
    """Structural signals detected from a repository's tree and file contents.

    Each field is a binary indicator (or count) used by the classification
    rules. Signals are designed to be independent and objectively verifiable.
    """
    has_manage_py_root: bool = False
    has_manage_py_in_tests: bool = False
    has_setup_py: bool = False
    has_setup_cfg_packaging: bool = False
    has_pyproject_build: bool = False
    has_manifest_in: bool = False
    has_dockerfile: bool = False
    has_docker_compose: bool = False
    has_procfile: bool = False
    has_deploy_dir: bool = False
    has_tox_ini: bool = False
    template_count: int = 0
    on_pypi: bool = False
    exclude_keywords_in_name: bool = False


@dataclass
class ClassificationResult:
    """Automated classification for a single repository."""
    full_name: str
    nature: str
    rule: str
    reason: str
    signals: dict


# ---------------------------------------------------------------------------
# GitHub API client
# ---------------------------------------------------------------------------

class GitHubClient:
    """Minimal GitHub REST API client with rate-limit handling and retries.

    Same pattern as mine_repositories_full.py for consistency.
    """

    def __init__(self, token: str):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def _get(self, url: str, params: Optional[dict] = None,
             _retries: int = 0) -> requests.Response:
        if _retries >= 5:
            raise requests.exceptions.ConnectionError(
                f"Failed after {_retries} retries: {url}")
        try:
            resp = self.session.get(url, params=params, timeout=30)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout) as exc:
            wait = min(10 * (2 ** _retries), 120)
            print(f"  connection error, retry {_retries + 1}/5 in {wait}s: "
                  f"{exc}", file=sys.stderr)
            time.sleep(wait)
            return self._get(url, params, _retries=_retries + 1)
        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            if _retries >= 3:
                resp.raise_for_status()
            reset = int(resp.headers.get("X-RateLimit-Reset",
                                         time.time() + 60))
            wait = min(max(reset - time.time(), 1), 900)
            print(f"  rate limited, sleeping {wait:.0f}s", file=sys.stderr)
            time.sleep(wait)
            return self._get(url, params, _retries=_retries + 1)
        return resp

    def get_tree(self, full_name: str, ref: str) -> Optional[dict]:
        """Fetch the full recursive tree for a repo at a given ref (SHA or branch)."""
        resp = self._get(f"{GITHUB_API}/repos/{full_name}/git/trees/{ref}",
                         params={"recursive": "1"})
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    def get_file_content(self, full_name: str, path: str) -> Optional[str]:
        """Fetch and decode the text content of a single file."""
        resp = self._get(f"{GITHUB_API}/repos/{full_name}/contents/{path}")
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("encoding") != "base64":
            return None
        return base64.b64decode(data["content"]).decode("utf-8",
                                                        errors="replace")


# ---------------------------------------------------------------------------
# Signal detection
# ---------------------------------------------------------------------------

def _has_exclude_keywords(repo_name: str) -> bool:
    """Check if the repository name contains tutorial/demo/sample keywords.

    Handles plurals (e.g., 'samples' matches 'sample') by checking both
    exact tokens and tokens with trailing 's' stripped.
    """
    name_lower = repo_name.lower()
    tokens = set(re.split(r"[-_.]", name_lower))
    # Also check singular forms for pluralized tokens
    singulars = {t.rstrip("s") for t in tokens if t.endswith("s") and len(t) > 3}
    all_tokens = tokens | singulars
    return bool(all_tokens & EXCLUDE_KEYWORDS)


def detect_signals(client: GitHubClient, full_name: str, ref: str,
                   check_pypi: bool = False) -> Optional[RepoSignals]:
    """Detect structural signals from a repository's file tree.

    Uses the Git Tree API (single call) to scan all file paths, then reads
    specific files (setup.cfg, pyproject.toml) when present to check for
    packaging configuration sections.

    Args:
        client: GitHub API client.
        full_name: Repository identifier (owner/repo).
        ref: Git ref to inspect (commit SHA or branch name).
        check_pypi: Whether to check PyPI for package existence.

    Returns:
        RepoSignals with all detected indicators, or None if the tree
        cannot be fetched (repo deleted, private, or ref invalid).
    """
    signals = RepoSignals()
    repo_name = full_name.split("/")[-1]

    # --- Name keywords ---
    signals.exclude_keywords_in_name = _has_exclude_keywords(repo_name)

    # --- Fetch tree ---
    tree_data = client.get_tree(full_name, ref)
    time.sleep(REST_PACING)
    if tree_data is None or "tree" not in tree_data:
        return None

    if tree_data.get("truncated"):
        print(f"  warning: tree truncated for {full_name}", file=sys.stderr)

    entries = tree_data["tree"]
    blob_paths = [e["path"] for e in entries if e.get("type") == "blob"]
    tree_paths = {e["path"] for e in entries if e.get("type") == "tree"}
    root_files = {p for p in blob_paths if "/" not in p}
    root_files_lower = {f.lower() for f in root_files}

    # --- manage.py ---
    signals.has_manage_py_root = "manage.py" in root_files
    for p in blob_paths:
        if p.endswith("/manage.py") and "/" in p:
            top_dir = p.split("/")[0].lower()
            if top_dir in TEST_EXAMPLE_DIRS:
                signals.has_manage_py_in_tests = True
                break

    # --- Packaging signals ---
    signals.has_setup_py = "setup.py" in root_files
    signals.has_manifest_in = "MANIFEST.in" in root_files

    if "setup.cfg" in root_files:
        content = client.get_file_content(full_name, "setup.cfg")
        time.sleep(REST_PACING)
        if content and re.search(r"^\[(metadata|options)\]",
                                 content, re.MULTILINE):
            signals.has_setup_cfg_packaging = True

    if "pyproject.toml" in root_files:
        content = client.get_file_content(full_name, "pyproject.toml")
        time.sleep(REST_PACING)
        if content and re.search(r"^\[build-system\]",
                                 content, re.MULTILINE):
            signals.has_pyproject_build = True

    # --- Deployment signals ---
    # Root-level files (case-insensitive for Dockerfile variants)
    for f in root_files:
        fl = f.lower()
        if fl == "dockerfile" or fl.startswith("dockerfile."):
            signals.has_dockerfile = True
        elif fl in ("docker-compose.yml", "docker-compose.yaml",
                     "compose.yml", "compose.yaml"):
            signals.has_docker_compose = True
        elif fl == "procfile":
            signals.has_procfile = True

    # Deploy-related directories
    deploy_dir_names = {"deploy", ".deploy", "k8s", "kubernetes", "helm",
                        ".heroku", "docker"}
    for d in tree_paths:
        top_dir = d.split("/")[0].lower()
        if top_dir in deploy_dir_names:
            signals.has_deploy_dir = True
            break

    # Platform config files at root (fly.toml, railway.json, etc.)
    platform_configs = {"fly.toml", "railway.json", "render.yaml",
                        "app.yaml", "heroku.yml", "app.json"}
    if root_files_lower & {c.lower() for c in platform_configs}:
        signals.has_deploy_dir = True

    # --- Testing tools ---
    signals.has_tox_ini = "tox.ini" in root_files

    # --- Templates ---
    signals.template_count = sum(
        1 for p in blob_paths
        if "/templates/" in p and p.endswith(".html")
    )

    # --- PyPI ---
    if check_pypi:
        signals.on_pypi = _check_pypi(repo_name)

    return signals


def _check_pypi(repo_name: str) -> bool:
    """Check if a package with this name (or common variants) exists on PyPI."""
    candidates = {
        repo_name,
        repo_name.replace("_", "-"),
        repo_name.replace("-", "_"),
    }
    for name in candidates:
        try:
            resp = requests.get(f"{PYPI_API}/{name}/json", timeout=10)
            if resp.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(0.3)
    return False


# ---------------------------------------------------------------------------
# Classification rules
# ---------------------------------------------------------------------------

def classify(signals: RepoSignals) -> tuple[str, str, str]:
    """Apply classification decision rules to a set of repository signals.

    Rules are applied in priority order; the first matching rule determines
    the classification. Each rule is identified by a code (R1-R9) for
    traceability in the comparison report.

    Returns:
        Tuple of (nature, rule_id, reason).
    """
    has_packaging = (signals.has_setup_py
                     or signals.has_setup_cfg_packaging
                     or signals.has_pyproject_build)
    has_deploy = (signals.has_dockerfile
                  or signals.has_docker_compose
                  or signals.has_procfile
                  or signals.has_deploy_dir)

    # R1: Repository name contains tutorial/demo/sample keywords
    if signals.exclude_keywords_in_name:
        return ("exclude", "R1",
                "repository name contains exclude keyword")

    # R2: Packaging config present, no manage.py at root
    # Strong lib signal: the project is structured as an installable package.
    if has_packaging and not signals.has_manage_py_root:
        return ("lib", "R2",
                "packaging config present, no manage.py at root")

    # R3: Deployment artifacts present, no packaging config
    # Strong app signal: project is deployed, not installed as a package.
    if has_deploy and not has_packaging:
        return ("app", "R3",
                "deployment artifacts present, no packaging config")

    # R4: Both deployment and packaging present
    # Ambiguous case. Some apps are distributed as pip packages (e.g. modoboa).
    # Some libs have docker-compose for local development.
    if has_deploy and has_packaging:
        # R4b: If on PyPI with few templates, the primary purpose is likely
        # the reusable package, and deployment is for dev/testing.
        if signals.on_pypi and signals.template_count <= 10:
            return ("lib", "R4b",
                    "on PyPI with few templates, deployment likely dev-only")
        # R4a: Otherwise, deployment signals dominate. Apps sometimes include
        # setup.py for installation convenience.
        return ("app", "R4a",
                "deployment + packaging (app distributed as package)")

    # R5: Packaging present, no deployment, few templates
    # Without deployment artifacts, a packaged project with few templates is
    # likely a reusable library (templates, if any, are admin/widget defaults).
    if has_packaging and not has_deploy and signals.template_count <= 10:
        return ("lib", "R5",
                f"packaging config, {signals.template_count} templates, "
                f"no deployment")

    # R6: manage.py at root with many templates
    # A project serving many HTML templates is a web application.
    if signals.has_manage_py_root and signals.template_count > 10:
        return ("app", "R6",
                f"manage.py at root, {signals.template_count} HTML templates")

    # R7: Packaging config present (fallback)
    if has_packaging:
        return ("lib", "R7",
                "packaging config present (fallback)")

    # R8: manage.py at root (fallback)
    if signals.has_manage_py_root:
        return ("app", "R8",
                "manage.py at root (fallback)")

    # R9: Default classification
    return ("app", "R9",
            "default classification (no strong signals detected)")


# ---------------------------------------------------------------------------
# Agreement metrics
# ---------------------------------------------------------------------------

def compute_cohens_kappa(labels_a: list[str], labels_b: list[str],
                         classes: list[str]) -> float:
    """Compute Cohen's kappa coefficient for inter-rater agreement.

    Measures agreement beyond what would be expected by chance.

    Reference: Cohen, J. (1960). A coefficient of agreement for nominal
    scales. Educational and Psychological Measurement, 20(1), 37-46.

    Args:
        labels_a: First set of classifications (e.g., manual).
        labels_b: Second set of classifications (e.g., automated).
        classes: List of all possible class labels.

    Returns:
        Kappa coefficient in [-1, 1]. Values:
          0.81-1.00 = almost perfect agreement
          0.61-0.80 = substantial agreement
          0.41-0.60 = moderate agreement
          0.21-0.40 = fair agreement
          0.01-0.20 = slight agreement
          < 0        = less than chance agreement
    """
    n = len(labels_a)
    if n == 0:
        return 0.0

    # Observed agreement
    p_o = sum(1 for a, b in zip(labels_a, labels_b) if a == b) / n

    # Expected agreement by chance
    p_e = sum(
        (sum(1 for x in labels_a if x == c) / n)
        * (sum(1 for x in labels_b if x == c) / n)
        for c in classes
    )

    if p_e >= 1.0:
        return 1.0
    return (p_o - p_e) / (1 - p_e)


def interpret_kappa(kappa: float) -> str:
    """Interpret kappa value according to Landis & Koch (1977)."""
    for threshold, label in KAPPA_INTERPRETATION:
        if kappa >= threshold:
            return label
    return "undefined"


def compute_comparison(manual_map: dict[str, str],
                       auto_results: list[ClassificationResult]) -> dict:
    """Compare automated classification against manual ground truth.

    Computes overall accuracy, Cohen's kappa, per-class precision/recall/F1,
    confusion matrix, and a detailed list of disagreements.

    Args:
        manual_map: {full_name: nature} from manual classification.
        auto_results: List of ClassificationResult from automated pipeline.

    Returns:
        Dictionary with all comparison metrics and disagreement details.
    """
    auto_map = {r.full_name: r.nature for r in auto_results}
    auto_by_name = {r.full_name: r for r in auto_results}
    common = sorted(set(manual_map) & set(auto_map))
    classes = ["app", "lib", "exclude"]

    manual_labels = [manual_map[n] for n in common]
    auto_labels = [auto_map[n] for n in common]

    agree = sum(1 for m, a in zip(manual_labels, auto_labels) if m == a)
    accuracy = agree / len(common) if common else 0

    kappa = compute_cohens_kappa(manual_labels, auto_labels, classes)

    # Confusion matrix (rows = manual, cols = automated)
    matrix = {m: {a: 0 for a in classes} for m in classes}
    for m, a in zip(manual_labels, auto_labels):
        matrix[m][a] += 1

    # Per-class precision, recall, F1
    per_class = {}
    for c in classes:
        tp = matrix[c][c]
        fp = sum(matrix[other][c] for other in classes if other != c)
        fn = sum(matrix[c][other] for other in classes if other != c)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        per_class[c] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "support": sum(matrix[c].values()),
        }

    # Disagreements with context
    disagreements = []
    for name in common:
        if manual_map[name] != auto_map[name]:
            result = auto_by_name[name]
            disagreements.append({
                "full_name": name,
                "manual": manual_map[name],
                "automated": auto_map[name],
                "rule": result.rule,
                "reason": result.reason,
            })

    return {
        "total_compared": len(common),
        "agreements": agree,
        "accuracy": round(accuracy, 4),
        "cohens_kappa": round(kappa, 4),
        "kappa_interpretation": interpret_kappa(kappa),
        "confusion_matrix": matrix,
        "per_class_metrics": per_class,
        "disagreements": disagreements,
        "disagreement_count": len(disagreements),
    }


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def print_report(report: dict):
    """Print human-readable comparison report to stdout."""
    sep = "=" * 64
    print(f"\n{sep}")
    print("CLASSIFICATION COMPARISON REPORT")
    print(f"{sep}")
    print(f"Total repos compared:  {report['total_compared']}")
    print(f"Agreements:            {report['agreements']}")
    print(f"Disagreements:         {report['disagreement_count']}")
    print(f"Accuracy:              {report['accuracy']:.1%}")
    print(f"Cohen's kappa:         {report['cohens_kappa']:.4f} "
          f"({report['kappa_interpretation']})")

    # Confusion matrix
    classes = ["app", "lib", "exclude"]
    print(f"\nConfusion matrix (rows=manual, cols=automated):")
    header = f"{'':>14}" + "".join(f"{c:>10}" for c in classes)
    print(header)
    print(f"{'':>14}" + "-" * 30)
    for row_class in classes:
        row = f"{row_class:>14}" + "".join(
            f"{report['confusion_matrix'][row_class][col]:>10}"
            for col in classes
        )
        print(row)

    # Per-class metrics
    print(f"\nPer-class metrics:")
    print(f"{'Class':>14} {'Prec':>8} {'Recall':>8} {'F1':>8} {'Support':>8}")
    print(f"{'':>14}" + "-" * 32)
    for c in classes:
        m = report["per_class_metrics"][c]
        print(f"{c:>14} {m['precision']:>8.2%} {m['recall']:>8.2%} "
              f"{m['f1']:>8.2%} {m['support']:>8}")

    # Disagreements
    if report["disagreements"]:
        print(f"\nDisagreements ({report['disagreement_count']}):")
        for d in report["disagreements"]:
            print(f"  {d['full_name']}")
            print(f"    manual={d['manual']}  auto={d['automated']}  "
                  f"rule={d['rule']}")
            print(f"    reason: {d['reason']}")
    else:
        print("\nNo disagreements found.")

    print(sep)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_candidates(path: str) -> dict[str, dict]:
    """Load mining candidates and index by full_name."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {c["full_name"]: c for c in data}


def load_manual_classification(path: str) -> dict[str, str]:
    """Load manual classification as {full_name: nature}."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {entry["full_name"]: entry["nature"] for entry in data}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_dry_run(repos: list[dict], check_pypi: bool):
    """Estimate API calls and time without executing."""
    n = len(repos)
    tree_calls = n
    # On average, ~1 content read per repo (setup.cfg or pyproject.toml)
    content_calls = n
    pypi_calls = n if check_pypi else 0
    total_github = tree_calls + content_calls
    est_seconds = total_github * REST_PACING + pypi_calls * 0.3
    est_minutes = est_seconds / 60

    print(f"Repositories to classify:    {n}")
    print(f"Estimated GitHub API calls:  ~{total_github}")
    print(f"Estimated PyPI API calls:    {pypi_calls}")
    print(f"Estimated time:              ~{est_minutes:.1f} minutes")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--candidates", default="data/raw/candidates_full.json",
        help="Path to mining candidates JSON "
             "(default: data/raw/candidates_full.json)")
    parser.add_argument(
        "--manual", default="data/processed/corpus_classification.json",
        help="Path to manual classification JSON "
             "(default: data/processed/corpus_classification.json)")
    parser.add_argument(
        "--output", default="data/processed/corpus_classification_auto.json",
        help="Path to save automated classification "
             "(default: data/processed/corpus_classification_auto.json)")
    parser.add_argument(
        "--report", default="data/processed/classification_report.json",
        help="Path to save comparison report "
             "(default: data/processed/classification_report.json)")
    parser.add_argument(
        "--check-pypi", action="store_true",
        help="Check PyPI for package existence (slower, improves lib "
             "detection in ambiguous cases)")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Estimate API calls without executing")
    args = parser.parse_args()

    load_dotenv()
    token = os.environ.get("GITHUB_TOKEN")
    if not token and not args.dry_run:
        print("GITHUB_TOKEN not set (check .env or environment)",
              file=sys.stderr)
        sys.exit(1)

    # Load data
    candidates = load_candidates(args.candidates)
    manual_map = load_manual_classification(args.manual)

    # Build list: classify repos present in both candidates and manual
    repos_to_classify = []
    missing = []
    for full_name in manual_map:
        if full_name in candidates:
            repos_to_classify.append(candidates[full_name])
        else:
            missing.append(full_name)

    print(f"Repos in manual classification: {len(manual_map)}")
    print(f"Repos found in candidates:      {len(repos_to_classify)}")
    if missing:
        print(f"Missing from candidates:        {len(missing)}")
        for name in missing:
            print(f"  - {name}")

    if args.dry_run:
        run_dry_run(repos_to_classify, args.check_pypi)
        return

    # Classify each repository
    client = GitHubClient(token)
    results: list[ClassificationResult] = []
    skipped: list[str] = []

    for i, repo in enumerate(repos_to_classify, 1):
        full_name = repo["full_name"]
        # Use recorded commit SHA for reproducibility; fall back to branch
        ref = repo.get("commit_sha") or repo.get("default_branch", "main")
        print(f"[{i}/{len(repos_to_classify)}] {full_name} ... ",
              end="", flush=True)

        try:
            signals = detect_signals(client, full_name, ref,
                                      check_pypi=args.check_pypi)
        except requests.exceptions.RequestException as exc:
            print(f"ERROR ({exc})")
            skipped.append(full_name)
            continue

        if signals is None:
            print("SKIP (tree not accessible)")
            skipped.append(full_name)
            continue

        nature, rule, reason = classify(signals)
        result = ClassificationResult(
            full_name=full_name,
            nature=nature,
            rule=rule,
            reason=reason,
            signals=asdict(signals),
        )
        results.append(result)

        manual_label = manual_map.get(full_name, "?")
        match_str = "==" if nature == manual_label else "!="
        print(f"{nature} ({rule}) [{match_str} manual:{manual_label}]")

    # Save automated classification
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    auto_data = [asdict(r) for r in results]
    output_path.write_text(
        json.dumps(auto_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nSaved automated classification: {output_path}")

    # Compute and save comparison report
    report = compute_comparison(manual_map, results)
    report["skipped"] = skipped
    report["missing_from_candidates"] = missing

    report_path = Path(args.report)
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Saved comparison report: {report_path}")

    # Print report
    print_report(report)


if __name__ == "__main__":
    main()
