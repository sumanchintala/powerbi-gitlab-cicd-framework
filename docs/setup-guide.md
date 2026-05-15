# Setup Guide

## 1. Create Power BI workspaces

Create one HUB workspace and one or more SPOKE workspaces per environment.

Example:

```text
PBI-DEV-ANALYTICS-HUB
PBI-DEV-SALES-SPOKE
PBI-SIT-ANALYTICS-HUB
PBI-SIT-SALES-SPOKE
PBI-PRD-ANALYTICS-HUB
PBI-PRD-SALES-SPOKE
```

## 2. Create or export PBIP content

Use Power BI Desktop to save reports and semantic models as PBIP projects. Commit only public-safe example content to this repository.

## 3. Configure Microsoft Entra service principal

See `docs/service-principal-setup.md`.

## 4. Add GitLab CI/CD variables

See `docs/gitlab-ci-variables.md`.

## 5. Update deployment files

Update these files:

```text
deployment/powerbi-deploy.yml
deployment/report-bindings.yml
deployment/deployment-rules.yml
```

## 6. Validate locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/validate_deployment_manifest.py
```

## 7. Commit and push

```bash
git add .
git commit -m "Add Power BI GitLab CI/CD framework"
git push origin main
```

## 8. Create GitLab project or mirror repository

This repository is hosted on GitHub as a public reference. For real GitLab CI/CD execution, copy or mirror it into GitLab.
