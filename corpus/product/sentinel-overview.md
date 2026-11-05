# Halebrook Sentinel

Network detection and response. Product overview maintained by Product Marketing, reviewed quarterly.

## What Sentinel does

Sentinel observes network traffic to identify malicious activity that endpoint tools miss: lateral movement, command and control beaconing, data staging, and activity originating from unmanaged or unmanageable devices.

It is deployed as passive sensors that receive a traffic mirror. Sentinel does not sit inline and cannot drop traffic on its own, which means a sensor failure cannot interrupt production traffic.

## Deployment footprint

A sensor is a virtual or physical appliance receiving a SPAN, TAP, or cloud traffic mirror. A single virtual sensor at 8 vCPU and 32 GiB handles sustained throughput of 5 Gbps. Physical appliances are available at 10, 40, and 100 Gbps.

Sensors are also available as cloud-native collectors for AWS VPC Traffic Mirroring, Azure Virtual Network TAP, and Google Packet Mirroring.

## Detection approach

Three layers operate together. Signature detection covers known indicators and is updated every four hours. Behavioral analytics model per-asset baselines over a 30-day rolling window and flag deviations. Protocol analysis identifies misuse of legitimate protocols, such as DNS tunneling or unusual SMB access patterns.

Detection content is authored by Halebrook's research team and mapped to MITRE ATT&CK technique identifiers. Customers can author custom detections in the Sentinel query language.

## Encrypted traffic

Sentinel analyzes encrypted traffic without decryption, using JA4 fingerprinting, certificate metadata, and flow characteristics. Decryption is optional and requires the customer to provide keys or deploy a decryption appliance upstream.

Detection coverage on encrypted traffic without decryption is meaningfully narrower. Halebrook publishes which detection categories require visibility into payload.

## Response actions

Sentinel can trigger containment through integrated endpoint and network tools: isolating a host through CrowdStrike or Defender, or applying a block through supported firewall and NAC platforms.

All response actions are off by default and require explicit per-action enablement. Automated response can be restricted to specific asset groups and specific detection categories.

## Scale

The largest production Sentinel deployment monitors approximately 180,000 assets across 40 sites. Event ingest in that environment averages 1.2 million events per second at peak.
