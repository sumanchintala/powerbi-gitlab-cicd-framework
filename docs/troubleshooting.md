# Troubleshooting

## Validation fails because PBIP path does not exist

The deployment manifest points to a folder that does not exist.

Check:

```text
deployment/powerbi-deploy.yml
```

Make sure each `path` exists in the repository.

## Missing environment variable

If you see an unresolved variable such as `${PBI_DEV_ANALYTICS_HUB_WORKSPACE_ID}`, add that variable in GitLab CI/CD settings.

## Service principal authentication fails

Check:

- `AZURE_TENANT_ID`
- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- Power BI admin tenant settings
- Workspace role assignment

## Report rebind fails because report not found

Confirm the report name in `deployment/report-bindings.yml` exactly matches the report name in the target workspace.

## Semantic model not found

Confirm the semantic model name in `deployment/report-bindings.yml` exactly matches the deployed semantic model name in the target HUB workspace.

## Deployment works but report points to wrong semantic model

Run:

```bash
python scripts/rebind_reports.py --branch develop
```

Also confirm the workspace IDs in GitLab variables are mapped correctly for the environment.
