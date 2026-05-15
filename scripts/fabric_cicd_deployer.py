#!/usr/bin/env python3
"""
Deployment helper for Microsoft fabric-cicd.

This wrapper keeps the rest of the deployment code independent from the exact
fabric-cicd object construction. It expects each repository directory to contain
one or more PBIP item folders, such as:

- Sales Analytics.SemanticModel
- Sales Performance.Report
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from azure.identity import TokenCredential


def deploy_pbip_items(
    *,
    credential: TokenCredential,
    workspace_id: str,
    environment: str,
    repository_directory: Path,
    item_types: List[str],
) -> None:
    """Deploys PBIP items to a Fabric / Power BI workspace using fabric-cicd."""
    try:
        from fabric_cicd import FabricWorkspace, publish_all_items
    except ImportError as exc:
        raise ImportError("fabric-cicd is not installed. Run: pip install fabric-cicd") from exc

    if not repository_directory.exists():
        raise FileNotFoundError(f"Repository directory does not exist: {repository_directory}")

    print(
        f"[INFO] fabric-cicd deployment: workspace={workspace_id}, "
        f"environment={environment}, directory={repository_directory}, "
        f"item_types={item_types}"
    )

    target_workspace = FabricWorkspace(
        workspace_id=workspace_id,
        environment=environment.lower(),
        repository_directory=str(repository_directory),
        item_type_in_scope=item_types,
        token_credential=credential,
    )

    publish_all_items(target_workspace)
    print("[OK] fabric-cicd deployment completed.")
