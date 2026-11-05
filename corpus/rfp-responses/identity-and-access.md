# Identity and Access Management

Responses drawn from the Ardent Financial Group RFP (2025) and the Northgate Logistics RFP (2026). Approved by Platform Engineering.

## What single sign-on standards are supported?

Halebrook supports SAML 2.0 and OpenID Connect for single sign-on. Both are available on all paid tiers at no additional cost.

Tested and documented integrations exist for Okta, Microsoft Entra ID, Ping Identity, Google Workspace, and JumpCloud. Any identity provider conforming to SAML 2.0 or OIDC will work; the named providers simply have published setup guides.

## Is automated user provisioning supported?

Yes. Halebrook supports SCIM 2.0 for automated provisioning and deprovisioning. Group membership from the identity provider can be mapped to Halebrook roles, so access changes in the directory propagate without administrator action.

Deprovisioning through SCIM revokes active sessions within 60 seconds.

## Describe your role-based access control model.

Halebrook ships five predefined roles: Viewer, Analyst, Responder, Administrator, and Auditor. Custom roles can be defined on the Enterprise tier with permissions assigned at the resource-type level.

Permissions are additive and deny-by-default. A user with no role assignment has no access to any resource. Role assignments can be scoped to specific asset groups, so a regional team sees only the assets in its region.

## Is multi-factor authentication enforced?

When single sign-on is configured, multi-factor authentication is enforced by the customer's identity provider and Halebrook honors that assertion.

For customers not using single sign-on, Halebrook enforces time-based one-time password authentication on all administrator accounts. This cannot be disabled. MFA on non-administrator local accounts is configurable per tenant and enabled by default.

## How long are sessions valid?

Default session lifetime is 12 hours with a 30-minute idle timeout. Both values are configurable per tenant between 1 and 24 hours, and 5 and 120 minutes respectively.

Administrators can terminate any active session from the console, and termination takes effect immediately across all of that user's devices.

## Are service accounts and API keys supported?

Yes. API keys are scoped to a role and optionally to an asset group, and can be restricted to a list of source IP ranges. Keys carry a mandatory expiry of no more than 365 days.

Key usage is logged with timestamp, source address, and endpoint. Unused keys are flagged in the console after 90 days of inactivity.
