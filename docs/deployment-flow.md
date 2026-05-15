# Deployment Flow

## Branch strategy

| Branch | Environment | Action |
|---|---|---|
| `feature/*` | None | Validate only |
| `develop` | DEV | Deploy to DEV workspaces |
| `sit` | SIT | Deploy to SIT workspaces |
| `main` | PRD | Deploy to PRD workspaces |

## Sequence

1. Developer saves Power BI content as PBIP.
2. Developer commits PBIP changes to a feature branch.
3. Merge request validates manifest and folder structure.
4. Merge to `develop` deploys to DEV.
5. Merge to `sit` deploys to SIT.
6. Merge to `main` deploys to PRD after manual approval.

## Deployment order

1. Semantic models
2. Reports
3. Report rebind
4. Optional post-deployment validation
