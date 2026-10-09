# Meridian operational economics and public-exposure gate

Amendment reviewed 9 October 2026; starting checkpoint `6c83603d72c33bdac2d1c7d3302c0cc47ab76ad8`. Decision **F32** establishes this gate; it does not approve expenditure or assert that controls already exist. See the [maturity roadmap](roadmap.md) and [decision register](decisions.md).

## When the gate applies

Local-first development remains preferred. A local prototype needs no hosting procurement. Before **unrestricted public access**, including an openly accessible beta or prototype endpoint, the project owner must accept a documented operating plan, **user-approved operating budget and exposure ceiling**. A beta label does not exempt a service from this gate. Any earlier paid, remotely accessible trial also needs explicitly approved, bounded costs and access appropriate to that trial; it need not adopt a public-scale architecture.

No prices, traffic forecasts, numerical budgets or provider are selected here. All estimates and approvals remain outstanding until a concrete delivery requirement exists. Passing technical or scientific readiness checks does not pass this financial gate.

## Required evidence before opening public access

A short versioned operating plan and one costing worksheet are sufficient. The project owner records approval, supported scope, review date and limits; specialist review is needed only where an actual requirement warrants it.

- Document the **delivery architecture and service dependency inventory**: hosting, domains, object storage/CDN, processing, databases, maps, imagery, weather, external APIs, logs, backups and distribution channels. Record owners, rights, billable units, request paths and dependencies that remain chargeable when the application stops.
- Separate **fixed costs**, **variable costs**, one-off setup and provisioned commitments. Include currency, tax treatment, billing period, region, dated tariff/terms evidence and exclusions. A free allowance, promotional credit or assumed cache hit is not a permanent zero-cost guarantee.
- Model **ordinary**, **high-demand** and **adverse/abusive usage**. State assumed users, sessions, map movement, package sizes, repeated downloads, cache misses, concurrent requests, failed/retried operations and refresh cadence. These are scenarios, not forecasts; identify unknowns instead of manufacturing volumes.
- Estimate **cost per user** and **cost per completed download** where measurable, alongside marginal and allocated costs. Include retries and distribution overhead; state the denominator and period. Report unmeasured costs as unknown, not zero. Perform sensitivity analysis on the dominant variables and plausible combinations of failures.
- Obtain explicit approval of the operating budget, exposure ceiling, acceptable residual liability and escalation point. A budget is an estimate/authorisation; an exposure ceiling is a control objective. Do not call either an enforceable hard cap without evidence that every chargeable path is bounded.
- Specify and test proportionate **quotas, rate limits, request validation and abuse controls**. Bound query area/complexity, downloads, retries, concurrent work and expensive transformations. Controls must cover origin access and APIs as well as the application/CDN; changing clients or exhausting a cache must not bypass them. Do not add accounts or persistent location tracking merely to meter usage.
- Assess **provider-side spending safeguards where available**: exact service/account coverage, delay, exemptions and failure behaviour. Add **application-level controls** when provider caps are insufficient. Measure the costs of controls themselves and spending that continues after suspension.
- Rehearse **safe degradation or suspension**, alerts, ownership, incident response and recovery. Name who can stop costly work, revoke access and restore service; define re-entry conditions and how users learn what is unavailable. Never replace missing weather with fabricated freshness or erase pinned evidence/history to reduce a bill.
- Show a credible route to **financially sustainable operation**: approved funding for free provision, transparent recovery of genuine costs, or income from new value Meridian creates. Include support/maintenance effort and reserve requirements. If no sustainable bounded route exists, retain controlled/local access rather than open-ended exposure.

## Cost drivers and worksheet

Use one consistent period and explicit units. Avoid double-counting a prepaid service in both fixed and per-request costs; distinguish cash commitments from allocated utilisation.

| Driver | Measure before estimating | Sensitivity / overlooked charges |
|---|---|---|
| Storage | Source, prepared, derived, rendering and package bytes; storage class and duration | Replication, minimum retention, retrieval charges and temporary copies |
| Egress and delivery | Delivered bytes, destination, cache misses, range requests and repeat downloads | Origin/CDN legs, failed transfers, abusive scraping and regional rates |
| Requests and external APIs | Tile, query, search, weather, imagery and metadata calls; retries | Provider limits, paid tiers, query fan-out and unauthorised direct access |
| Compute and preprocessing | Runtime/worker duration, memory, concurrency, update frequency | Startup/idle provision, failure loops and source-to-package rebuilds |
| Retained versions and backups | Generation/package growth, required retention, copies and restore reads | Compatible historical access, archive retrieval and disaster recovery |
| Logs and observability | Ingestion, retention, queries and alerts | High-cardinality/error storms, personal-data minimisation and monitoring charges |
| Fixed commitments | Hosting baseline, licences, domains, support and agreed minimums | Currency/tax changes, renewal, termination and unused capacity |

Worksheet identities: `period cost = fixed commitments + sum(measured billable quantity × applicable unit rate) + identified ancillary costs`; `allocated cost per active user = attributable period cost / active users`; `cost per completed download = attributable delivery cost / completed downloads`. Define allocation rules, zero-denominator behaviour and measurements; these are accounting aids, not pricing or demand predictions. Vary package size, retention, request frequency, cache effectiveness, egress region and retry rate individually and jointly. Record when an estimate cannot bound adverse exposure.

## Alerts are not universal spending caps

Checked against primary provider documentation on **9 October 2026**. AWS documents notification lag and charges continuing around budget alerts. Azure budgets do not themselves stop consumption. Google's alerts-only budgets do not automatically cap usage; its documentation also identifies spend-cap budgets for supported services. Verify the exact selected service and configuration before making any cap claim. [AWS budget limitations](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html), [Azure budgets](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/tutorial-acm-create-budgets), [Google budgets and supported spend caps](https://docs.cloud.google.com/billing/docs/how-to/budgets).

An alert threshold can be exceeded before a human or automation responds. Stopping new requests does not necessarily stop storage, backups, committed capacity or in-flight charges. Record residual spend and worst-case response latency supported by evidence. If a true ceiling cannot be enforced, explicitly disclose and obtain approval for residual risk, narrow exposure and keep a tested shutdown path. Do not imply that application throttling prevents every network/provider charge.

## Operational acceptance and review

Before opening access, retain the approved worksheet, control configuration/review, bounded abuse/failure test receipt, alert/contact test and suspension/recovery rehearsal. Use non-personal counters where possible. Check that capacity/budget controls fail safely without advertising unavailable capabilities; offline retained evidence must remain honestly dated and qualified. Restoration requires reconciled usage/bills, corrected cause, intact compatible data and owner approval.

Revisit F32 when audience, package volume, provider/terms, cadence, retention, capabilities or exposure changes materially. A public release must continue monitoring costs and dependencies; approval is not permanent permission for unlimited growth. No infrastructure, account, paid resource or endpoint is created by this amendment.

## Monetisation boundary

Do not charge merely for information, data or functionality Meridian can provide at no cost. Genuine costs of licensed data, paid services, computation and delivery may be recovered transparently. New value created by Meridian may support a sustainable business model; it does not override source rights, the free-at-no-cost principle or explicit opt-in privacy. Billing remains deferred under F29. A business proposition, price, subsidy or guaranteed revenue is not established here.
