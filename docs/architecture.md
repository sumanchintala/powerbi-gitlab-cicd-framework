# Architecture

This framework demonstrates a practical Power BI CI/CD architecture for organizations using GitLab.

## Design principles

1. GitLab is the source of truth.
2. Power BI workspaces are deployment targets.
3. PBIP files are used for source-control-friendly Power BI content.
4. Semantic models are deployed before reports.
5. Thin reports are rebound to the correct environment-specific semantic model after deployment.
6. Environment-specific values are managed through CI/CD variables, not hardcoded files.

## Components

| Component | Purpose |
|---|---|
| Power BI Desktop | Create and save PBIP project files |
| GitLab Repository | Version control for PBIP and deployment scripts |
| GitLab CI/CD | Validation, deployment, approval gates |
| Microsoft Entra ID | Service principal authentication |
| fabric-cicd | Deploy PBIP items to Power BI / Fabric workspaces |
| Power BI REST API | Discover reports/models and rebind reports |
| HUB workspace | Shared semantic models |
| SPOKE workspace | Thin reports connected to HUB semantic models |

## HUB/SPOKE pattern

Semantic models are deployed to HUB workspaces. Thin reports are deployed to SPOKE workspaces. After deployment, reports are rebound to the correct semantic model for the target environment.

```text
SIT SPOKE report → SIT HUB semantic model
PRD SPOKE report → PRD HUB semantic model
```
