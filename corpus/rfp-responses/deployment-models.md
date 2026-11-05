# Deployment Models

Responses drawn from the Lindhaus Group RFP (2025) and the Caldwell Municipal Utilities RFP (2026). Approved by Solutions Architecture.

## What deployment models do you offer?

Three models. Multi-tenant SaaS is the default and accounts for the majority of deployments. Private cloud is a single-tenant deployment in a dedicated account within a Halebrook-operated region. Self-managed is a customer-operated deployment in the customer's own cloud account.

All three run the same product build. Feature parity is maintained within one release of each other.

## What is the difference between private cloud and self-managed?

In private cloud, Halebrook operates the infrastructure in a dedicated account and retains responsibility for patching, upgrades, and availability. The SLA applies unchanged.

In self-managed, the customer operates the infrastructure. Halebrook provides the container images, Helm charts, and reference Terraform. The availability SLA does not apply, since Halebrook does not control the environment. Support covers the software, not the customer's infrastructure.

## Which clouds are supported for self-managed deployment?

AWS and Azure are supported and documented. Google Cloud is supported on a best-effort basis; reference Terraform is not published for GCP and deployment requires a professional services engagement.

## What are the minimum infrastructure requirements for self-managed?

A Kubernetes cluster at version 1.29 or later with at least three worker nodes of 8 vCPU and 32 GiB each, a PostgreSQL 15 or later instance with 500 GiB of storage, and an S3-compatible object store with 2 TiB of capacity.

These figures size a deployment monitoring up to 10,000 assets. Sizing guidance for larger estates is provided during the architecture review.

## Can the platform run without internet connectivity?

Self-managed deployments of Sentinel and Atlas can run with outbound connectivity restricted to a Halebrook update endpoint and a license validation endpoint, both of which can be proxied. Threat intelligence feeds require periodic outbound access; customers can substitute an internally hosted feed mirror.

Fully air-gapped operation, with no outbound connectivity at all, is supported for Sentinel and Atlas through an offline update bundle delivered quarterly.

## How are upgrades handled?

SaaS and private cloud are upgraded by Halebrook. SaaS follows a continuous release cadence; private cloud customers choose a monthly maintenance window.

Self-managed customers control their own upgrade schedule. Halebrook supports the current release and the two preceding minor releases. Running more than three releases behind places a deployment outside support.
