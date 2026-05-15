# Report Rebind

Thin reports commonly connect to shared semantic models. When reports and semantic models are promoted across DEV, SIT, and PRD, the report must point to the semantic model in the same target environment.

## Example

```text
DEV report → DEV semantic model
SIT report → SIT semantic model
PRD report → PRD semantic model
```

## How this framework handles it

The file `deployment/report-bindings.yml` defines which report should bind to which semantic model:

```yaml
bindings:
  - report_name: Sales Performance
    report_workspace_key: sales_spoke
    semantic_model_name: Sales Analytics
    semantic_model_workspace_key: analytics_hub
```

The script `scripts/rebind_reports.py` then:

1. Resolves the target environment from the branch.
2. Reads workspace IDs from environment variables.
3. Finds the report by name in the report workspace.
4. Finds the semantic model by name in the semantic model workspace.
5. Calls the Power BI REST API Rebind endpoint.

## Important

Use unique report names and semantic model names inside each workspace. Duplicate names make automated deployment and rebind logic harder to control.
