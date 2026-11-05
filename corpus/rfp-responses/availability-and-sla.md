# Availability, Resilience and Service Levels

Responses drawn from the Caldwell Municipal Utilities RFP (2026) and the Ardent Financial Group RFP (2025). Approved by Site Reliability Engineering.

## What uptime do you commit to?

The Standard and Professional tiers carry a 99.9% monthly uptime commitment. The Enterprise tier carries 99.95%.

Uptime is measured as the percentage of one-minute intervals in a calendar month during which the API and console are reachable and returning successful responses. Scheduled maintenance is excluded, and scheduled maintenance has not exceeded two hours per quarter in the last eight quarters.

## What service credits apply if you miss the commitment?

Credits are applied against the following month's fees: 10% for availability below the commitment but at or above 99.0%, 25% below 99.0%, and 50% below 95.0%.

Credits are the sole remedy for availability shortfalls. A customer must request credits within 30 days of the affected month.

## Describe your disaster recovery posture.

Each region operates across three availability zones with synchronous replication of primary data stores. Loss of a single zone is handled automatically with no customer action and no data loss.

For regional loss, the recovery point objective is 15 minutes and the recovery time objective is 4 hours. Cross-region failover is a manual, declared process.

Disaster recovery is tested twice a year with a full regional failover exercise. The most recent test report summary is available under NDA.

## How are backups taken and verified?

Full backups are taken daily and incremental backups every 15 minutes. Backups are encrypted with the same key hierarchy as primary data and stored in a separate account within the home region.

Restore is tested weekly against a randomly selected tenant snapshot in an isolated environment. Restore verification results are retained for 12 months.

## What is your change management process?

Production changes require a reviewed pull request, automated test suite passage, and deployment through a staged rollout that begins at 1% of traffic. Rollback is automated and triggers on error-rate or latency regression.

Customer-visible changes are announced at least 10 business days in advance through the status page and the administrator notification channel. Emergency security patches are exempt from the notice period and are communicated within 24 hours of deployment.

## Do you provide a status page?

Yes, at status.halebrook.example, with component-level status, incident history, and subscription by email, webhook, or RSS. Incident post-mortems for Severity 1 events are published within five business days.
