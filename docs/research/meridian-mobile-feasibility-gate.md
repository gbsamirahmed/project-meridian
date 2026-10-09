# Meridian mobile terrain and offline evidence feasibility — prerequisite gate

Recorded and external sources checked **9 October 2026**. This is a Stage 1 inventory and capability review, followed by the required prerequisite stop. It is not a completed mobile experiment or a platform recommendation.

## Result and starting checkpoint

**PREREQUISITE GATE — MOBILE FEASIBILITY NOT ESTABLISHED.** No physical test device is connected to the inspected Windows host; Android build/debug tools were not found in the checked locations; iOS hardware and Mac/Xcode build access have not been confirmed. Device availability elsewhere remains unknown. These observations prevent the required named-device terrain, offline, recovery, battery and thermal experiments. They do not demonstrate that the owner has no devices or that Meridian cannot work on mobile.

Public repository `gbsamirahmed/project-meridian`, required and observed HEAD `f2c1e3db8dd78eb592a07745e1b4645b241f1408`, `main` / `origin/main`. The initial tree was clean. Origin was fetched; divergence was 0/0 and the checkpoint remained exact before documentation changes. No unrelated work required reconciliation.

The [Foundations scope](../foundations/summary.md#exactly-one-next-bounded-task--not-begun) explicitly requires named physical hardware and permits stopping when it is unavailable. The study has begun its inventory; its experiments are blocked. Historical “NOT BEGUN” entries describe earlier tasks, not today's status. The accepted prototype-readiness finding remains valid within its retained local boundary; it supplies no mobile performance or offline guarantees.

## Authority reviewed and frozen boundary

Read the committed [summary](../foundations/summary.md), [decision register](../foundations/decisions.md), [platform options](../foundations/platform.md), [engineering standards](../foundations/engineering.md), [roadmap](../foundations/roadmap.md), [economics](../foundations/economics.md), [evolution register](../foundations/evolution.md) and [reconciliation](../foundations/reconciliation.md). Reviewed the actual [prototype plan](meridian-prototype-architecture.md), [runtime guide](../../runtime/atlas/README.md), [Riffelhorn preparation](atlas-riffelhorn-preparation.md), [retrieval semantics](atlas-riffelhorn-retrieval.md), [Swiss terrain product](../atlas/riffelhorn-swiss-support-product.md), its [source/product record](../atlas/riffelhorn-support-product.json) and the accepted [failed reconciliation](../atlas/riffelhorn-terrain-reconciliation.md). The latter remains negative evidence; none of its Swiss/AWS blends is adopted.

The frozen uncertainty is whether actual elevation-based terrain and an independently usable, read-only qualified Atlas view work offline on representative mobile hardware within measured resource limits. Mandatory acceptance remains physical-device evidence, genuine terrain-disabled 2D comparison, at least 25 predetermined desktop-reference query cases, full offline resource closure and failure recovery. The 30 fps interaction and 2 seconds warm-inspection targets are investigation targets, not guarantees. No criterion has been relaxed to fit the available host.

No implementation starts at this gate. F03, F04, F05, F11, F12 and F16 retain their existing decision statuses. There is no final framework, reader contract, package format, renderer adoption or expensive private-repository restructuring decision. Shared scientific meaning and immutable publication identity remain requirements; Node/Python remains the reference implementation, not a mandatory mobile network service.

## Device and tooling inventory

All observations below concern this host on the recorded date. Inventory commands are read-only. No serial numbers, location history or personal files were collected.

| Item | Observed result | Evidence category and limit |
| --- | --- | --- |
| Host OS | Windows kernel/build string `Microsoft Windows 10.0.26200` | Locally observed; not a marketing-edition identification |
| Connected phones/tablets | Windows PnP enumeration returned no entries matching Android, ADB, iPhone, iPad, Apple Mobile or MTP | Locally observed, bounded name search; not an exhaustive device/ownership inventory |
| Physical Android model / OS / GPU / RAM | Unconfirmed | No device performance or compatibility evidence |
| Physical iOS model / OS / GPU / RAM | Unconfirmed | No device performance or compatibility evidence |
| Mac, Xcode, signing and deployment access | Unconfirmed off-host; `xcrun` and `xcodebuild` absent on this Windows host | iOS build/deployment not tested |
| Android SDK and Android Studio | `ANDROID_HOME` / `ANDROID_SDK_ROOT` unset; conventional `%LOCALAPPDATA%/Android/Sdk` and `C:/Program Files/Android/Android Studio` absent | Other installation locations/off-host access unknown |
| ADB, SDK manager and Gradle | Not on PATH | No ADB device enumeration or USB-debug authorisation test; no Android build attempted |
| Java / Javac | Oracle 21.0.2, runtime `21.0.2+13-LTS-58` | Locally observed; compatibility with a future chosen Android plugin is untested |
| Node / npm | 24.11.0 / 11.6.2 | Locally observed; sufficient to inspect existing desktop tooling, not mobile validation |
| Flutter / CMake | Not on PATH | No framework/build test |
| Rust / Cargo | 1.87.0 / 1.87.0 | Locally observed; availability does not justify a shared native core |
| GL JS source | Existing dependency pinned to 6.11.2; installed source inspected | Source-level capability evidence, no new rendering trial |

The owner was asked which physical devices and Mac/Xcode access could be made available. No answer was available when this gate was recorded. Unknown access is not treated as refusal or proof of absence. No toolchain installation has been requested or performed; exact SDK/build requirements, download size, disk footprint and temporary requirements cannot responsibly be set before device/OS and renderer selection. Report those resources before any substantial installation and obtain the necessary approval.

### Reproduce the bounded inventory

From the public checkout in PowerShell; these commands do not install anything:

```powershell
git status --short
git rev-parse HEAD
git remote -v
git rev-parse --abbrev-ref '@{u}'
git rev-list --left-right --count HEAD...origin/main
[System.Runtime.InteropServices.RuntimeInformation]::OSDescription
'adb','java','javac','gradle','sdkmanager','node','npm.cmd','flutter','rustc','cargo','cmake','xcrun','xcodebuild' |
  ForEach-Object { Get-Command $_ -ErrorAction SilentlyContinue | Select-Object Name,Source }
Get-Item Env:ANDROID_HOME,Env:ANDROID_SDK_ROOT -ErrorAction SilentlyContinue
Test-Path (Join-Path $env:LOCALAPPDATA 'Android/Sdk')
Test-Path 'C:/Program Files/Android/Android Studio'
Get-CimInstance Win32_PnPEntity |
  Where-Object { $_.Name -match 'Android|ADB|iPhone|iPad|Apple Mobile|MTP' } |
  Select-Object Name,Status
node --version
npm.cmd --version
java -version
javac -version
rustc --version
cargo --version
```

A connected device must subsequently be explicitly identified and authorised for debugging; do not infer this from USB attachment. Remote hardware or a Mac requires confirmed access and an agreed measurement operator. No permission to collect personal location history is needed or implied.

## Candidate capability and rights matrix

These are bounded investigation paths, not implemented shells. No shell or renderer was built, installed or benchmarked. At most two distinct renderer paths remain proposed; multiple wrappers must not become additional “independent” renderer trials. A platform-specific native shell and a minimal file-backed web shell are sufficient starting shell categories; React Native/Flutter wrappers are not required to resolve the renderer question.

| Path | Exact version evidence | Terrain / 2D status | Offline / rights status | Gate |
| --- | --- | --- | --- | --- |
| MapLibre Native in a small Android/iOS native shell | Published Android `android-v13.5.3` and iOS `ios-v6.31.0` release references inspected; neither installed or selected | Credible native map path. The official terrain support table marks Android/iOS terrain unsupported; a terrain roadmap is not shipped capability. Exact-binary elevation terrain remains unestablished here. Native 2D comparison is untested | Native project licence is BSD-2-Clause; exact release and bundled third-party notices must be checked before distribution. Local/offline resource loading and recovery untested | Confirm terrain capability for the exact eligible SDK before scheduling a 3D benchmark. If unsupported, report that result; do not build a renderer or substitute hillshade |
| MapLibre GL JS 6.11.2 in a device browser or minimal local-file-backed shell | Repository pin and installed `src/ui/map.ts` inspected | Terrain documented and already exercised in accepted desktop research. Source has real terrain removal with `setTerrain(null)` and `getTerrain()` returning null; this is source inspection, not device behaviour. WebGL/device limits unknown | Installed main licence is BSD-3-Clause with additional bundled notices. Browser storage is quota/eviction-dependent; a shell's asset-loading closure and privileges require testing. No offline package has been produced | Named physical device and a lawful, complete local asset set required; browser and embedded shell are the same renderer path |

Primary capability references checked 9 October 2026: [MapLibre terrain support table](https://maplibre.org/maplibre-style-spec/terrain/), [Native terrain roadmap](https://maplibre.org/roadmap/maplibre-native/terrain3d/), [Native release records](https://github.com/maplibre/maplibre-native/releases), [Native licence](https://github.com/maplibre/maplibre-native/blob/main/LICENSE.md), and [pinned GL JS implementation](https://github.com/maplibre/maplibre-gl-js/blob/v6.11.2/src/ui/map.ts). Version references are not a claim that these are the newest versions on every release channel. Support documentation may lag releases; its negative native entry is a reason to verify, not an empirical test of all SDKs. The iOS API page could not be retrieved during this review; no capability claim is inferred from that failure.

Android documents distinct persistent app files and evictable cache files, with app-specific files removed on uninstall. A deliberate ready package must not rely on a cache flag. [Android app-specific storage](https://developer.android.com/training/data-storage/app-specific) was checked on the recorded date. WebKit documents quotas, possible eviction and heuristic persistence requests; advertised quotas do not guarantee allocatable storage. [WebKit storage policy](https://webkit.org/blog/14403/updates-to-storage-policy/) (10 August 2023, checked 9 October 2026) supplies documentation-only constraints, not a tested iPhone guarantee. No browser or OS storage guarantee is introduced by this review.

Software licences do not confer rights to terrain, imagery, labels, fonts, sprites or source evidence. Accepted source-specific attribution/redistribution records remain the basis; exact offline assets and third-party notices still need package-level verification. No account, API key, paid SDK or replacement basemap is introduced.

## Retained input identities and resource boundary

This is an exact **reference inventory**, not a selected mobile-package manifest. No tile subset was selected, copied or declared complete. Native fixture inputs were checked against existing recorded hashes by the repository safeguards; the full terrain pyramid was not rehashed or repackaged during this gate.

| Retained reference | Accepted identity and population | Meaning / boundary |
| --- | --- | --- |
| Swiss support source | `b24a4fdc7b378ba79d442d0ce216a031dfb95a6bc6eed5ad9c33be61175651f4`; 100 TIFFs / 1,667,166,026 bytes | DTM, 0.5 m distributed grid, LV95 EPSG:2056, LN02 EPSG:5728 metres; mixed acquisition support, per-cell epoch unknown |
| Pure Swiss rendering product | `1a44a0644de1bde73a3ba84d1b761dc0aa17d48cc971e5f6b5d2c14fb329d7ea`; 11,429 PNG tiles / 930,914,852 bytes, z12–18 | EPSG:3857 XYZ, 256×256 lossless Terrarium; complete tiles only, support varies by zoom. No coarse tiles below z12 or AWS fill |
| Qualified native fixture | Preparation revision `357b28e705f7c2647cdf2d54467fc9ee851465814d8ed645cae30713ef9187bb`; 12 inputs / 120,347,916 bytes; prepared members plus manifest 5,605,110 bytes | 4 km² core EPSG:2056 `[2624000,1091000,2626000,1093000]`; 44 queryable records: 6 raster supports and 38 native features |
| Existing published world | Canonical publication history described in the runtime and prototype reports | Must resolve and validate explicit existing generations before projection. No mobile projection or selected test-generation pair created here |

The exact source file inventories remain in [support acquisition](../atlas/riffelhorn-support-acquisition.json), [terrain product](../atlas/riffelhorn-support-product.json), [fixture specification](atlas-regional-expansion-fixture.json) and [preparation receipt](atlas-riffelhorn-preparation-results.json). Those accepted files are unchanged. Historical counts and bytes above are not new throughput or phone measurements.

The full rendering pyramid exceeds the 250 MB test-payload target and must not be copied wholesale. Once test cameras and zoom limits are fixed, enumerate only complete retained tiles intersecting their required loading closure, sum actual sizes, verify every selected hash, and record exact paths and omitted coverage. Include style/reader/evidence assets in the same budget; bound staging and last-ready copies separately before writing. Until that manifest exists there is no package size estimate or completeness claim. This gate generated zero terrain/evidence copies and zero mobile payload bytes.

Terrarium decoding remains `R*256 + G + B/256 - 32768` metres; horizontal preparation did not transform LN02 heights. Declared exaggeration must be recorded separately from elevation; the historical renderer's 1.45 is not an analytical height adjustment. Compare a known unity-exaggeration state and any declared visual exaggeration honestly. Copernicus DSM/EGM2008 is independent evidence, not a fill source or an equivalent DTM. Quantisation and sampled preparation fidelity do not establish physical height accuracy.

Existing network-backed experimental map styles are not a verified lawful offline dependency closure. Availability/rights of exact basemap, label, font and sprite assets remain unresolved; no replacements were acquired. A terrain-only, explicitly unlabelled scientific test may be useful later, but cannot establish completeness of an experience that promises labels or a basemap.

## Experiments blocked and requirements preserved

| Study stage | Actual result at this checkpoint |
| --- | --- |
| 1: capability/device inventory | Bounded host inventory and primary/source capability review performed; physical devices and off-host build access unconfirmed |
| 2: experiment selection | Two renderer paths identified for investigation; no executable versions/shells selected or driver written |
| 3: retained subset | Reference identities reviewed and protected fixture integrity checked; no complete-tile subset/packaging manifest or temporary copies |
| 4: terrain / 2D–3D | **Not tested on physical hardware, emulator or a fresh desktop driver**. No frame-time, memory, battery, thermal, startup or visual results |
| 5: portable offline Atlas | **Not implemented or tested**. Zero of the required 25 mobile/reference comparisons performed; no new scientific reader authority |
| 6: offline / recovery | **Not tested**. No airplane-mode, termination, interrupted installation, corrupt package, last-ready preservation or deletion results |
| 7: provisional architecture decision | Specific prerequisite blocker established; no preferred mobile framework or validated renderer |

For resumption, freeze named device/OS/SDK and fixed cameras inside exact complete-tile coverage before running. Test both actual terrain-enabled and disabled states with comparable camera trajectories, source assets, brightness, power/network/temperature conditions and durations. A top-down camera or zero exaggeration alone is not proof that the 3D path is disabled. Report distributions and controlled repeated thermal/battery trials, not a single FPS value. Do not extrapolate the desktop camera captures or 9.11 s full-open / 838 ms catalogue / 220 KiB baseline to a phone.

The portable projection must preserve the selected generation, exact evidence/revision identifiers, source/preparation/method lineage, native support/CRS and datum distinctions, rights, uncertainty, role-specific time and supported/unsupported capability outcomes. Native spatial boundary conventions and unknown time cannot be replaced by bounding boxes or unrestricted matching. Freeze at least 25 exact query requests and independent desktop envelopes before implementing matching. Include historical generations and unsupported/absent/indeterminate outcomes. Scope this only after hardware/build prerequisites are resolved; none of these are completed results.

Offline readiness requires the complete manifest-bound terrain, style/font/sprite/attribution, evidence, reader and any other runtime dependency closure. An incomplete or corrupt install cannot replace the last compatible ready state. Account for storage failure, reader incompatibility and user deletion; test restart in airplane mode. Integrity hashes establish byte identity, not permission or upstream authenticity. No package is currently asserted ready.

## Decisions and exactly one subsequent task — NOT BEGUN

**Decide now:** preserve all accepted authority and scientific qualifications; stop at the physical-device/build prerequisite; retain the two-renderer limit and the 250 MB payload target; make no mobile field-validation claim.

**Defer pending evidence:** F03 portable client, F04 native terrain, F05 offline reliability, F11 framework, F12 portable scientific conformance and F16 visual/offline product adoption. Hardware-specific capability, rights closure and measured resource behaviour remain unresolved. Existing local read-only adapter remains a reference, not an offline mobile dependency.

Exactly one subsequent bounded task: **MERIDIAN MOBILE FEASIBILITY PREREQUISITE RESOLUTION — PHYSICAL DEVICES AND BUILD ACCESS**.

- **Objective:** establish a usable, explicitly authorised physical Android/iOS and build-access inventory so the requested feasibility experiments can resume honestly.
- **Starting evidence:** this gate, the unchanged Foundations study scope and accepted Riffelhorn references.
- **Scope:** confirm named model/OS and representative hardware constraints; identify available Android tools and Mac/Xcode/signing/deployment access; agree physical access/operator and device-debug consent; specify exact candidate build requirements and download/disk/temporary resource estimates. If installations are necessary, report them and obtain approval before proceeding. No private repository, new data, paid/cloud resource or final framework selection.
- **Deliverable:** a reproducible device/build-access record, platform limitations and an approved or explicitly blocked resource plan. Existing SDK terrain support must be checked for the exact candidate versions before any native 3D trial is promised.
- **Acceptance:** at least one named physical platform has confirmed access and a workable build/debug route; every unavailable platform is explicitly limited. Both platforms are required before claiming cross-platform findings. Unavailable iOS/Mac access may remain a precise platform blocker, never fabricated coverage.
- **Stop condition:** record that prerequisite outcome and conditions for resuming the original terrain/offline study. Do not build the prototype, start renderer/reader experiments or restructure the private repository in the prerequisite task.

This follow-up is **not begun**. The present checkpoint is a valid documented stop, not completion of the full feasibility study.

## Verification and delivery boundary

Only this gate report and append-only navigation notes are changed. The committed Foundations decision register and historical prototype report remain unchanged. Safeguards check all other tracked files, 42 canonical status rows, 113 protected production hashes and retained accepted evidence/publications; internal documentation links and whitespace are checked. No executable application tests, types, lint or build are required or claimed for this documentation-only checkpoint.

No private-repository access, new geographical acquisition, SDK installation, large research download, personal-data collection, cloud/paid resource, public endpoint, production UI, canonical modification or S7 occurred. No test driver or catalogue is committed. Device performance, portable-reader conformance and package recovery are explicitly **not performed**, not passed. Final verification counts and Git delivery state are recorded in the development log and delivery message.
