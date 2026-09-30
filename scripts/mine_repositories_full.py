"""Mine GitHub for Django repositories suitable for schema-code co-evolution study.

Adapted from STAR-RG/django-smells evaluation/mine_repositories.py.
Original: https://github.com/STAR-RG/django-smells

Full-scan version: scans up to 10 pages (1000 repos) from GitHub Search API,
verifies each as a real Django project, classifies structure, and saves all
verified candidates. No bucket-filling early stop — migration count and project
maturity are the primary selection criteria.

Differences from mine_repositories.py (original):
- Removed bucket-filling logic (Small/Medium/Large quotas)
- Scans all 10 pages instead of stopping when buckets fill
- Removed --target-total and --max-candidates args
- Added --min-migrations to highlight relevant repos in output
- Output sorted by migration_count (descending)
- All verified repos saved for transparency

Usage:
    # Dry run - estimate API calls
    python scripts/mine_repositories_full.py --dry-run

    # Full mining pass (all 10 pages)
    python scripts/mine_repositories_full.py --output data/raw/candidates_full.csv

    # Custom migration threshold
    python scripts/mine_repositories_full.py --min-migrations 20

Requires GITHUB_TOKEN env var (or .env file at project root).
"""

import argparse
import ast
import base64
import csv
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import requests
    from dotenv import load_dotenv
except ImportError:
    print("Install dependencies: pip install requests python-dotenv", file=sys.stderr)
    sys.exit(1)

GITHUB_API = "https://api.github.com"
SEARCH_PACING = 2.5
REST_PACING = 0.4
MAX_FILES_PER_KIND = 25
DEFAULT_MIN_MIGRATIONS = 15
MAX_SEARCH_PAGES = 10


@dataclass
class Candidate:
    full_name: str
    url: str
    stars: int
    pushed_at: str
    license: str
    default_branch: str
    commit_sha: str
    modules: int
    models: int
    views: int
    migration_count: int
    migration_apps: int
    size_class: str
    verification_reason: str


class GitHubClient:
    def __init__(self, token: str):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def _get(self, url, params=None, _retries=0):
        if _retries >= 5:
            raise requests.exceptions.ConnectionError(f"Failed after {_retries} retries: {url}")
        try:
            resp = self.session.get(url, params=params, timeout=30)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
            wait = min(10 * (2 ** _retries), 120)
            print(f"  connection error, retry {_retries + 1}/5 in {wait}s: {exc}", file=sys.stderr)
            time.sleep(wait)
            return self._get(url, params, _retries=_retries + 1)
        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            if _retries >= 3:
                resp.raise_for_status()
            reset = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
            wait = min(max(reset - time.time(), 1), 900)
            print(f"  rate limited, sleeping {wait:.0f}s", file=sys.stderr)
            time.sleep(wait)
            return self._get(url, params, _retries=_retries + 1)
        return resp

    def search_repositories(self, query, page, per_page=100):
        resp = self._get(f"{GITHUB_API}/search/repositories",
                         params={"q": query, "per_page": per_page, "page": page})
        resp.raise_for_status()
        return resp.json()

    def get_contents(self, full_name, path=""):
        resp = self._get(f"{GITHUB_API}/repos/{full_name}/contents/{path}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    def get_tree(self, full_name, branch):
        resp = self._get(f"{GITHUB_API}/repos/{full_name}/git/trees/{branch}",
                         params={"recursive": "1"})
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    def get_repository(self, full_name):
        resp = self._get(f"{GITHUB_API}/repos/{full_name}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    def get_branch_commit_sha(self, full_name, branch):
        resp = self._get(f"{GITHUB_API}/repos/{full_name}/commits/{branch}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json().get("sha")


def build_search_query(min_stars, pushed_since):
    return (f"django in:name,description,readme,topics "
            f"language:Python fork:false "
            f"pushed:>={pushed_since} stars:>={min_stars}")


def decode_file(contents_json):
    if not contents_json or contents_json.get("encoding") != "base64":
        return ""
    return base64.b64decode(contents_json["content"]).decode("utf-8", errors="replace")


def mentions_django_dependency(text):
    return bool(re.search(r"(?im)^\s*django\s*[=<>~!\[]", text)) or \
           bool(re.search(r'(?im)^\s*"?django"?\s*=', text))


def verify_django_project(client, full_name):
    root = client.get_contents(full_name)
    time.sleep(REST_PACING)
    if root is None or not isinstance(root, list):
        return False, "could not list repository root"
    names = {entry["name"] for entry in root}
    has_manage_py = "manage.py" in names
    for dep_file in ("requirements.txt", "pyproject.toml", "Pipfile"):
        if dep_file in names:
            file_json = client.get_contents(full_name, dep_file)
            time.sleep(REST_PACING)
            text = decode_file(file_json)
            if mentions_django_dependency(text):
                return True, f"manage.py={has_manage_py}, {dep_file} lists Django"
    if has_manage_py:
        return True, "manage.py present at repository root"
    return False, "no manage.py and no dependency file listing Django"


SIZE_THRESHOLDS = {
    "modules": {"Small": (1, 3), "Medium": (4, 10), "Large": (11, float("inf"))},
    "models": {"Small": (1, 10), "Medium": (11, 30), "Large": (31, float("inf"))},
    "views": {"Small": (1, 10), "Medium": (11, 30), "Large": (31, float("inf"))},
}


def classify_size(modules, models, views):
    def bucket(value, thresholds):
        if value <= 0:
            return "Small"
        for size, (low, high) in thresholds.items():
            if low <= value <= high:
                return size
        return "Large"
    votes = [bucket(modules, SIZE_THRESHOLDS["modules"]),
             bucket(models, SIZE_THRESHOLDS["models"]),
             bucket(views, SIZE_THRESHOLDS["views"])]
    order = {"Small": 0, "Medium": 1, "Large": 2}
    counts = {s: votes.count(s) for s in set(votes)}
    max_votes = max(counts.values())
    tied = [s for s, c in counts.items() if c == max_votes]
    return max(tied, key=lambda s: order[s])


def _is_model_base(base):
    """Name-based heuristic: matches models.Model or bare Model."""
    if isinstance(base, ast.Attribute):
        return base.attr == "Model"
    if isinstance(base, ast.Name):
        return base.id == "Model"
    return False


def classify_repository(client, full_name, default_branch):
    """Count modules, models, views, and migration files via tree API."""
    tree = client.get_tree(full_name, default_branch)
    time.sleep(REST_PACING)
    if tree is None or "tree" not in tree:
        return 0, 0, 0, 0, 0

    paths = [item["path"] for item in tree["tree"] if item.get("type") == "blob"]
    modules = sum(1 for p in paths if p.endswith("apps.py"))

    # Migration metrics
    migration_files = [p for p in paths
                       if "/migrations/" in p and p.endswith(".py")
                       and not p.endswith("__init__.py")]
    migration_count = len(migration_files)
    migration_apps = set()
    for p in migration_files:
        parts = p.split("/")
        if "migrations" in parts:
            idx = parts.index("migrations")
            if idx > 0:
                migration_apps.add(parts[idx - 1])

    # Model count
    models_files = [p for p in paths if p.endswith("models.py")][:MAX_FILES_PER_KIND]
    models_count = 0
    for path in models_files:
        content = client.get_contents(full_name, path)
        time.sleep(REST_PACING)
        text = decode_file(content)
        try:
            tree_ast = ast.parse(text)
            models_count += sum(1 for node in ast.walk(tree_ast)
                                if isinstance(node, ast.ClassDef)
                                and any(_is_model_base(b) for b in node.bases))
        except SyntaxError:
            pass

    # View count
    views_files = [p for p in paths if p.endswith("views.py")][:MAX_FILES_PER_KIND]
    views_count = 0
    for path in views_files:
        content = client.get_contents(full_name, path)
        time.sleep(REST_PACING)
        text = decode_file(content)
        try:
            tree_ast = ast.parse(text)
            views_count += sum(1 for node in tree_ast.body
                               if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                                    ast.ClassDef)))
        except SyntaxError:
            pass

    return modules, models_count, views_count, migration_count, len(migration_apps)


def run_dry_run(client, query, args):
    result = client.search_repositories(query, 1)
    time.sleep(SEARCH_PACING)
    total_count = result.get("total_count", 0)
    pages = min(MAX_SEARCH_PAGES, (total_count + 99) // 100)
    scannable = min(total_count, pages * 100)

    # Estimate: ~2 calls to verify + ~9 calls to classify per verified repo
    # Assume ~15% pass Django verification (observed rate from first run)
    est_verified = int(scannable * 0.15)
    est_calls = scannable * 2 + est_verified * 9 + pages
    est_minutes = (est_calls * REST_PACING + pages * SEARCH_PACING) / 60

    print(f"Search query: {query}")
    print(f"Total matches: {total_count}")
    print(f"Scannable (API limit {MAX_SEARCH_PAGES} pages): {scannable}")
    print(f"Estimated verified (~15%): ~{est_verified}")
    print(f"Estimated API calls: ~{est_calls}")
    print(f"Estimated time: ~{est_minutes:.1f} minutes")
    print(f"Min migrations filter: {args.min_migrations}")


def run_full_pass(client, query, args):
    all_verified = []
    checked = 0
    page = 1

    while page <= MAX_SEARCH_PAGES:
        result = client.search_repositories(query, page)
        time.sleep(SEARCH_PACING)
        items = result.get("items", [])
        if not items:
            break

        print(f"\n--- Page {page} ({len(items)} repos) ---")

        for repo in items:
            checked += 1
            full_name = repo["full_name"]
            try:
                verified, reason = verify_django_project(client, full_name)
                if not verified:
                    continue
                repo_details = client.get_repository(full_name)
                time.sleep(REST_PACING)
                default_branch = (repo_details or {}).get(
                    "default_branch", repo.get("default_branch", "main"))
                license_info = (repo_details or {}).get("license") or {}
                license_spdx = license_info.get("spdx_id") or "NOASSERTION"
                commit_sha = client.get_branch_commit_sha(full_name, default_branch) or ""
                time.sleep(REST_PACING)
                modules, models_count, views_count, mig_count, mig_apps = \
                    classify_repository(client, full_name, default_branch)
            except requests.exceptions.RequestException as exc:
                print(f"  skipping {full_name}: {exc}", file=sys.stderr)
                continue

            if modules == 0 and models_count == 0 and views_count == 0:
                print(f"  skipping {full_name}: scaffold")
                continue

            size_class = classify_size(modules, models_count, views_count)
            candidate = Candidate(
                full_name=full_name, url=repo["html_url"],
                stars=repo["stargazers_count"], pushed_at=repo["pushed_at"],
                license=license_spdx, default_branch=default_branch,
                commit_sha=commit_sha, modules=modules,
                models=models_count, views=views_count,
                migration_count=mig_count, migration_apps=mig_apps,
                size_class=size_class, verification_reason=reason,
            )
            all_verified.append(candidate)

            tag = "*" if mig_count >= args.min_migrations else " "
            print(f"  [{tag}] [{size_class}] {full_name} "
                  f"(mig={mig_count}, apps={mig_apps}, "
                  f"modules={modules}, models={models_count}, views={views_count})")

        page += 1

    # Save all verified repos (full dataset)
    all_verified.sort(key=lambda c: -c.migration_count)
    _save_candidates(all_verified, args.output)

    # Print summary
    above = [c for c in all_verified if c.migration_count >= args.min_migrations]
    below = [c for c in all_verified if c.migration_count < args.min_migrations]
    sizes = {"Small": 0, "Medium": 0, "Large": 0}
    for c in above:
        sizes[c.size_class] += 1

    print(f"\n{'='*60}")
    print(f"Checked: {checked} repos across {page - 1} pages")
    print(f"Verified as Django: {len(all_verified)}")
    print(f"With >= {args.min_migrations} migrations: {len(above)}")
    print(f"Below threshold: {len(below)}")
    print(f"Size distribution (above threshold): S={sizes['Small']}, M={sizes['Medium']}, L={sizes['Large']}")
    print(f"{'='*60}")


def _save_candidates(candidates, output_path):
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [f.name for f in fields(Candidate)]
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in candidates:
            writer.writerow(asdict(c))
    json_path = output.with_suffix(".json")
    json_path.write_text(json.dumps([asdict(c) for c in candidates], indent=2), encoding="utf-8")
    print(f"Saved to {output} and {json_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--min-stars", type=int, default=20)
    parser.add_argument("--min-migrations", type=int, default=DEFAULT_MIN_MIGRATIONS,
                        help="Minimum migration count to highlight (all repos still saved)")
    parser.add_argument("--output", default="data/raw/candidates_full.csv")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_dotenv()
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN not set (check .env or environment)", file=sys.stderr)
        sys.exit(1)

    client = GitHubClient(token)
    pushed_since = (datetime.now(timezone.utc) - timedelta(days=730)).strftime("%Y-%m-%d")
    query = build_search_query(args.min_stars, pushed_since)

    if args.dry_run:
        run_dry_run(client, query, args)
    else:
        run_full_pass(client, query, args)


if __name__ == "__main__":
    main()
