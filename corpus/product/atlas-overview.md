# Halebrook Atlas

Asset inventory and discovery. Product overview maintained by Product Marketing, reviewed quarterly.

## What Atlas does

Atlas builds and maintains a continuously updated inventory of every device communicating on the network, including devices with no agent and devices that cannot accept one.

The common failure it addresses is that the configuration management database is incomplete and stale. Atlas discovers what is actually present rather than what was recorded.

## Discovery methods

Atlas discovers passively from network traffic observed by Sentinel sensors, which requires no scanning and no credentials. It supplements this with optional active discovery through authenticated and unauthenticated scanning.

It also ingests inventory from external sources: endpoint platforms, cloud provider APIs, virtualization platforms, directory services, and existing CMDBs.

## Device classification

Devices are classified by type, operating system, manufacturer, and role, using a fingerprint library covering more than 14,000 device profiles. Classification confidence is exposed on every record so analysts can see where the system is inferring rather than observing.

Unmanaged and operational technology devices, including building systems, medical devices, and industrial controllers, are classified using a dedicated profile library.

## Risk scoring

Each asset carries a composite risk score from exposure, known vulnerabilities, observed behavior, and business criticality assigned by the customer.

Scoring weights are configurable. Halebrook publishes the scoring model rather than treating it as proprietary, because customers consistently need to explain to auditors why a given asset is rated as it is.

## CMDB reconciliation

Atlas compares its inventory against the customer's CMDB and reports three categories: assets present in both, assets observed but absent from the CMDB, and assets recorded in the CMDB but never observed.

Reconciliation output can be written back to ServiceNow or exported for manual review. Automatic write-back is off by default.

## Scale and performance

A single Atlas deployment supports up to 250,000 assets. Discovery of a newly connected device typically completes within 90 seconds of its first observed network activity.
