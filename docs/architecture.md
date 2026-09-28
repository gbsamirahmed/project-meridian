# Meridian architecture contract

This document records Meridian's current architectural direction. It defines boundaries for future change; it does not claim that the existing repository has already been reorganised to match them.

## Product vocabulary

- **Meridian** is the overall project and ecosystem.
- **Atlas** represents and explores the physical world: terrain, elevation, surface evidence, imagery and spatial reference locations.
- **Weather** represents atmospheric observations, forecasts and weather visualisation.
- **Traverse** is the provisional product name for route, journey and movement planning. Technical code should continue to use precise terms such as route, path, waypoint, segment and journey.
- **Tryfan** is Atlas's first reference location. It is data and a validation target, not an architectural layer.
- A **Reference Renderer** is a high-fidelity environment used to inspect and validate Atlas representations. It consumes Meridian representations; it does not define them.
- **Lab NNN** and **Experiment** identify bounded historical investigations. Existing Earth Lab names remain part of their provenance.

Traverse may be renamed without renaming generic route concepts. Likewise, historical Lab identifiers remain stable even when useful implementation is later promoted into shared Atlas or renderer infrastructure.

## Modularity without fragmentation

The design test is: a change inside one domain should have the smallest reasonable blast radius outside that domain. Prefer cohesive modules with explicit responsibilities and small stable contracts. Do not introduce packages, interfaces, services or dependency-injection machinery without a real replacement or ownership boundary.

The current React application remains one deployable, client-side application. Atlas, Weather and Traverse are conceptual boundaries inside it; separate apps or a speculative package hierarchy are not justified yet.

The intended dependency direction is:

```text
small, genuinely shared primitives
             |
           Atlas
          /     \
     Weather   Traverse
                  ^
                  |
       narrow Weather sampling contract
```

- Atlas must not depend on Weather or Traverse.
- Weather may consume Atlas world/rendering contracts.
- Traverse may consume Atlas terrain/world contracts.
- Traverse may consume a narrow Weather sampling contract for conditions along a journey through space and time.
- Weather must not depend on Traverse scheduling or UI models merely for convenience.
- Shared/Core code is appropriate only for stable concepts with multiple real consumers. It is not a home for miscellaneous utilities.
- Provider acquisition, canonical data, inference and rendering should remain separable where the implementation presents a real replacement boundary.

## Source-of-truth hierarchy

```text
source observation
  -> canonical Meridian representation
  -> inference / reconstruction
  -> renderer-specific asset
  -> pixels / user experience
```

Each product and report must retain its role:

- **Observed**: values supplied by an identified source observation.
- **Derived**: deterministic quantities calculated from observations or canonical data.
- **Inferred**: uncertain interpretation supported by evidence.
- **Reconstructed**: plausible spatial or visual detail generated below the information resolution of the evidence.
- **Rendered**: platform-specific assets and pixels.

Missing is not zero. Inferred or reconstructed values must not be relabelled as measurement. A renderer may be replaced without changing the canonical world representation or its provenance.

## Experiments and promoted infrastructure

Experiments retain their original names, configs, hashes and output identities. Code becomes shared infrastructure only after it has a continuing role beyond the experiment that created it. Promotion should give that code a role-based name and an explicit interface; it must not rewrite the historical experiment record.

The current `scripts/earth_lab` and `meridian-data/earth-lab` paths remain in place until a later migration. "Earth Lab" is historical terminology, not the intended permanent name for shared Atlas infrastructure.

## Repository and storage boundaries

`project-meridian` contains implementation, lightweight configuration, tests and documentation required to build Meridian. Large downloaded observations, deterministic products, experiment outputs and caches remain outside Git.

Python tooling resolves two external roots through `scripts/meridian_paths.py`:

- `MERIDIAN_DATA_ROOT`: non-private source, derived and generated world data.
- `MERIDIAN_PRIVATE_ROOT`: personal/user research such as private activities, GPX files and exports.

The development defaults remain sibling directories named `meridian-data` and `meridian-private`. Environment overrides must be absolute and outside the Git repository. The private directory is optional until a tool explicitly requires it. These variables are Python/tooling configuration; they are not `VITE_` variables and must not be exposed to the browser bundle.

Historical configs using `../meridian-data/...` remain valid. The shared resolver can map that legacy prefix onto a configured data root without editing the frozen config. Existing historical entry points retain their current behaviour until they are deliberately adopted by a later migration.

Inspect or validate the resolved roots without touching data:

```powershell
$env:MERIDIAN_DATA_ROOT = 'D:\Meridian\data'
$env:MERIDIAN_PRIVATE_ROOT = 'D:\Meridian\private'
py scripts\meridian_paths.py --require-data
```
### Future data classification

- **SOURCE**: an externally acquired observation retained with licence, acquisition and native-resolution provenance.
- **CANONICAL**: Meridian's stable, documented representation of relevant source information. Canonical products are derived but have stronger identity and compatibility guarantees than ordinary intermediates.
- **DERIVED**: reproducible products calculated from source or canonical data.
- **EXPERIMENT**: outputs tied to a bounded historical investigation, including its report and deterministic identity.
- **CACHE**: reacquirable or recomputable performance state.
- **SCRATCH**: disposable temporary work with no recovery promise.
- **PRIVATE**: personal or user data that must not enter public/world-data stores or Git.
- **REFERENCE RENDERER SOURCE**: lightweight configuration plus unique authored or calibrated state required to recover a renderer.
- **REFERENCE RENDERER GENERATED STATE**: imported assets, deployed scripts, caches and build products reproducible from repository code and external data.

The later data migration should classify first and move second. Directory names such as `sources`, `derived`, `experiments`, `cache` and `scratch` are candidates, not a requirement to erase useful history.

## Tryfan Unreal reference renderer

The current project remains externally located at `meridian-data/earth-lab/tryfan-004/unreal-project/TryfanLab004`. It began in Lab 004 but now serves later experiments and is conceptually the **Tryfan Reference Renderer**.

### Current file classification

**Lightweight source/configuration**

- `TryfanLab004.uproject`: UE 5.8 association and required editor plugins.
- `Config/DefaultEngine.ini`: project settings, but its Android file-server token must be removed or regenerated before public versioning.
- `Config/DefaultInput.ini`: mostly engine-generated input defaults; retain only after confirming that its non-default FOV/input settings are intentional.
- Repository-owned Unreal Python under `scripts/earth_lab`: canonical source. `Content/Python` is a deployed copy.

**Unique calibrated binary state**

- `Content/Tryfan_Lab004.umap` (72,016,185 bytes): the canonical saved scene, including the validated Landscape, fixed camera, actor/component state and material bindings. No external-actor/World Partition packages are present.
- The newer autosave remains recovery evidence, not canonical source.

**Reproducible imported/generated assets**

- `MeridianLab004/Reference/T_TonyEdwards_2009.uasset` and `M_TonyEdwards_Overlay.uasset` are recreated by the photo-overlay script from the separately preserved reference image and configuration.
- `MeridianLab009` material and two control textures are recreated by the Lab 009 reconstruction and Unreal setup scripts.
- `Content/Python` files are byte-verifiable deployments of repository source.

**Transient state**

- `Intermediate`, `DerivedDataCache`, Python `__pycache__`, logs, crashes, shader debug output and routine `Saved` state.

### Recommended durable versioning

Use the existing `project-meridian` repository with narrowly scoped Git LFS, rather than creating a separate repository. The renderer is coupled to Meridian's Atlas contracts and presently has only one irreplaceable large asset, so a second repository would add coordination without a real ownership boundary.

The later, explicitly approved migration should place a source-controlled renderer under a role-based path such as:

```text
renderers/unreal/tryfan-reference/
  TryfanReferenceRenderer.uproject
  Config/
  Content/Tryfan_Reference.umap       # Git LFS
  renderer-manifest.json
  README.md
```

The manifest should pin the engine version, plugins, canonical map hash, expected external data identities, fixed camera validation and regeneration commands. Generated textures/materials and deployed Python should remain reproducible rather than being committed by default.

Git LFS 3.2.0 is installed locally but this repository has no LFS attributes yet. Adding LFS changes clone/push requirements and consumes remote LFS storage. The `.umap`, project/config copy and Unreal-aware rename therefore require an explicit decision before execution. Project, map, actor and asset renames must be performed through Unreal where necessary to preserve package references; historical Lab 004 names remain in experiment provenance.
