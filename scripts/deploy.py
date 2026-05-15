#!/usr/bin/env python3
"""
Main deployment entry point for the Power BI GitLab CI/CD Framework.

What this script does:
1. Reads deployment rules and manifest files.
2. Maps the current GitLab branch to DEV, SIT, or PRD.
3. Resolves workspace IDs from GitLab CI/CD environment variables.
4. Deploys PBIP semantic models and reports using fabric-cicd.
5. Rebinds thin reports to the correct semantic model in the target environment.

Example:
    python scripts/deploy.py --branch develop
    python scripts/deploy.py --branch sit
    python scripts/deploy.py --branch main
"""

from __future__ import annotations

import argparse
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

from fabric_cicd_deployer import deploy_pbip_items
from powerbi_rest_client import PowerBIRestClient


@dataclass(frozen=True)
class DeploymentItem:
    name: str
    type: str
    workspace_key: str
    path: Path


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
        valid = ", ".join(branches.keys())
        raise ValueError(f"Branch '{branch_name}' is not mapped. Valid branches: {valid}")
    return branches[branch_name]


def workspace_map_for_environment(rules: Dict[str, Any], environment: str) -> Dict[str, str]:
    raw = rules.get("workspaces", {}).get(environment)
    if not raw:
        raise ValueError(f"No workspace mapping found for environment '{environment}'.")
    return {workspace_key: expand_env_var(workspace_id) for workspace_key, workspace_id in raw.items()}


def parse_deployment_items(manifest: Dict[str, Any], repo_root: Path) -> List[DeploymentItem]:
    items: List[DeploymentItem] = []
    for raw in manifest.get("items", []):
        items.append(
            DeploymentItem(
                name=raw["name"],
                type=raw["type"],
                workspace_key=raw["workspace_key"],
                path=(repo_root / raw["path"]).resolve(),
            )
        )
    return items


def deploy_items(
    *,
    credential,
    environment: str,
    items: List[DeploymentItem],
    workspace_ids: Dict[str, str],
) -> None:
    """
    Groups PBIP items by target workspace, item type, and parent folder.

    fabric-cicd expects repository_directory to point to the folder that contains
    one or more PBIP item folders.
    """
    deployment_groups: Dict[Tuple[str, str, Path], List[DeploymentItem]] = {}

    for item in items:
        if item.workspace_key not in workspace_ids:
            raise KeyError(f"Workspace key '{item.workspace_key}' is not defined for {environment}.")
        if not item.path.exists():
            raise FileNotFoundError(
                f"PBIP item path does not exist: {item.path}\n"
                "For a real implementation, export/save the PBIP item into this folder."
            )

        group_key = (item.workspace_key, item.type, item.path.parent)
        deployment_groups.setdefault(group_key, []).append(item)

    for (workspace_key, item_type, repository_directory), group_items in deployment_groups.items():
        item_names = ", ".join(item.name for item in group_items)
        print(f"[INFO] Deploying {item_type}: {item_names}")
        deploy_pbip_items(
            credential=credential,
            workspace_id=workspace_ids[workspace_key],
            environment=environment,
            repository_directory=repository_directory,
            item_types=[item_type],
        )


def rebind_reports(*, client: PowerBIRestClient, bindings_doc: Dict[str, Any], workspace_ids: Dict[str, str]) -> None:
    for binding in bindings_doc.get("bindings", []):
        client.rebind_report_by_name(
            report_workspace_id=workspace_ids[binding["report_workspace_key"]],
            report_name=binding["report_name"],
            semantic_model_workspace_id=workspace_ids[binding["semantic_model_workspace_key"]],
            semantic_model_name=binding["semantic_model_name"],
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy Power BI PBIP items from GitLab CI/CD.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--branch", default=os.environ.get("CI_COMMIT_BRANCH", "develop"))
    parser.add_argument("--rules", default="deployment/deployment-rules.yml")
    parser.add_argument("--manifest", default="deployment/powerbi-deploy.yml")
    parser.add_argument("--bindings", default="deployment/report-bindings.yml")
    parser.add_argument("--skip-deploy", action="store_true")
    parser.add_argument("--skip-rebind", action="store_true")
    parser.add_argument("--use-default-credential", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    rules = load_yaml(repo_root / args.rules)
    manifest = load_yaml(repo_root / args.manifest)
    bindings_doc = load_yaml(repo_root / args.bindings)

    environment = environment_from_branch(rules, args.branch)
    workspace_ids = workspace_map_for_environment(rules, environment)

    print(f"[INFO] Branch: {args.branch}")
    print(f"[INFO] Target environment: {environment}")
    print(f"[INFO] Workspace keys: {', '.join(workspace_ids.keys())}")

    credential = (
        PowerBIRestClient.default_credential()
        if args.use_default_credential
        else PowerBIRestClient.credential_from_environment()
    )

    if not args.skip_deploy:
        deploy_items(
            credential=credential,
            environment=environment,
            items=parse_deployment_items(manifest, repo_root),
            workspace_ids=workspace_ids,
        )

    if not args.skip_rebind:
        # Newly deployed items may take a short time to appear through list APIs.
        time.sleep(10)
        client = PowerBIRestClient(credential)
        rebind_reports(client=client, bindings_doc=bindings_doc, workspace_ids=workspace_ids)

    print("[SUCCESS] Deployment workflow completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
