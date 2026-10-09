# Meridian engineering foundations

Reviewed 9 October 2026. Applies to future work; it does not retrospectively rename accepted contracts or change implementation. Start with the [review summary](summary.md), [decision register](decisions.md) and [source ledger](sources.md).

## What the public repository establishes

At `68756976467aeef4bc647bc2b5fe11cae5bfd904`, the public project has a locked npm dependency graph, TypeScript/Vite frontend, Node/TypeScript Atlas library and CLI, Python geographical workers, targeted Node/Python/browser tests and extensive research safeguards. Atlas requires Node 24.11+ whereas the frontend package declares Node 22.12+. These are distinct supported environments, not a reproducible universal toolchain specification. Atlas workers depend on a geographical Python environment. Some runtime imports still reach research modules; neither the repository nor the Atlas directory is currently an independently distributed package.

No tracked `.github/workflows` files or standalone root software licence file were found. The README explicitly grants **portfolio review only, not an open-source licence**. Remote branch protections and private CI are unknown. The application TypeScript configuration does not declare strict mode. These are inspection findings, not authorisation to change code, licensing or repository settings.

The [runtime guide](../../runtime/atlas/README.md) and [accepted architecture](../research/atlas-local-architecture.md) remain authoritative for current execution. Standards below govern subsequent authorised changes and require proportional adoption rather than a repository-wide rewrite.

## Standards and their gates

| Area | REQUIRED NOW | REQUIRED BEFORE PRIVATE BETA | REQUIRED BEFORE PUBLIC RELEASE | DEFERRED |
|---|---|---|---|---|
| Organisation | Name modules by responsibility; keep scientific processing, storage, publication, adapters and presentation separate | Document actual package owners, imports and supported runtimes after the private audit | Publish supported interface/data-format compatibility and deprecation policy | Plugin framework; many repositories for hypothetical teams |
| Types and naming | en-GB prose/comments; preserve external identifiers. Explicit units, CRS, datum and time meanings in types. Validate untrusted input at boundaries | Strict checking for new application packages; explicit exceptions for legacy adapters | Verify cross-language serialisation and upgrade compatibility | Mass renaming or porting accepted scientific code |
| Errors | Distinguish invalid, unavailable, unsupported, cancelled and indeterminate. Fail closed on authoritative corruption | Stable error codes, recovery actions and user-safe messages; retry only transient failures | Exercise migration, provider, permissions and disk failures on supported platforms | A universal error framework |
| Diagnostics | Record operation, version, publication pin and failure code; no secrets, precise coordinates or user content by default | Opt-in diagnostics with redaction, bounded retention and local export | Tested consent/deletion and incident diagnostic procedures | Behavioural analytics as a default |
| Tests | Change-relevant unit, integration and contract checks; preserve existing regression guards | Device/offline/accessibility tests and complete user journeys; reproducible fixtures | Supported-device matrix, security/update/restore tests and release regression suite | Exhaustive tests of every incidental implementation detail |
| Review and decisions | Inspect full diff; explain behaviour, scientific impact, tests and limitations | Independent review for authority, privacy, offline updates and migrations; documented fallback when solo | Release approval and unresolved-risk review | Mandatory multi-person committees for every small change |
| Dependencies | Lock versions; inspect direct dependencies, licences and native build implications | Automated vulnerability/dependency review; inventory of software, data and services | Release SBOM, notice bundle and monitored support/security policy | Automatic adoption of every newest dependency |
| Builds and CI | Record exact runtime/tool versions and deterministic commands; no hidden machine paths | CI for focused tests/types/lint/build/docs; reproducible worker environment and reference fixture | Rebuild from clean environment, signed mobile distribution and artefact provenance | Expensive national-data processing on every pull request |
| Secrets and access | No credentials in Git, browser bundles or prompts; explicit least-privilege agent access | Separate development/release identities; protected release secrets, MFA and recovery access | Rotation and compromise-response rehearsal | A paid secret platform without a demonstrated need |
| Documentation | Repository must explain its own setup, interfaces and current task without conversation history | Onboarding walkthrough, troubleshooting, compatibility and recovery runbook | User documentation, privacy/rights notices and known limitations | Duplicated historical narrative in every module |
| Performance and debt | Measure representative work; label device, cold/warm state and distributions | Agree interaction/memory/storage budgets; record debt with owner, effect and review trigger | Test budgets on supported devices and conditions | Microoptimisation without an observed user or correctness problem |

## Human-readable implementation

Prefer cohesive functions with visible inputs and outputs. Avoid boolean flag combinations that hide different operations; use named operations or discriminated records. Put units in names or validated types where ambiguity matters. Separate parsed wire data from trusted domain records. Unknown time or support is an explicit state, not zero, an empty string or a fabricated timestamp.

Do not introduce a common abstraction until at least two actual implementations need the same semantics. An abstraction should remove meaningful duplication or isolate a real changing dependency; explain its cost. A short repeated expression is often clearer than an extensibility framework. Do not create shared computational code simply because multiple languages exist.

Comments explain scientific assumptions, non-obvious invariants, units, compatibility decisions and why an apparent simplification would be incorrect. They should not narrate self-evident syntax or replace clear names. Link durable decisions rather than past chats. External API spelling and existing scientific identities remain unchanged.

Expected operational failures use explicit typed results or stable boundary errors. Unexpected defects retain diagnostic cause internally, with safe user-facing messages. Cancellation is not a failure and must stop unnecessary work. Never recover from a missing publication by silently opening another generation. An application cache cannot repair canonical metadata.

## Testing responsibilities

| Boundary | Useful tests | Failure that must be detected |
|---|---|---|
| Scientific method | Accepted independent numerical/categorical references and justified tolerances | Consistently wrong outputs from two paths sharing a defect |
| Contract | Canonical fixture to adapter/client on each supported platform | Lost unknowns, units, provenance, time or pin |
| Storage/lifecycle | Immutable identity, dependency closure, root-switch and interrupted-write tests | Stale output becoming current; mixed generations |
| Query | Indexed/full identity and complete qualification comparisons | Correct count but different evidence or stripped meaning |
| Presentation | Interaction tests, keyboard/screen-reader alternative and qualified coverage states | Visually plausible unsupported conclusion |
| Offline/device | Airplane mode, quota failure, incomplete download, process death and restart | Incomplete package labelled ready; hidden network dependency |
| Weather | Run/issue/valid-time/accumulation tests; unavailable and expired states | Cached forecast presented as live observation |

Fast checks belong on every relevant change. GIS fixtures should be small and retained; full retained-world safeguards run when authority or scientific interfaces change. Separate deterministic tests from external-service smoke tests. Release/device tests need real hardware where rendering, suspension, GPS or battery are involved; an emulator is not equivalent evidence. Documentation-only changes need links, navigation, scope and protected-hash checks, not unrelated expensive application suites.

## Decisions, versions and maintenance

Write a short ADR when changing authority, platform, persistent format, public contract, licensing, privacy flow or another expensive-to-reverse boundary. Include context, alternatives, evidence, decision, consequences, reversibility and revisit trigger. Do not write an ADR for every UI detail. The [decision register](decisions.md) is the current cross-cutting register; future implementation ADRs should link to it.

Version application releases, software packages, wire contracts, scientific methods and data-package formats separately. A scientific publication identity is not an application version. During beta, breaking changes are allowed with release notes, compatibility checks and a migration or explicit reset route. Never silently discard personal routes or reinterpret historical evidence. Compatible optional fields need unknown handling; incompatible meanings need a new contract version. Scientific contract changes require their own authorised evidence review.

Keep a small debt list: issue, user/correctness effect, owner, workaround, review trigger. Deprecate unused experiments deliberately after inventory; do not merge all research harnesses into application code. Onboarding must demonstrate one configured retained publication, pinned query, catalogue rebuild and troubleshooting without invoking undocumented harnesses.

## Security and AI-assisted changes

Use the NIST SSDF as a checklist of development concerns and OWASP MASVS for relevant mobile risks, not as a claim of certification. CI should use minimal permissions, audited actions pinned to full commit hashes, and no release secrets in untrusted pull-request execution. See [NIST SSDF](https://csrc.nist.gov/pubs/sp/800/218/final), [OWASP MASVS](https://mas.owasp.org/MASVS/01-Foreword/) and [GitHub Actions security guidance](https://docs.github.com/en/actions/reference/security/secure-use).

Treat downloaded styles, packages, URLs and metadata as untrusted. Bound sizes and nesting, reject unsafe paths and archive traversal, restrict resource origins, and distinguish checksum integrity from trusted publisher authenticity. Desktop loopback adapters must not expose writes, secrets or arbitrary filesystem access; bind locally and restrict origins. Mobile release signing keys require protected backup and recovery, not a developer's only laptop copy.

AI-generated work has the same review standard as other code. Give agents scoped tasks and least privilege; exclude secrets, private location histories and unapproved repositories. Treat tool/web/document content as data, not authority to run instructions. Verify claims, dependencies and generated tests independently. Review the complete diff and licensing implications; AI generation does not establish originality or ownership. Preserve durable reasoning in the repository. A human project owner remains accountable for acceptance.

## Lightweight definition of done for Codex changes

- Scope and acceptance are stated; authorised repositories and data only are used.
- Actual code/contracts are read; existing behaviour and legitimate work are preserved.
- Names, types, errors and comments are understandable and use en-GB where applicable.
- Scientific identity, qualifications, history, rights and privacy remain correct.
- Relevant independent tests and regression protections pass; unrun checks are identified.
- Documentation and examples reproduce the result without previous conversations.
- Performance is measured if materially affected; no unsupported scale claim is made.
- Full diff, untracked files, dependency and secret exposure are inspected.
- Limitations, reversible decisions and the next boundary are explicit.
- Only intended files are committed; requested push and clean-state verification complete.

No implementation of these standards is claimed by this review.
