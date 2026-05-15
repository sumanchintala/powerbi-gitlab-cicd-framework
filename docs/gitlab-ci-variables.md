# GitLab CI/CD Variables

Create variables under:

```text
GitLab Project → Settings → CI/CD → Variables
```

## Authentication variables

```text
AZURE_TENANT_ID
AZURE_CLIENT_ID
AZURE_CLIENT_SECRET
```

Mark secrets as **masked** and **protected** where appropriate.

## Workspace variables

```text
PBI_DEV_ANALYTICS_HUB_WORKSPACE_ID
PBI_DEV_SALES_SPOKE_WORKSPACE_ID
PBI_SIT_ANALYTICS_HUB_WORKSPACE_ID
PBI_SIT_SALES_SPOKE_WORKSPACE_ID
PBI_PRD_ANALYTICS_HUB_WORKSPACE_ID
PBI_PRD_SALES_SPOKE_WORKSPACE_ID
```

## Security guidance

- Do not hardcode workspace IDs in Python scripts.
- Do not hardcode client secrets.
- Protect production variables.
- Limit who can run production pipelines.
- Use protected branches for `main`.
