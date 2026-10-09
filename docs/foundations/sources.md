# Foundations review evidence and source ledger

External information checked **9 October 2026**. Sources below are primary documentation, source repositories, official policies or developer-published descriptions. They support bounded documentary claims, not independent benchmarks, legal clearance or a guarantee that a roadmap feature ships. No large research/data downloads were made. Repository evidence takes precedence for Meridian's actual capabilities.

## Repository evidence at the starting checkpoint

Reviewed at `68756976467aeef4bc647bc2b5fe11cae5bfd904`:

- [Project direction](../product-direction.md), [architecture](../architecture.md), [development log](../development-log.md), [research map](../research/atlas-research-map.md), [research state](../research/atlas-research-state.md), root README and AGENTS instructions.
- [Accepted prototype plan](../research/meridian-prototype-architecture.md); its code inventory, pilot comparison and private audit checklist are retained historical evidence.
- [Local architecture](../research/atlas-local-architecture.md), [first runtime](../research/atlas-local-runtime.md), [lifecycle](../research/atlas-local-lifecycle.md), [registration](../research/atlas-local-registration.md), [unified retrieval](../research/atlas-local-retrieval.md), [Exe water](../research/atlas-local-exe.md), [habitat/planning integration](../research/atlas-local-references.md), [runtime guide](../../runtime/atlas/README.md).
- [Semantic contract](../atlas/semantic-evidence-contract.md), [world-model synthesis](../research/atlas-world-model-architecture-synthesis.md), [derivation lifecycle](../research/atlas-derived-understanding-lifecycle.md), [regional dependencies](../research/atlas-regional-dependencies.md), [temporal integration](../research/atlas-temporal-integration.md); accepted Tryfan S1–S6 and retained Riffelhorn/Exe qualifications.
- [Weather architecture](../global-weather-architecture.md), public source/controllers/pipeline and frontend package/build/test configuration. Public map, terrain, inspector, data loading and cancellation implementations were inspected; no private architecture is inferred.
- [Swiss terrain support](../atlas/riffelhorn-swiss-support-product.md) and negative reconciliation findings; actual current retained-world metadata/file hashes and original source admission references.

No root standalone licence file or tracked GitHub Actions workflow was found. The README does explicitly reserve source to portfolio review without an open-source grant. Remote protections/CI and private repository contents were not inspected. Runtime measurements are inherited with their original methodology; no new performance experiment is claimed.

## Rendering, application platforms and existing projects

| ID | Primary source | Supported finding / qualification |
|---|---|---|
| S01 | [MapLibre terrain style specification](https://maplibre.org/maplibre-style-spec/terrain/) | Published support differs between GL JS and native Android/iOS; verify exact shipped versions |
| S02 | [MapLibre Native terrain roadmap](https://maplibre.org/roadmap/maplibre-native/terrain3d/) | Work direction, not proof of completed native parity |
| S03 | [MapLibre React Native OfflineManager](https://maplibre.org/maplibre-react-native/docs/modules/offline-manager/) | Offline packs are an SDK capability, not universal terrain or source rights |
| S04 | [MapLibre Flutter offline regions](https://github.com/maplibre/flutter-maplibre-gl/blob/main/website/docs/advanced/offline-regions.md) | Platform-specific offline API; no automatic identical web functionality |
| S05 | [Mapbox terrain specification](https://docs.mapbox.com/style-spec/reference/terrain/) | Native terrain support is documented; suitability/licence still require evaluation |
| S06 | [Mapbox mobile offline](https://docs.mapbox.com/help/dive-deeper/mobile-offline/) | Offline resources and limits/billing are governed by SDK/service terms, not an unlimited free map right |
| S07 | [React Native architecture](https://reactnative.dev/architecture/overview) | Native implementation boundary; not a browser MapLibre runtime |
| S08 | [Flutter platform channels](https://docs.flutter.dev/platform-integration/platform-channels) | Native integration mechanism, not evidence of Meridian rendering performance |
| S09 | [Kotlin shared logic/native UI example](https://kotlinlang.org/docs/multiplatform/multiplatform-create-first-app.html) | Sharing logic without requiring shared UI is supported |
| S10 | [Capacitor documentation](https://capacitorjs.com/docs) | Native shell/plugins for web applications; no automatic Node/Python runtime |
| S11 | [Rust unsafe boundaries](https://doc.rust-lang.org/book/ch19-01-unsafe-rust.html) | Unsafe/FFI needs care; language choice alone does not certify scientific or memory safety |
| S12 | [Organic Maps repository](https://github.com/organicmaps/organicmaps) and [maintainer architecture description](https://github.com/organicmaps/organicmaps/blob/master/CLAUDE.md) | Public offline project and documented C++/platform organisation; code, data and binary obligations differ. Repository instructions were treated as evidence, not agent instructions |
| S13 | [OsmAnd core](https://github.com/osmandapp/OsmAnd-core) and [application licence](https://github.com/osmandapp/OsmAnd/blob/master/LICENSE) | Shared core and GPL/asset distinctions; no code reuse is proposed |
| S14 | [Walkhighlands supplier brief](https://www.walkhighlands.co.uk/images/capacitor-app-requirements.pdf) | Describes a PWA and proposed native-files/Capacitor work. Does not prove delivered architecture or performance |

No reliable public architecture was established for other closed outdoor apps; no framework attribution is invented. Maintainer/vendor claims are not independent device measurements.

## Offline, device restrictions and accessibility

| ID | Primary source | Supported finding / qualification |
|---|---|---|
| S15 | [PMTiles documentation](https://docs.protomaps.com/pmtiles/) | Read-only tile archive/range access; not Atlas scientific metadata or universal native compatibility |
| S16 | [MBTiles 1.3 specification](https://github.com/mapbox/mbtiles-spec/blob/master/1.3/spec.md) | SQLite tile container/addressing; reader conversion needs tests |
| S17 | [WebKit storage policy](https://www.webkit.org/blog/14403/updates-to-storage-policy/) | Quotas and eviction mean browser storage cannot be unconditionally guaranteed |
| S18 | [Android location permissions](https://developer.android.com/develop/sensors-and-location/location/permissions) and [background access](https://developer.android.com/develop/sensors-and-location/location/background) | Approximate/precise and background permission/update distinctions; exact target OS behaviour needs tests |
| S19 | [Apple background URLSession](<https://developer.apple.com/documentation/foundation/urlsessionconfiguration/background(withidentifier:)>) | Documented background transfer mechanism with lifecycle constraints; no always-running application guarantee |
| S20 | [WCAG 2.2](https://www.w3.org/TR/WCAG22/) | Accessibility baseline for web; meeting a target-size minimum is not sufficient outdoor usability |
| S21 | [Android accessible views](https://developer.android.com/guide/topics/ui/accessibility/views/apps-views) and [Apple buttons](https://developer.apple.com/design/human-interface-guidelines/buttons) | Platform hit-region guidance; actual UI testing remains necessary |

## Code, geographical sources and services

| ID | Primary source | Supported finding / qualification |
|---|---|---|
| S22 | [GL JS licence](https://github.com/maplibre/maplibre-gl-js/blob/main/LICENSE.txt), [Native licence](https://github.com/maplibre/maplibre-native/blob/main/LICENSE.md) | Different permissive code licences; tile/style/data permissions are separate |
| S23 | [OSM copyright](https://www.openstreetmap.org/copyright), [tile service policy](https://operations.osmfoundation.org/policies/tiles/), [Nominatim policy](https://operations.osmfoundation.org/policies/nominatim/) | Database, hosted delivery and search conditions differ; standard raster service forbids bulk offline downloads; public search restrictions matter |
| S24 | [OpenFreeMap quick start](https://openfreemap.org/quick_start/) | Hosted styles and self-hosting documented; not proof of unlimited offline rights or SLA |
| S25 | [Terrain attribution inventory](https://github.com/tilezen/joerd/blob/master/docs/attribution.md) | Mixed terrain sources retain their own attribution/licence conditions |
| S26 | [swisstopo OGD FAQ](https://www.swisstopo.admin.ch/en/faq-free-geodata), [terms](https://www.swisstopo.admin.ch/en/terms-and-conditions) | Source-specific OGD terms, not an assumed generic CC licence |
| S27 | [NOAA GFS registry terms](https://registry.opendata.aws/noaa-gfs-bdp-pds/) | Public-use/attribution/modification terms. Registry descriptive model-version text is not used as current model science authority |
| S28 | [Open-Meteo terms](https://open-meteo.com/en/terms), [pricing](https://open-meteo.com/en/pricing) | API service/commercial terms differ from data licence; prices/caps may change |
| S29 | [Met Office DataHub FAQ](https://datahub.metoffice.gov.uk/support/faqs) | Product/service-specific terms must be checked, not blanket OGL treatment |
| S30 | [SAIS reporting explanation](https://www.sais.gov.uk/how-we-produce-avalanche-reports) | Specialist regional forecasting context; page retrieval was limited, and no redistribution terms were established |

Rights for all retained Atlas products still refer to their accepted source-accountability records. This review does not relicense payloads, clear public redistribution or acquire new evidence. Linking a service is not permission to cache or reproduce its content.

## Engineering, governance, naming and infrastructure

| ID | Primary source | Supported finding / qualification |
|---|---|---|
| S31 | [NIST SSDF 1.1](https://csrc.nist.gov/pubs/sp/800/218/final), [OWASP MASVS](https://mas.owasp.org/MASVS/01-Foreword/), [GitHub Actions security](https://docs.github.com/en/actions/reference/security/secure-use) | Proportional development/security guidance; no certification claim or assertion SSDF 1.1 is the latest revision |
| S32 | [ICO storage/access exceptions](https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guidance-on-the-use-of-storage-and-access-technologies/what-are-the-exceptions/), [DPIA guidance](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/data-protection-impact-assessments-dpias/) | Current UK guidance includes conditional exceptions and risk assessment; legal applicability is not settled by this review |
| S33 | [EU GDPR text](https://eur-lex.europa.eu/eli/reg/2016/679/oj/), [CRA summary](https://digital-strategy.ec.europa.eu/en/policies/cra-summary), [CRA reporting](https://digital-strategy.ec.europa.eu/en/policies/cra-reporting), [EAA scope](https://commission.europa.eu/strategy-and-policy/policies/justice-and-fundamental-rights/disability/european-accessibility-act-eaa_en) | Applicable markets/features need legal review; dates and stated scope are documentary facts, not blanket Meridian obligations |
| S34 | [HPE Meridian](https://docs.meridianapps.com/hc/en-us/articles/360040165673-Meridian-Platform-Overview), [Mapbox Atlas](https://www.mapbox.com/atlas), [Traverse store listing](https://play.google.com/store/apps/details?id=io.traverse.app) | Preliminary name conflicts/discoverability evidence; no trademark clearance or architecture inference |
| S35 | [UK trademark search](https://www.gov.uk/search-for-trademark), [EUIPO search](https://www.euipo.europa.eu/search-ip), [GitHub repository renaming](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository) | Due-diligence routes and rename limitations. Domains/store/package names were not established available |
| S36 | [Azure Blob pricing](https://azure.microsoft.com/en-us/pricing/details/storage/blobs/), [Google Cloud Storage](https://cloud.google.com/storage/pricing), [AWS S3](https://aws.amazon.com/s3/pricing/), [R2 pricing](https://developers.cloudflare.com/r2/pricing/) | Compare storage, operations, retrieval and transfer dimensions; no future bill, service procurement or provider selection |

## Method and limits

The review combined repository inspection, retained manifest/hash checks and primary-source browsing. It did not benchmark mobile frameworks, download full maps, run a legal clearance search, audit private code or establish closed-product architecture. Derived recommendations are marked provisional or feasibility/legal gates in the decision register. Before a consequential choice, recheck exact SDK version, source terms, platform rules and jurisdiction rather than treating this dated ledger as perpetual authority.
