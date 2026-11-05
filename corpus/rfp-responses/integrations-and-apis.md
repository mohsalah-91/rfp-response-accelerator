# Integrations and APIs

Responses drawn from the Ardent Financial Group RFP (2025) and the Northgate Logistics RFP (2026). Approved by Platform Engineering.

## Do you provide a public API?

Yes. Halebrook exposes a REST API covering every function available in the console, documented with an OpenAPI 3.1 specification published at docs.halebrook.example.

The API is versioned in the path. A version is supported for a minimum of 24 months after the release of its successor, and deprecation notices are issued at least 12 months in advance.

## What are the API rate limits?

The default limit is 600 requests per minute per tenant, with a burst allowance of 1,200. Bulk export endpoints have a separate limit of 20 requests per minute.

Limits can be raised on the Enterprise tier by agreement. Responses include rate limit headers so clients can back off before being throttled.

## Are webhooks supported?

Yes. Webhooks can be configured for detection events, asset state changes, policy violations, and administrative actions. Payloads are signed with HMAC-SHA256 using a per-endpoint secret.

Delivery is retried with exponential backoff for up to 24 hours. Undelivered events remain available through the API for the tenant's retention period.

## Which SIEM platforms do you integrate with?

Certified integrations exist for Splunk Enterprise and Splunk Cloud, Microsoft Sentinel, Elastic Security, Sumo Logic, and Google SecOps. Each ships as a vendor-published app or content pack.

For platforms without a certified integration, Halebrook can forward events in CEF or JSON over syslog, or to an S3 bucket the customer controls.

## What ITSM and collaboration integrations are available?

ServiceNow and Jira Service Management are supported with bidirectional sync: Halebrook creates tickets on detection, and ticket closure updates the Halebrook case.

PagerDuty and Opsgenie are supported for alerting. Slack and Microsoft Teams are supported for notification and for a limited set of response actions approved by the customer.

## Do you integrate with endpoint detection tools?

Halebrook Atlas ingests asset inventory from CrowdStrike Falcon, SentinelOne, and Microsoft Defender for Endpoint, which improves discovery coverage for managed endpoints.

Halebrook Sentinel can trigger containment actions through CrowdStrike and Defender where the customer has enabled that permission.

## Can data be exported in bulk?

Yes. Scheduled exports to a customer-controlled S3 or Azure Blob destination are available in Parquet, JSON, or CSV, on an hourly or daily cadence. There is no charge for export and no egress fee.
