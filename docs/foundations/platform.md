# Meridian platform and infrastructure options

Reviewed 9 October 2026. This is an evidence-based shortlist, not a framework selection. External facts and their limits are in the [source ledger](sources.md). Decisions and gates are in the [register](decisions.md).

## What needs to be portable

Share scientific semantics, stable identifiers, qualified data contracts and conformance fixtures first. Share computational implementations only where a measured need justifies it. Rendering, user interaction, files, permissions, downloads and positioning can have platform-specific implementations without creating different scientific meanings.

The accepted desktop Atlas authority uses Node/TypeScript, Python geographical workers, canonical files and a rebuildable SQLite catalogue. It cannot simply execute in a browser or mobile shell. Keep scientific preparation/publication on the supported local processing host initially. A later device package must be a faithful **read-only projection of an identified publication**, with declared coverage and capabilities, source qualifications and provenance. It is not permission for a mobile app to invent, repair or publish scientific evidence.

This future projection requires its own compatible export/reader boundary and conformance proof; it is not implemented or covered merely by the browser DTO proposal. Do not put Python/GDAL and the whole publication validation pipeline on a phone by default. Do not make a connection to a desktop Node server a prerequisite for all field use.

## Actual baseline and constraints

The public frontend is a React/TypeScript/Vite experimental application. `src/atlas/map/AtlasMap.ts` owns imperative MapLibre setup and a bundler-specific worker URL; `src/app/map/MeridianMap.tsx` composes it. Terrain, satellite selection and attribution are separate utilities. The current inspector samples rendered height and Weather fields rather than exposing the new qualified Atlas view. Public controls, workspaces and CSS are **reference only** for a new UI; controller lifetime, camera logic, cancellation and numeric utilities can be reviewed individually. The browser currently depends on external styles/tiles; an offline application must audit those URLs rather than assume a build bundles them.

Focused Node/UI/browser tests are useful references, but the present browser build and generated `dist` delivery assumptions do not establish mobile offline deployment. Tests of pure logic, map/resource fixtures and publication contracts can be adapted; experimental screen snapshots should not constrain the new product. Satellite imagery remains provider/rights-dependent and is not mandatory for the first terrain explorer. Unsupported loading, map errors, cache bounds and cancellation need explicit new interaction states rather than silent overlays disappearing.

| Evidence at the checkpoint | Consequence |
|---|---|
| 141 runtime records, 107 source and 34 derived; 34 retrieval relationships | Adequate semantic test population; not a national-scale workload |
| Latest full-open median 9.11 s; catalogue build 838 ms; 220 KiB catalogue | Validate and pin once in a long-lived desktop context. Cold opening is different from map interaction |
| Accepted warm query measurements approximately 0.46–0.58 s | Existing candidate selection is useful, but population-wide audits remain. No claim of a uniformly instant UI or indexed speed-up |
| Logical validation work: 113 metadata reads/21,900,027 bytes; 523 payload hash operations/211,858,995 bytes | Repeated logical work is not unique stored volume. Do not reopen the publication on each pointer movement |
| Latest world 382 files/19,308,188 bytes; measured Node RSS samples 292–530 MB | Process samples are not combined Node/Python peak memory or mobile budgets |
| Retained pure-Swiss rendering support: 11,429 tiles, 930,914,852 bytes, z12–18 | Existing research tiles are a possible bounded test input; not an authorised complete offline map product |
| Visual production uses AWS Terrarium and exaggeration 1.45; no regional terrain source is enabled | Public rendering is not already an integrated native Riffelhorn view. Do not adopt the failed Swiss/AWS join |

Sources: [accepted prototype inventory](../research/meridian-prototype-architecture.md), [runtime integration measurements](../research/atlas-local-references-results.json), [Swiss support assessment](../atlas/riffelhorn-swiss-support-product.md). No timings were rerun in this documentation review. The approximately 29.1 GB retained-data use and 80 GB laptop planning budget are last reported, not a fresh disk inventory; an external 4 TB drive is available in principle, not assumed mounted or a backup.

### Weather boundary grounded in current implementation

The [current Weather architecture](../global-weather-architecture.md) selects complete NOAA GFS 0.25° runs, prepares ten fields over 24 hourly steps, validates coherent immutable output and advances its own `latest.json`. Node/Python processing remains outside browser execution. It retains the current and one previous complete run; that policy is not Atlas historical retention. A guarded Vite adapter serves selected publication files in development, while builds materialise the selected view. The UI does not automatically operate the updater.

Persistent Weather controllers, manifests, samplers, cancellation and a shared numeric tile cache are potentially reusable technical units. Its nominal cache budget is not proof of bounded total process memory, particularly with pinned entries. Open-Meteo selected-location forecasts/current conditions are a distinct product, not a fallback for missing global GFS overlays. Overzoom does not create local meteorological detail. Preserve run issue, valid time and real accumulation interval; terrain visualisation does not justify new lapse-rate or avalanche inference.

Future Weather offline downloads are selected issued snapshots with manifest closure, rights and ageing status. They can coexist with an Atlas package but must not inherit its observation or knowledge clock. No Weather redesign, migration or processing change occurs in this review.

## Platform alternatives

The rendering engine is a decision separate from its UI wrapper. MapLibre GL JS documents 3D terrain; the published style-support table does **not establish equivalent Android/iOS MapLibre Native terrain support**. Its native terrain roadmap is intent, not shipped capability. Pin exact versions and test; documentation may lag releases. Native hillshade or an offline-region API alone does not prove a 3D elevation mesh. Mapbox documents native terrain and mobile offline support, but introduces commercial/service terms that require review. [MapLibre terrain support](https://maplibre.org/maplibre-style-spec/terrain/), [native terrain roadmap](https://maplibre.org/roadmap/maplibre-native/terrain3d/), [Mapbox terrain](https://docs.mapbox.com/style-spec/reference/terrain/).

| Architecture | Credible advantages | Meridian-specific costs and uncertainty |
|---|---|---|
| A. React Native mobile + React web | TypeScript data/client sharing; native platform components and modules; existing web technical experience | Mobile map engine is distinct from GL JS. Wrappers do not supply absent native terrain. Native download/location/lifecycle work remains; shared JSX is not a goal |
| B. Kotlin Android + Swift iOS + separate web | Direct platform services, accessible native controls and lifecycle integration | Two UI implementations, native build/signing expertise and more device testing. Engine terrain still needs proof; no automatic offline science query implementation |
| C. Shared native computational core + platform UIs | Suitable for expensive cross-platform query/geometry work when justified; consistent computation can be tested once and bridged | C++/Rust/Kotlin core, FFI, bindings and build tooling add costs. Current methods are not automatically portable. Do not rewrite a core before profiling or conformance requirements establish need |
| D. Flutter mobile, optional Flutter web | Coherent Dart UI tooling; native plugins/channels and FFI available | Another language and UI stack; map plugins still depend on their underlying engines. Web renderer/offline behaviour can differ. No evidence it solves the current terrain gap better |
| E. Web-first/PWA | Strong existing GL JS terrain path; easy desktop/browser delivery and accessibility tooling | Browser storage may be evicted; permission/background limits, download persistence and suspended GPU state require tests. A PWA cannot promise native-strength retained storage |
| F. Native shell with web rendering, e.g. Capacitor | Retain a GL JS rendering path while using native files/download/device plugins; incremental web development | WebView GPU, memory, bridge, permissions and lifecycle risks. A native shell does not make Node/Python available or guarantee terrain battery efficiency |

Kotlin Multiplatform is a credible variant of B/C for shared logic with native UI, not a requirement to share Compose screens. React, React Native and Flutter are UI/application approaches, not terrain algorithms. Rust may help a justified compact computational core; its unsafe/FFI boundary still needs review. C++ already underlies established renderers, but adopting it for Meridian would add maintenance. None is necessary merely because another geographical application uses it. [Kotlin shared logic](https://kotlinlang.org/docs/multiplatform/multiplatform-create-first-app.html), [React Native architecture](https://reactnative.dev/architecture/overview), [Flutter platform channels](https://docs.flutter.dev/platform-integration/platform-channels), [Capacitor](https://capacitorjs.com/docs), [Rust unsafe boundaries](https://doc.rust-lang.org/book/ch19-01-unsafe-rust.html).

## Functional comparison: do not substitute framework claims for tests

| Requirement | Web/GL JS | Native engine + platform UI or wrapper | Native shell + GL JS |
|---|---|---|---|
| 2D maps, vectors and hillshade | Established public implementation; style/asset closure needed | Established SDK capability; test equivalent styles | Web rendering plus local-resource bridge |
| High-quality 3D DEM, lighting, exaggeration | Documented terrain path; browser/WebView/device quality differs | Exact SDK/version must demonstrate mesh, encoding and lighting; commercial alternative has documented support | Reuses web mesh path; GPU/lifecycle performance unproven |
| Deliberate offline maps | Local format reader/service worker possible; quota/eviction limits | SDK packs or own readers; styles/fonts/data rights remain separate | Native files can outlive browser caches; integration not automatic |
| Offline routing/search | Requires actual retained graph/index and algorithm, absent from first slice | Native libraries exist, but licencing and data integration are additional tasks | Native plug-in or portable reader needed |
| GPS/background/suspension | Foreground permission possible; limited background reliability | Best access to OS APIs, still subject to policies and termination | Native plugins needed; bridge/recovery must be tested |
| Battery/memory/GPU | Profile terrain and context loss on real devices | Profile SDK and wrappers; no inherent efficiency guarantee | Profile both WebView and native resources |
| Accessibility | DOM/keyboard/list alternatives; canvas itself insufficient | Native controls help; map accessibility still needs designed alternatives | Accessible web controls plus plugin/OS focus testing |
| Tooling/testing/maintenance | Existing TypeScript skills; browser tests do not establish field reliability | Android/iOS toolchains, signing and device CI; wrappers add version compatibility | Web and mobile toolchains; bridge plugins are operational dependencies |
| Ecosystem/licence | Open renderer does not license hosted tiles | Engine/wrapper/software/data licences differ | Same multiple rights layers; shell licence does not grant offline resources |

Equivalent scientific results can come from different conforming readers. Equivalent visual results may need different mesh, shading and camera implementations; numerical metadata agreement is not visual parity. Tests need the same retained DEM/support, comparable views and disclosed exaggeration, not a synthetic performance-only scene.

## Established application evidence

Organic Maps' public repository demonstrates an offline mapping/search/routing project with a C++ core and platform-specific integrations. Its source/binary/data/branding obligations are distinct. OsmAnd exposes a cross-platform core and a GPL-licensed application repository with separate asset exceptions. Their existence supports native-core feasibility, not a claim that Meridian should copy their code or that either demonstrates Meridian's required 3D terrain. [Organic Maps](https://github.com/organicmaps/organicmaps), [maintainer architecture description](https://github.com/organicmaps/organicmaps/blob/master/CLAUDE.md), [OsmAnd core](https://github.com/osmandapp/OsmAnd-core), [OsmAnd licence](https://github.com/osmandapp/OsmAnd/blob/master/LICENSE).

Walkhighlands publishes a supplier brief describing an existing JavaScript PWA and proposing Capacitor/native-file offline development. This is evidence of a documented hybrid approach and browser-storage concerns, **not proof that the proposed replacement shipped or met performance requirements**. [Walkhighlands brief](https://www.walkhighlands.co.uk/images/capacitor-app-requirements.pdf). Closed-source outdoor applications' framework choices were not established by reliable public technical evidence and are not treated as facts.

## Three candidate architectures for bounded feasibility

1. **Native map path with platform UI**: small Kotlin/Swift hosts; evaluate exact MapLibre Native terrain capability. A documented native alternative can be assessed separately on terms first; do not introduce paid accounts/resources implicitly. Kotlin shared logic remains optional.
2. **React Native shell with native map path, separate React web**: determine whether wrapper lifecycle/bridge overhead is material and whether required terrain/offline functionality is exposed. Shares risk with candidate 1; do not benchmark the same engine twice as independent terrain evidence.
3. **Native file-backed shell with GL JS terrain, separate web**: test the known web terrain path on real devices, local file/resource loading and recovery. PWA is a useful browser control, not the only field-storage solution.

Flutter remains credible but outside the first small comparison unless its exact plugin/engine offers a demonstrated capability advantage. No final framework, new native scientific core or renderer is selected. Team hardware, iOS build access, skills and budget are currently unknown. Missing physical-device access must be reported rather than inferred from desktop tests.

## Offline architecture

A future downloadable region should have a versioned manifest: region/support, Atlas publication identity, component/revision references, capabilities, source/rights references, observation/effective/knowledge qualifications, render-product ancestry, coordinate/datum/encoding metadata, reader compatibility, file sizes/checksums and required dependencies. A package may intentionally cover only declared components; it must not claim closure for omitted inputs or unsupported queries. Source-published hashes verify identity; publisher signatures/trusted distribution authenticate origin. Neither replaces scientific qualification.

Keep canonical exported metadata and immutable selected payloads distinct from disposable local indexes and caches. A phone's SQLite index is not publication authority; an SDK's offline tile database is not an Atlas scientific catalogue. Separate personal waypoints/routes from replaceable geographical packages. Record downloaded rights/notice text so attribution remains available offline.

Future download sequence: preflight size/space/licence; stage a new package; resume verified chunks/ranges where supported; verify all declared assets; validate manifest compatibility and membership; atomically select the complete package; retain the previous compatible package until success. Power/process interruption leaves the previous selection usable. HTTP ranges/ETags alone do not authenticate content. Mixed-generation chunks are rejected. Partial data stays labelled partial with explicit supported capabilities, never silently upgraded to complete.

Include style JSON, sprites, fonts/glyphs, basemap, terrain and relevant metadata in the offline dependency inventory. Audit hidden third-party URLs. Allow metered-network controls, user quota and deletion; do not evict deliberate packages as ordinary cache without warning/consent. Evict rebuildable caches first. Test disk-full, user deletion, incompatible reader, unavailable mounted volume, revoked permission and OS termination. Defer delta updates until whole-package correctness and measured bandwidth justify them.

PMTiles is a compact read-only tiled archive with range access; updating it generally creates a replacement. MBTiles is a SQLite tile container with its own addressing convention, requiring tested XYZ/TMS conversion. Neither automatically represents Atlas dependencies or licences nor guarantees native reader support. MapLibre/Mapbox offline packs can be useful but bring SDK-specific format/lifecycle and provider constraints. Format selection is provisional pending reader, rights and recovery tests. [PMTiles](https://docs.protomaps.com/pmtiles/), [MBTiles](https://github.com/mapbox/mbtiles-spec/blob/master/1.3/spec.md), [MapLibre React Native offline manager](https://maplibre.org/maplibre-react-native/docs/modules/offline-manager/), [Mapbox offline guide](https://docs.mapbox.com/help/dive-deeper/mobile-offline/).

Browser persistence is subject to quota, eviction and OS behaviour; installed PWA status is not an unconditional storage guarantee. Native background transfers and location also have OS lifecycle restrictions. Test termination and force-quit separately; do not promise continuous background progress. [WebKit storage policy](https://www.webkit.org/blog/14403/updates-to-storage-policy/), [Apple background transfers](<https://developer.apple.com/documentation/foundation/urlsessionconfiguration/background(withidentifier:)>), [Android location permissions](https://developer.android.com/develop/sensors-and-location/location/permissions).

| Maturity | Reasonable offline scope | Not promised |
|---|---|---|
| First prototype | Explicitly bounded retained terrain/evidence demonstration; provenance locally readable; honest missing basemap/labels if assets unavailable | Complete regional maps, live forecasts, search/routing or background tracking |
| Early private beta | One deliberately downloaded complete supported package; deletion, quota, interruption and relaunch tests; saved local positions if implemented | Nationwide coverage or automatic deltas |
| Extended private beta | Several packages, compatible updates, optional local search/waypoints; forecast snapshots with ageing; routing only after its own evidence/licence/safety gates | Seamless live conditions offline or guaranteed OS background execution |
| Public release | Declared devices/regions/capabilities, tested upgrade/recovery, rights-complete notices and user storage controls | Functions outside stated coverage or safety suitability |
| Longer term | Measured need may justify compact routing/search graphs, delta updates or broader packages | A requirement to ship every possible offline capability |

## Infrastructure alternatives and cost

| Approach | Useful role | Cost/operational burden and portability |
|---|---|---|
| Local-first workstation | Scientific preparation, validation and prototype development | Device capacity, backup and worker setup; no high-availability promise |
| Independent hosting/VPS | Later small read-only delivery or API where needed | Patching, TLS, monitoring, recovery and bandwidth remain project work |
| Microsoft Azure | Blob delivery, managed compute/identity/monitoring | Redundancy, operations, transfer and service-specific coupling; evaluate actual workload |
| Google Cloud | Object delivery and managed processing | Storage class, operations and network charges; managed APIs create lock-in |
| AWS | Object delivery and flexible batch/compute | Storage/requests/retrieval/egress/IAM burden; no free-data implication from S3 hosting |
| Other object/CDN arrangements, e.g. R2 | Later immutable package delivery | R2 currently advertises no direct egress charge; storage/operations and surrounding services still cost |
| Hybrid | Local processing plus independently delivered immutable packages | Sensible later option; still needs publication, rights, restore and access policy |

Official pricing dimensions: [Azure Blob](https://azure.microsoft.com/en-us/pricing/details/storage/blobs/), [Google Cloud Storage](https://cloud.google.com/storage/pricing), [AWS S3](https://aws.amazon.com/s3/pricing/), [Cloudflare R2](https://developers.cloudflare.com/r2/pricing/). No provider quote, account or resource is created. Compare actual region size × retained versions × users' downloads, operations, compute hours, logs, backup copies and transfer. Do not invent request rates or assume free egress removes all cost.

Local prototype needs no cloud. Private beta may use controlled distribution and immutable read-only packages before any persistent application service. Public release needs reliable delivery, status, backup/restore and security operations appropriate to actual features. Larger scale can revisit CDN/compute/database choices when measured. Avoid a distributed catalogue, event bus, always-on GIS workers or multi-cloud replication now.

Keep identity/location separate; use configured roots and portable manifests, explicit HTTP/object boundaries where required, and no embedded provider credentials. S3-compatible does not mean identical semantics. Do not abstract every provider feature in advance. Scientific batch processing has environment and memory needs unlike a tiny request handler. Atlas and Weather publish independently; an application view can pin both identities without one scientific transaction.

An external disk extends capacity but is neither always available nor a backup. Back up irreplaceable user data, canonical metadata, source rights records and release keys separately; restore-test before beta. Large replaceable caches have lower priority. Define recovery point/time targets only after operational needs and costs are known.

## Performance acceptance direction

For the bounded prototype, show startup progress and permit map use while evidence is unavailable; never display unvalidated records as current. Keep one pinned context; cancel superseded map requests and cache only by explicit publication/query identity. Proposed desktop budgets from the previous plan remain provisional; use a target of qualified inspection within 2 seconds warm on named hardware and no publication reopen per map gesture. Render responsiveness and device memory are separate tests. Do not relax full authoritative validation to meet a UI budget.

The next feasibility study should profile a small retained terrain subset, identical views, query fixtures, offline launch and process recovery. Provisional sustained-interaction target: 30 fps on a named representative physical device, with 2D degradation and no crash/context-loss concealment. Report distributions, memory and a controlled battery/thermal comparison, not global guarantees. Final supported-device budgets await device evidence.

## Architecture evolution and operational exposure

The [subsystem evolution register](evolution.md) separates long-lived scientific/product responsibilities from current implementations, workload dimensions, measured revisit triggers and migration protections. The existing GL JS web renderer is experimental evidence, not a cross-platform commitment. Portable readers, mobile framework and native terrain remain unresolved; no shared native core or universal provider layer is selected.

Before unrestricted public access, the [economics gate](economics.md) requires a concrete delivery/dependency inventory, fixed/variable costs, ordinary/high-demand/adverse scenarios, user-approved budget and exposure ceiling, and verified control/suspension/recovery behaviour. Budget alerts are not universal caps. This supplements provider comparisons above without choosing a provider, estimating a bill or creating infrastructure. Internal, alpha and beta scopes follow the [eight-stage roadmap](roadmap.md); the earlier offline capability stages are capability targets within that lifecycle, not automatic invitations to testers.
