# Microsoft Entra Service Principal Setup

Use a Microsoft Entra application registration for GitLab CI/CD authentication.

## Required high-level steps

1. Create an app registration in Microsoft Entra ID.
2. Create a client secret or configure certificate authentication.
3. Capture:
   - Tenant ID
   - Client ID
   - Client Secret
4. Enable service principal usage in the Power BI admin portal, if required by your tenant settings.
5. Add the service principal or security group to the target Power BI workspaces.
6. Grant the service principal sufficient workspace permissions to deploy/update content.

## Recommended workspace role

For deployment automation, the service principal typically needs sufficient workspace permissions to create and update items. Validate the exact role with your tenant governance team.

## GitLab CI/CD variables

Store these values as masked/protected GitLab CI/CD variables:

```text
AZURE_TENANT_ID
AZURE_CLIENT_ID
AZURE_CLIENT_SECRET
```

Do not commit these values to Git.
