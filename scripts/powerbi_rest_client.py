#!/usr/bin/env python3
"""
Small Power BI REST API helper used by the GitLab CI/CD deployment scripts.

This module intentionally keeps the API surface small:
- authenticate with Microsoft Entra ID
- list reports in a workspace
- list semantic models / datasets in a workspace
- rebind a report to a semantic model

Environment variables expected for service principal authentication:
- AZURE_TENANT_ID
- AZURE_CLIENT_ID
- AZURE_CLIENT_SECRET
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import requests
from azure.identity import ClientSecretCredential, DefaultAzureCredential, TokenCredential

POWERBI_API_ROOT = "https://api.powerbi.com/v1.0/myorg"
POWERBI_SCOPE = "https://analysis.windows.net/powerbi/api/.default"


@dataclass(frozen=True)
class PowerBIItem:
    """Represents a Power BI item found by REST API."""

    id: str
    name: str
    raw: Dict[str, Any]


class PowerBIRestClient:
    """Thin wrapper around the Power BI REST API."""

    def __init__(self, credential: TokenCredential):
        token = credential.get_token(POWERBI_SCOPE).token
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )

    @staticmethod
    def credential_from_environment() -> TokenCredential:
        """Builds a service principal credential from environment variables."""
        required = {
            "AZURE_TENANT_ID": os.environ.get("AZURE_TENANT_ID"),
            "AZURE_CLIENT_ID": os.environ.get("AZURE_CLIENT_ID"),
            "AZURE_CLIENT_SECRET": os.environ.get("AZURE_CLIENT_SECRET"),
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise EnvironmentError(
                "Missing required service-principal environment variables: "
                + ", ".join(missing)
            )

        return ClientSecretCredential(
            tenant_id=required["AZURE_TENANT_ID"],
            client_id=required["AZURE_CLIENT_ID"],
            client_secret=required["AZURE_CLIENT_SECRET"],
        )

    @staticmethod
    def default_credential() -> TokenCredential:
        """Uses local developer authentication such as Azure CLI or VS Code login."""
        return DefaultAzureCredential(exclude_interactive_browser_credential=False)

    def _request_json(
        self,
        method: str,
        url: str,
        *,
        expected_status: Iterable[int] = (200,),
        **kwargs: Any,
    ) -> Dict[str, Any]:
        response = self.session.request(method, url, timeout=120, **kwargs)
        if response.status_code not in set(expected_status):
            raise RuntimeError(
                f"Power BI REST API call failed: {method} {url}\n"
                f"Status: {response.status_code}\n"
                f"Response: {response.text}"
            )
        if not response.text:
            return {}
        return response.json()

    def list_reports(self, workspace_id: str) -> List[PowerBIItem]:
        """Returns reports from a workspace."""
        url = f"{POWERBI_API_ROOT}/groups/{workspace_id}/reports"
        payload = self._request_json("GET", url)
        return [
            PowerBIItem(id=item["id"], name=item.get("name", ""), raw=item)
            for item in payload.get("value", [])
        ]

    def list_semantic_models(self, workspace_id: str) -> List[PowerBIItem]:
        """
        Returns semantic models from a workspace.

        The Power BI REST API still exposes semantic models through the datasets endpoint.
        """
        url = f"{POWERBI_API_ROOT}/groups/{workspace_id}/datasets"
        payload = self._request_json("GET", url)
        return [
            PowerBIItem(id=item["id"], name=item.get("name", ""), raw=item)
            for item in payload.get("value", [])
        ]

    @staticmethod
    def find_unique_by_name(items: List[PowerBIItem], name: str, item_kind: str) -> PowerBIItem:
        matches = [item for item in items if item.name == name]
        if not matches:
            available = ", ".join(sorted(item.name for item in items))
            raise LookupError(f"{item_kind} named '{name}' was not found. Available: {available}")
        if len(matches) > 1:
            raise LookupError(f"Multiple {item_kind}s named '{name}' were found. Use unique names.")
        return matches[0]

    def rebind_report(
        self,
        *,
        report_workspace_id: str,
        report_id: str,
        semantic_model_id: str,
    ) -> None:
        """
        Rebinds one report to one semantic model/dataset.

        REST endpoint:
        POST /groups/{workspaceId}/reports/{reportId}/Rebind
        Body: {"datasetId": "<semantic-model-id>"}
        """
        url = f"{POWERBI_API_ROOT}/groups/{report_workspace_id}/reports/{report_id}/Rebind"
        self._request_json(
            "POST",
            url,
            expected_status=(200,),
            json={"datasetId": semantic_model_id},
        )

    def rebind_report_by_name(
        self,
        *,
        report_workspace_id: str,
        report_name: str,
        semantic_model_workspace_id: str,
        semantic_model_name: str,
    ) -> None:
        """Finds the report and semantic model by name, then rebinds the report."""
        report = self.find_unique_by_name(
            self.list_reports(report_workspace_id),
            report_name,
            "report",
        )
        semantic_model = self.find_unique_by_name(
            self.list_semantic_models(semantic_model_workspace_id),
            semantic_model_name,
            "semantic model",
        )
        self.rebind_report(
            report_workspace_id=report_workspace_id,
            report_id=report.id,
            semantic_model_id=semantic_model.id,
        )
        print(
            f"[OK] Rebound report '{report_name}' "
            f"to semantic model '{semantic_model_name}'."
        )
