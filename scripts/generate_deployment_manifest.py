#!/usr/bin/env python3
"""
Generate a deployment manifest from PBIP folders.

This script scans the source folder and creates deployment/powerbi-deploy.yml.
It is intentionally simple and generic. You can extend it to support more
workspace routing rules, naming conventions, and item types.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List

import yaml


def discover_items(repo_root: Path, source_root: Path) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []

    for item_path in sorted(source_root.rglob("*.SemanticModel")):
        items.append(
            {
                "name": item_path.name.removesuffix(".SemanticModel"),
                "type": "SemanticModel",
                "workspace_key": "analytics_hub",
                "path": str(item_path.relative_to(repo_root)),
            }
        )

    for item_path in sorted(source_root.rglob("*.Report")):
        items.append(
            {
                "name": item_path.name.removesuffix(".Report"),
                "type": "Report",
                "workspace_key": "sales_spoke",
                "path": str(item_path.relative_to(repo_root)),
            }
        )

    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deployment manifest from PBIP folders.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--source-root", default="src/powerbi")
    parser.add_argument("--output", default="deployment/powerbi-deploy.yml")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    source_root = (repo_root / args.source_root).resolve()
    output_path = repo_root / args.output

    if not source_root.exists():
        raise FileNotFoundError(f"Source root not found: {source_root}")

    manifest = {
        "items": discover_items(repo_root, source_root),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(manifest, handle, sort_keys=False)

    print(f"[OK] Generated manifest: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
