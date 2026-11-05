# Data Residency and Privacy

Responses drawn from the Lindhaus Group RFP (2025, Germany) and the Pemberton Trust RFP (2026, UK). Approved by Legal and Privacy.

## In which regions can our data be stored?

Halebrook operates in six regions: US East (Virginia), US West (Oregon), EU Central (Frankfurt), EU West (Dublin), APAC Southeast (Singapore), and APAC South (Sydney).

The customer selects a home region at provisioning. All customer data, including backups and telemetry, remains within that region. Region cannot be changed after provisioning without a migration engagement.

## Does any customer data leave the selected region?

Customer content does not leave the home region. Three categories of operational metadata are processed in US East regardless of home region: aggregate usage counters for billing, platform health metrics, and support case metadata.

None of these contain customer content, asset names, network addresses, or user identities. A full schema of what is replicated is available under NDA.

## Are you GDPR compliant?

Halebrook acts as a data processor under GDPR. A Data Processing Addendum incorporating the 2021 Standard Contractual Clauses is available and is signed as part of the master agreement.

Halebrook has appointed a Data Protection Officer who can be reached at dpo@halebrook.example. Records of processing activities are maintained under Article 30 and are available to customers on request.

## How do you handle data subject access requests?

Customers can export all data associated with an identified user through the console or the audit API, in JSON or CSV. Deletion of a data subject's records is available through the same interfaces.

Where Halebrook receives a request directly from a data subject, it is forwarded to the customer within two business days. Halebrook does not respond to such requests on the customer's behalf.

## What is your data retention policy?

Event data is retained for 90 days on Standard, 180 days on Professional, and 400 days on Enterprise. Configuration and audit records are retained for the life of the contract plus 90 days.

On termination, all customer data is deleted within 30 days. Backups containing customer data age out within a further 35 days. A certificate of deletion is issued on request.

## Do you comply with CCPA?

Yes. Halebrook acts as a service provider under CCPA and does not sell or share personal information. The same export and deletion interfaces described above serve CCPA requests.
