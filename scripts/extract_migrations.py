"""Extract structured migration operations from Django projects via AST parsing.

Walks a cloned Django repository, finds all migration files, and extracts
each migration's operations (AddField, CreateModel, etc.) into structured data.

Usage:
    # Analyze a single cloned repo
    python scripts/extract_migrations.py /path/to/repo

    # Analyze all repos in a directory
    python scripts/extract_migrations.py /path/to/repos/ --batch

    # Output as JSON
    python scripts/extract_migrations.py /path/to/repo --output data/processed/migrations.json
"""

import argparse
import ast
import json
import os
import sys
from pathlib import Path

# All Django migration operation types
MIGRATION_OPS = {
    "CreateModel", "DeleteModel", "RenameModel",
    "AlterModelOptions", "AlterModelTable", "AlterModelManagers",
    "AlterUniqueTogether", "AlterIndexTogether", "AlterOrderWithRespectTo",
    "AddField", "RemoveField", "AlterField", "RenameField",
    "AddIndex", "RemoveIndex", "AddConstraint", "RemoveConstraint",
    "RunSQL", "RunPython", "SeparateDatabaseAndState",
}

# Broad categories for analysis
OP_CATEGORIES = {
    "model_lifecycle": {"CreateModel", "DeleteModel", "RenameModel"},
    "field_change": {"AddField", "RemoveField", "AlterField", "RenameField"},
    "index_constraint": {"AddIndex", "RemoveIndex", "AddConstraint", "RemoveConstraint"},
    "model_meta": {"AlterModelOptions", "AlterModelTable", "AlterModelManagers",
                   "AlterUniqueTogether", "AlterIndexTogether", "AlterOrderWithRespectTo"},
    "custom": {"RunSQL", "RunPython", "SeparateDatabaseAndState"},
}


def extract_operations(filepath):
    """Parse a Django migration file and extract all operations.

    Django migrations follow a standard structure:
        class Migration(migrations.Migration):
            dependencies = [...]
            operations = [
                migrations.AddField(model_name='...', name='...', ...),
            ]

    We parse the AST to find the operations list and extract each call.
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return []

    operations = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        # Check if this is a Migration class
        is_migration = any(
            (isinstance(b, ast.Attribute) and b.attr == "Migration") or
            (isinstance(b, ast.Name) and b.id == "Migration")
            for b in node.bases
        )
        if not is_migration:
            continue

        # Find the operations = [...] assignment
        for item in node.body:
            if not isinstance(item, ast.Assign):
                continue
            for target in item.targets:
                if isinstance(target, ast.Name) and target.id == "operations":
                    if isinstance(item.value, ast.List):
                        for elt in item.value.elts:
                            op = _parse_operation(elt)
                            if op:
                                operations.append(op)

        # Also extract dependencies for context
        for item in node.body:
            if not isinstance(item, ast.Assign):
                continue
            for target in item.targets:
                if isinstance(target, ast.Name) and target.id == "dependencies":
                    pass  # Could extract deps if needed later

    return operations


def _parse_operation(node):
    """Extract operation type and key arguments from a migrations.XYZ(...) call."""
    if not isinstance(node, ast.Call):
        return None

    if isinstance(node.func, ast.Attribute):
        op_type = node.func.attr
    elif isinstance(node.func, ast.Name):
        op_type = node.func.id
    else:
        return None

    if op_type not in MIGRATION_OPS:
        return None

    result = {"type": op_type}

    # Extract key keyword arguments
    for kw in node.keywords:
        if kw.arg == "model_name" and isinstance(kw.value, ast.Constant):
            result["model"] = kw.value.value
        elif kw.arg == "name" and isinstance(kw.value, ast.Constant):
            result["field"] = kw.value.value
        elif kw.arg == "old_name" and isinstance(kw.value, ast.Constant):
            result["old_name"] = kw.value.value
        elif kw.arg == "new_name" and isinstance(kw.value, ast.Constant):
            result["new_name"] = kw.value.value

    # For CreateModel/DeleteModel/RenameModel, model name can be positional or keyword
    if op_type in ("CreateModel", "DeleteModel", "RenameModel"):
        if node.args and isinstance(node.args[0], ast.Constant):
            result["model"] = node.args[0].value
        for kw in node.keywords:
            if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                result["model"] = kw.value.value

    # Classify into broad category
    for cat, ops in OP_CATEGORIES.items():
        if op_type in ops:
            result["category"] = cat
            break

    return result


def find_migration_files(repo_path):
    """Find all Django migration files in a repository."""
    migrations = []
    for root, dirs, files in os.walk(repo_path):
        # Skip .git and common non-source directories
        if ".git" in root or "node_modules" in root or ".venv" in root:
            continue
        if os.path.basename(root) != "migrations":
            continue
        for f in sorted(files):
            if f.endswith(".py") and f != "__init__.py":
                abs_path = os.path.join(root, f)
                rel_path = os.path.relpath(abs_path, repo_path).replace("\\", "/")
                # App name is the parent of the migrations/ directory
                app = os.path.basename(os.path.dirname(root))
                migrations.append({
                    "abs_path": abs_path,
                    "rel_path": rel_path,
                    "app": app,
                    "filename": f,
                })
    return migrations


def analyze_repo(repo_path):
    """Extract all migration operations from a repository."""
    repo_path = Path(repo_path)
    repo_name = repo_path.name

    migration_files = find_migration_files(repo_path)
    results = []

    for mf in migration_files:
        ops = extract_operations(mf["abs_path"])
        results.append({
            "repository": repo_name,
            "app": mf["app"],
            "migration": mf["filename"],
            "rel_path": mf["rel_path"],
            "operation_count": len(ops),
            "operations": ops,
        })

    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", help="Path to repo or directory of repos")
    parser.add_argument("--batch", action="store_true",
                        help="Treat path as directory containing multiple repos")
    parser.add_argument("--output", help="Output JSON file path")
    args = parser.parse_args()

    path = Path(args.path)
    all_results = []

    if args.batch:
        for d in sorted(path.iterdir()):
            if d.is_dir() and (d / ".git").exists():
                print(f"Analyzing {d.name}...")
                results = analyze_repo(d)
                all_results.extend(results)
                total_ops = sum(r["operation_count"] for r in results)
                print(f"  {len(results)} migrations, {total_ops} operations")
    else:
        results = analyze_repo(path)
        all_results = results
        total_ops = sum(r["operation_count"] for r in results)
        print(f"{len(results)} migrations, {total_ops} operations")

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(all_results, indent=2), encoding="utf-8")
        print(f"Saved to {out}")
    else:
        # Print summary to stdout
        from collections import Counter
        op_counter = Counter()
        for r in all_results:
            for op in r["operations"]:
                op_counter[op["type"]] += 1
        print(f"\nTotal migrations: {len(all_results)}")
        print(f"Total operations: {sum(op_counter.values())}")
        print("\nOperation distribution:")
        for op, count in op_counter.most_common():
            print(f"  {op}: {count}")


if __name__ == "__main__":
    main()
