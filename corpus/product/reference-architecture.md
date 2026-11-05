# Reference Architecture

Maintained by Solutions Architecture. Current as of release 7.4.

## Platform layers

The platform separates into four layers: collection, ingest, analysis, and presentation.

Collection comprises Sentinel sensors, Atlas discovery, Gate connectors, and external data ingestion. Collection components run in the customer environment in every deployment model.

Ingest normalizes, enriches, and routes events. Analysis applies detection content, behavioral models, and risk scoring. Presentation covers the console, the API, and outbound integrations.

## Data flow

Sensors process traffic locally and forward metadata, not full packet capture, to the ingest layer. A typical sensor forwards between 1 and 3 percent of observed traffic volume as metadata.

Full packet capture is available as an optional sensor-local rolling buffer, retained on the sensor and never forwarded. Buffer depth depends on sensor storage, typically 4 to 72 hours.

## Network requirements

Sensors require outbound HTTPS on 443 to the regional ingest endpoint. No inbound connections to sensors are required.

Where egress is restricted, sensors can forward through an HTTP proxy with authentication, or to a customer-operated aggregator that holds the single permitted egress path.

Bandwidth from site to ingest should be provisioned at approximately 2 percent of monitored throughput, with a floor of 10 Mbps per site.

## Multi-region deployments

A customer operating in several geographies can deploy sensors in each and forward to a single home region, or can operate separate tenants per region where data residency rules prohibit consolidation.

Cross-tenant reporting for separate regional tenants is available through the API and is the customer's responsibility to assemble. Halebrook does not aggregate across tenants.

## High availability at the collection layer

Sensors can be deployed in pairs receiving the same traffic mirror, with deduplication at ingest. Loss of one sensor in a pair causes no gap.

Where a pair is not deployed, loss of a sensor creates a visibility gap for the duration of the outage. Sensors buffer locally for up to four hours when ingest is unreachable, so an ingest-side or network interruption shorter than that results in no data loss.
