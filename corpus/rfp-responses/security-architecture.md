# Security Architecture

Responses drawn from the Meridian Health Network RFP (2025) and the Caldwell Municipal Utilities RFP (2026). Approved by Security Engineering.

## How is customer data encrypted at rest?

All customer data at rest is encrypted using AES-256 in GCM mode. This applies to primary databases, object storage, backups, and snapshots. Encryption is enabled by default on every tenant and cannot be disabled.

Key rotation occurs automatically every 90 days. Previous key versions are retained for the duration of the backup retention window so that historical restores remain possible.

## How is data encrypted in transit?

All external connections require TLS 1.3. TLS 1.2 is accepted only for named legacy integrations and must be requested in writing. Older protocol versions, including TLS 1.1 and SSLv3, are refused at the load balancer.

Internal service-to-service traffic within the Halebrook platform is encrypted with mutual TLS, with certificates issued by an internal certificate authority and rotated every 30 days.

## Can we manage our own encryption keys?

Customer-managed keys are available on the Enterprise tier. Halebrook supports AWS KMS and Azure Key Vault as external key providers. The customer retains the ability to revoke key access, which renders tenant data unreadable to Halebrook within 15 minutes.

Customer-managed keys are not available on the Standard or Professional tiers, which use Halebrook-managed keys with the rotation policy described above.

## How is the platform network segmented?

Each tenant's data plane runs in a logically isolated namespace with network policies that deny cross-tenant traffic by default. Control plane and data plane run in separate virtual networks connected only through an authenticated internal gateway.

Production environments are isolated from staging and development at the account level, not merely at the network level. No production data is copied into lower environments under any circumstances.

## How do you protect against insider access to customer data?

Halebrook staff have no standing access to customer data. Access requires a time-bound elevation request tied to an open support case, approved by a second engineer, and automatically expires after four hours.

Every elevation is logged with the requesting engineer, the approving engineer, the case reference, and the records accessed. Customers on the Enterprise tier receive these access logs through the audit API and can opt into real-time notification.
