# Halebrook Gate

Zero trust network access. Product overview maintained by Product Marketing, reviewed quarterly.

## What Gate does

Gate replaces network-level remote access with per-application access brokered on identity and device posture. A user authenticates once and reaches only the applications policy permits, with no route to anything else.

It is most often deployed to retire a legacy VPN concentrator, or to give third-party contractors scoped access without issuing network credentials.

## Architecture

Gate has three components. The client runs on the user's device. The connector is a lightweight process deployed adjacent to each protected application, which makes only outbound connections. The broker is a Halebrook-operated service that authenticates and authorizes sessions.

Because connectors dial out, no inbound firewall rules are required and protected applications need no public exposure.

## Policy model

Policy is expressed as identity plus device posture plus application. A policy might permit members of a directory group to reach a named internal application, only from a device with disk encryption enabled and an endpoint agent reporting healthy, only during defined hours.

Policy is evaluated on every connection, not only at session establishment. A device that falls out of posture loses access within 60 seconds.

## Device posture signals

Gate collects posture directly from the client and ingests additional signals from CrowdStrike, SentinelOne, Microsoft Intune, and Jamf. Supported checks include disk encryption, OS version and patch level, endpoint agent presence and health, screen lock configuration, and certificate presence.

## Supported platforms

Clients are available for Windows 10 and 11, macOS 13 and later, Ubuntu and RHEL, iOS 16 and later, and Android 12 and later.

Browser-based access without a client is available for web applications and for contractors on unmanaged devices.

## Deployment model

Gate is available as SaaS and as private cloud. Self-managed deployment of the Gate broker is not currently available; the broker is operated by Halebrook in all configurations. Connectors always run in the customer's environment.
