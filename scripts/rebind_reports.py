#!/usr/bin/env python3
"""
Rebind thin Power BI reports to the correct semantic models after deployment.

Example use:
    python scripts/rebind_reports.py --branch develop

This script reads:
- deployment/deployment-rules.yml for environment and workspace mapping
- deployment/report-bindings.yml for report-to-semantic-model mapping
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any, Dict

import yaml

from powerbi_rest_client import PowerBIRestClient


def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required config file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def expand_env_var(value: str) -> str:
    expanded = os.path.expandvars(value)
    if expanded.startswith("${") and expanded.endswith("}"):
        raise ValueError(f"Environment variable was not resolved: {value}")
    return expanded


def environment_from_branch(rules: Dict[str, Any], branch_name: str) -> str:
    branches = rules.get("branches", {})
    if branch_name not in branches:
        raise ValueError(f"Branch '{branch_name}' is not mapped in deployment-rules.yml")
    return branches[branch_name]


def workspace_map_for_environment(rules: Dict[str, Any], environment: str) -> Dict[str, str]:
    raw = rules.get("workspaces", {}).get(environment, {})
    if not raw:
        raise ValueError(f"No workspace mapping found for environment '{environment}'.")
    return {key: expand_env_var(value) for key, value in raw.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebind Power BI reports to target semantic models.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--branch", default=os.environ.get("CI_COMMIT_BRANCH", "develop"))
    parser.add_argument("--rules", default="deployment/deployment-rules.yml")
    parser.add_argument("--bindings", default="deployment/report-bindings.yml")
    parser.add_argument("--use-default-credential", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    rules = load_yaml(repo_root / args.rules)
    bindings_doc = load_yaml(repo_root / args.bindings)

    environment = environment_from_branch(rules, args.branch)
    workspace_ids = workspace_map_for_environment(rules, environment)

    credential = (
        PowerBIRestClient.default_credential()
        if args.use_default_credential
        else PowerBIRestClient.credential_from_environment()
    )
    client = PowerBIRestClient(credential)

    for binding in bindings_doc.get("bindings", []):
        client.rebind_report_by_name(
            report_workspace_id=workspace_ids[binding["report_workspace_key"]],
            report_name=binding["report_name"],
            semantic_model_workspace_id=workspace_ids[binding["semantic_model_workspace_key"]],
            semantic_model_name=binding["semantic_model_name"],
        )

    print("[SUCCESS] Report rebind completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
