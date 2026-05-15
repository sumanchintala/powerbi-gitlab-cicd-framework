#!/usr/bin/env python3
"""Validate deployment manifest, report bindings, and deployment rules."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List, Set

import yaml


def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def validate_manifest(manifest: Dict[str, Any], repo_root: Path) -> List[str]:
    errors: List[str] = []
    items = manifest.get("items", [])
    if not isinstance(items, list) or not items:
        errors.append("deployment manifest must contain a non-empty 'items' list.")
        return errors

    names: Set[str] = set()
    valid_types = {"SemanticModel", "Report"}

    for index, item in enumerate(items, start=1):
        for key in ["name", "type", "workspace_key", "path"]:
            if key not in item:
                errors.append(f"manifest item #{index} is missing required field '{key}'.")

        name = item.get("name")
        item_type = item.get("type")
        path = item.get("path")

        if name in names:
            errors.append(f"duplicate manifest item name: {name}")
        names.add(name)

        if item_type not in valid_types:
            errors.append(f"item '{name}' has invalid type '{item_type}'. Valid types: {sorted(valid_types)}")

        if path and not (repo_root / path).exists():
            errors.append(f"item '{name}' path does not exist: {path}")

    return errors


def validate_bindings(bindings_doc: Dict[str, Any], manifest: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    bindings = bindings_doc.get("bindings", [])
    manifest_items = {item.get("name"): item for item in manifest.get("items", [])}

    for index, binding in enumerate(bindings, start=1):
        for key in [
            "report_name",
            "report_workspace_key",
            "semantic_model_name",
            "semantic_model_workspace_key",
        ]:
            if key not in binding:
                errors.append(f"binding #{index} is missing required field '{key}'.")

        report_name = binding.get("report_name")
        semantic_model_name = binding.get("semantic_model_name")

        if report_name not in manifest_items:
            errors.append(f"binding references report not found in manifest: {report_name}")
        elif manifest_items[report_name].get("type") != "Report":
            errors.append(f"binding report_name is not a Report item in manifest: {report_name}")

        if semantic_model_name not in manifest_items:
            errors.append(f"binding references semantic model not found in manifest: {semantic_model_name}")
        elif manifest_items[semantic_model_name].get("type") != "SemanticModel":
            errors.append(
                f"binding semantic_model_name is not a SemanticModel item in manifest: {semantic_model_name}"
            )

    return errors


def validate_rules(rules: Dict[str, Any], manifest: Dict[str, Any], bindings_doc: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    branches = rules.get("branches", {})
    workspaces = rules.get("workspaces", {})

    if not branches:
        errors.append("deployment-rules.yml must contain branch mappings.")
    if not workspaces:
        errors.append("deployment-rules.yml must contain workspace mappings.")

    referenced_workspace_keys = {
        item.get("workspace_key") for item in manifest.get("items", []) if item.get("workspace_key")
    }
    for binding in bindings_doc.get("bindings", []):
        referenced_workspace_keys.add(binding.get("report_workspace_key"))
        referenced_workspace_keys.add(binding.get("semantic_model_workspace_key"))

    for branch, environment in branches.items():
        if environment not in workspaces:
            errors.append(f"branch '{branch}' maps to environment '{environment}', but no workspace mapping exists.")
            continue

        env_workspace_keys = set(workspaces.get(environment, {}).keys())
        missing = referenced_workspace_keys - env_workspace_keys
        if missing:
            errors.append(
                f"environment '{environment}' is missing workspace keys: {', '.join(sorted(missing))}"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Power BI deployment configuration.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--manifest", default="deployment/powerbi-deploy.yml")
    parser.add_argument("--bindings", default="deployment/report-bindings.yml")
    parser.add_argument("--rules", default="deployment/deployment-rules.yml")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    manifest = load_yaml(repo_root / args.manifest)
    bindings_doc = load_yaml(repo_root / args.bindings)
    rules = load_yaml(repo_root / args.rules)

    errors = []
    errors.extend(validate_manifest(manifest, repo_root))
    errors.extend(validate_bindings(bindings_doc, manifest))
    errors.extend(validate_rules(rules, manifest, bindings_doc))

    if errors:
        print("[FAILED] Deployment configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("[OK] Deployment configuration validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
