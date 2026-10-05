# Atlas spatial terrain reconciliation: research/design review

2026-10-05. Baseline `3e54ca8e195c5a4669f5f9d1c909cc83c4d6830e`.
Status: completed bounded research/design review; no reconciliation implemented.

**Conclusion:** keep regional LOD and spatial reconciliation separate. The next
justified test is whether a supported seam corridor exists around the protected
interior, not another blend. Existing overlap permits that test but does not
establish a valid join. Production remains unchanged.

## Frozen problem and scope

Atlas has two individually reproducible but independently estimated elevation
surfaces: a Swiss DTM pyramid preserving LN02 and a Copernicus edited DSM pyramid
preserving EGM2008. Swiss-derived parents reduce the protected-interior z13→14
change from 39.82 to 0.71 m RMS without changing fine Swiss terrain. Internal
regional refinement is therefore substantially understood; source handoff is not.

The remaining question is where, and under what physical/support assumptions,
these independent surfaces can meet without a false wall or an unjustified
deformation of authoritative regional terrain. A smooth picture alone does not
answer which elevation Atlas should represent.

Keep seven components separate:

| Component | Established Meridian evidence; remaining uncertainty |
| --- | --- |
| Internal regional LOD | Same-family parents substantially reduce the source-change jump; normal coarse aggregation still changes extrema. |
| Height reference | LN02 and EGM2008 differ. Retained diagnostic adjustment +0.166…+0.752 m; combined accuracy unresolved. This does not explain tens to >100 m surface differences. |
| Registration | Retained Copernicus signature (−0.85,+2.89) m is sector-unstable; no accepted correction. |
| Surface meaning | Swiss DTM versus edited Copernicus DSM, with different measurement/processing footprints. |
| Epoch | Different acquisition histories; cell epochs unknown; ice/change effects not apportioned. |
| Resolution/generalisation | Fine ridges, cliffs and valleys can disagree because estimates represent different spatial support. Delivery zoom is not accuracy. |
| Spatial handoff | Same-level source walls remain; complete-tile frontiers change with level and differ from actual native coverage. |

The 1.5 km protected interior and 10×10 km Swiss support remain fixed. Candidate
stable support is uneven: 7.003 km² overall, NW/NE/SW/SE counts
1960/6379/2567/299. It is not a validated perimeter correction mask or seamline.
No new blend, fitted correction, transformation, terrain product or renderer
change is authorized in this review. Retained documentation and lightweight
records are sufficient initially; external terrain files need not be accessed.

**MERIDIAN EVIDENCE (M):** identified retained experiments, not independent Earth
accuracy. **EXTERNAL EVIDENCE (E):** reviewed primary methods/authoritative tools.
**RESEARCH HYPOTHESES / DIRECTIONS (H):** applicability or future tests, not adopted
production architecture.

## Retained products and controls (M)

This review uses repository records only. No canonical terrain file was opened,
acquired, regenerated or transformed. Product identities below are retained
identities, not newly verified external-file hashes.

| Product | Immutable identity and relevant contract |
| --- | --- |
| Swiss support product | `1a44a0644de1bde73a3ba84d1b761dc0aa17d48cc971e5f6b5d2c14fb329d7ea`; 100 swissALTI3D 2024 inputs; LV95 10×10 km, 0.5 m distributed grid, DTM/LN02; XYZ/Web Mercator Terrarium z12–18. |
| Common product | `8f002dcbdeceb6aa37cc9eeef9f2d2060193b1eff7922ddb1d0535a6b8030da2`; six frozen 2021 public GLO-30 assets, exact sub-release unknown; edited DSM/EGM2008; Terrarium z8–13, higher detail is overzoom. |
| Regional parents | `b92c9a3dfa05a87e4fcce4a6e6638efd2d9ab8e86537f52833ff1ed6def78672`; separate unencoded Swiss z14 sum/count basis aggregated through z10; complete, partial and absent support distinguished; original fine terrain unchanged. |

Primary Meridian records: [direct prototype](riffelhorn-regional-terrain-prototype.md),
[Swiss/AWS reconciliation](riffelhorn-terrain-reconciliation.md),
[metadata architecture](terrain-source-product-architecture.md),
[Swiss support](riffelhorn-swiss-support-product.md),
[reference assessment](global-reference-assessment.md),
[common product](copernicus-common-product.md),
[first hierarchy](terrain-hierarchy-prototype.md) and
[regional parents](regional-parent-diagnostic.md). These retain exact reproduction
commands, hashes and external-product locations.

The parent diagnostic changes an interior LOD problem into an explicit spatial
problem, not a solved join. At the same 705 protected points, Swiss z13→z14 RMS is
0.7107 m versus common z13→Swiss z14 39.8249 m. Fine Swiss changes are zero. The
first delivered unrelated-source jump moves to common z11→Swiss z12, RMS 39.7680 m.
Full-cell Swiss/common RMS decreases only from 20.010 m at z14 to 18.800 m at z10;
protected-point RMS remains 38.373 m at z10. These populations differ from the
stable-terrain assessment: do not compare them as equivalent accuracy metrics.

Complete Swiss tile counts are 25/4/1/0/0 at z14/z13/z12/z11/z10. Growing tile envelopes
are not growing observational coverage. At z10, 93.1% of the diagnostic envelope
is unsupported. A partial observed-subset mean is not a valid full-cell height.
Same-level edges still reach 48.40/61.77 m at z12/z13; fine walls persist. The renderer
can load different geometry and relief levels and reuse parents, so camera zoom
alone cannot specify a source handoff.

## Method findings (E) and applicability (H)

### Correct reference and registration errors before attributing residuals

[Nuth & Kääb (2011)](https://tc.copernicus.org/articles/5/271/2011/) distinguish
three-dimensional shifts, elevation-dependent bias and sensor-specific effects.
A slope/aspect signature can diagnose displacement, but not every residual is
registration. [xDEM's documented practice](https://xdem.readthedocs.io/en/stable/coregistration.html)
separates affine registration from bias correction and uses static-terrain inliers.
Flat terrain poorly constrains slope/aspect translation; ice, vegetation and
changing ground must be considered separately.

[Li et al. (2023)](https://tc.copernicus.org/articles/17/5299/2023/) show why good
training residuals are insufficient: spatially restricted stable terrain can
support a fit that extrapolates badly onto ice; elevation-dependent fits can
misbehave outside their training range. Extra rotation, scale or spatial degrees
of freedom require evidence, not simply a lower RMS.

**H — Atlas consequence:** registration precedes fusion when a repeatable,
physically interpretable registration error has been demonstrated. It is not a
mandatory correction when no such error is established. The retained approximately
(−0.85,+2.89) m Copernicus diagnostic varies by sector and can partly reflect
DSM/DTM smoothing. No correction is accepted. A future acceptance would require
spatially distributed stable support, held-out sectors, plausible magnitude and
residual structure consistent with the proposed error model. Do not fit local
sectors into agreement merely to make a seam.

### Height-system harmonisation is not empirical bias fitting

[Swisstopo's LHN95 description](https://www.swisstopo.admin.ch/en/national-height-network-lhn95)
distinguishes LN02's older levelled heights from rigorous orthometric LHN95.
[Its transformation guidance](https://www.swisstopo.admin.ch/en/transformations-in-height)
describes an approximate relationship between the systems, not an exact universal
offset. The [English REFRAME documentation](https://www.swisstopo.admin.ch/en/rest-api-geoservices-reframe-web)
quotes decimetric HTRANS accuracy and 1–3 cm for CHGeo2004; these are component
figures, not a combined LN02→EGM2008 error budget.

The [Swiss PROJ grid record](https://cdn.proj.org/ch_swisstopo_README.txt) documents
separate CHGeo2004 grids linking LN02 and LHN95 to ETRS89 ellipsoidal heights,
with CC0 distribution. The LN02 variant already incorporates that system's
relationship; applying HTRANS as well would need a different, explicitly defined
chain. The [NGA grid record](https://cdn.proj.org/us_nga_README.txt) documents the
public-domain EGM2008 2.5-minute grid and reproducible conversion from its model
distribution.

**H — appropriate chain to verify before numerical fusion:** LN02→ETRS89
ellipsoidal heights using the corresponding Swiss grid; explicit horizontal/frame
handling between the grid domains and WGS84; ellipsoidal heights→EGM2008 physical
heights using the inverse applicable NGA model. Preserve operation identities,
grid hashes, interpolation and frame assumptions. EPSG:2056 alone says nothing
about the vertical reference. The retained network-disabled diagnostic exercised
this kind of route, but reported combined accuracy as unknown. Round-trip closure
is not external accuracy. No new transformation was performed here.

**Decision:** a declared common height frame is a prerequisite for claiming
geodetic numerical fusion. Native-reference switching remains possible as a
clearly heterogeneous diagnostic, not an implicitly harmonised surface. The
retained +0.166…+0.752 m adjustment is too small to explain the major walls. Datum
handling is necessary accounting; it does not authorize correcting the remaining
tens-of-metres disagreement as datum error.

### Priority, weighting and transition zones are different operations

[GDAL VRT mosaicking](https://gdal.org/en/stable/programs/gdalbuildvrt.html) can
select the last valid overlapping source with nodata fallback. Selection is not
edge reconciliation; assigning a CRS is not reprojecting. Modern documented
pixel functions should not be assumed available in Meridian's retained GDAL 3.9.3.
[GDAL warping](https://gdal.org/en/stable/programs/gdalwarp.html) controls sampling,
nodata and vertical shifts: a recognised compound CRS can trigger height changes.
Future horizontal-only preparation must verify that no unintended vertical
operation occurs.

[Ames Stereo Pipeline's dem_mosaic](https://stereopipeline.readthedocs.io/en/stable/tools/dem_mosaic.html)
distinguishes default overlap blending from priority blending. Priority mode
retains the preferred source except in a declared boundary band; external weight
maps and saved weights permit explicit contributions. Hole filling and blur are
additional operations, not evidence of source support. This is useful executable
prior art, but its controls do not determine scientifically appropriate widths.

[Petrasova et al. (2017)](https://link.springer.com/article/10.1186/s40965-017-0019-2)
address local DEM updates, including constant/adaptive distance weighting. Their
inputs are co-registered and aligned; boundary discrepancies and terrain govern
width. They warn about unrealistic features when discrepancies reflect other
errors. Their agricultural/UAS examples do not validate Alpine DSM/DTM fusion.
The associated [GRASS r.patch.smooth manual](https://grass.osgeo.org/grass-stable/manuals/addons/r.patch.smooth.html)
requires compatible grids and describes experimental blend-mask behavior.

**Physical meaning:** weighted elevations are a derived estimate between sources,
not new observations. In a blend h=w·Swiss+(1−w)·common, the gradient contains
`(Swiss−common)·∇w`. Thus a changing weight can introduce a slope or landform even
when both input surfaces are reasonable. Smooth weights reduce a step; they do
not prove a plausible terrain shape or preserve extrema.

### A regional-preserving alternative exists, with important assumptions

[USGS adaptive topobathymetric fusion](https://www.usgs.gov/software/adaptive-topobathymetric-fusion-software-version-10),
and its [versioned implementation guide](https://code.usgs.gov/spcmsc/DEMFusion/-/tree/v1.0.1),
adapt distance-weighted fusion so the newer survey remains intact and the older
surrounding surface changes. An allocated/smoothed outward proxy guides the
transition. The guide warns that adaptive widths can modify large areas and rely
on prior knowledge of coastal morphology.

**H:** this is closer prior art for protecting regional terrain than modifying
Swiss inward. It is nevertheless synthetic extrapolation outside the preferred
source, not additional Swiss support. Coastal assumptions do not establish
mountainous validity. Do not reproduce it automatically or call its output an
authoritative Swiss surface.

### Seam selection can precede any transition surface

[Chon, Kim & Lin (2010)](https://www.sciencedirect.com/science/article/abs/pii/S0924271609001154)
use local mismatch and global cost in orthophoto seam selection, including a
minimax formulation. The transferable idea is to examine connected routes and
bad bottlenecks rather than only average mismatch. This is **imagery** evidence,
not a validated elevation seam-cost model.

**H:** DEM candidate corridors may consider height disagreement, slopes/roughness,
stability, observation support and protected-terrain constraints. Low slope alone
is insufficient: valleys can be hydrologically important, and a low-slope site
can still have a large height offset. Ridges, channels and glaciers cannot be
assigned universal good/bad costs without purpose and evidence. No reviewed
source establishes a universal Alpine seam rule or a guaranteed closed low-cost
route around this protected interior.

### Frequency and constrained fusion have a stronger modelling burden

[Karkee, Steward & Aziz (2008)](https://www.sciencedirect.com/science/article/pii/S1537511008002493)
combine frequency components of registered ASTER/SRTM after correcting their
specific errors. The source/error bands and cutoff are empirical, not a universal
rule that global low frequencies are correct and regional high frequencies are
detail. A broad Swiss/Copernicus difference is not proof that Swiss broad shape
should be replaced.

[Burt & Adelson's multiresolution image spline (1983)](https://ai.stanford.edu/~kosecka/burt-adelson-spline83.pdf)
uses wider transitions for coarser frequency bands while retaining finer image
features. That is established image blending, not evidence that broad terrain
deformation is correct. Applied to elevation, multiband blending still creates a
derived surface and requires explicit regional-preservation constraints.

[Gradient Terrain Authoring (Guérin et al., 2022)](https://diglib.eg.org/items/aae91029-ed2e-417f-9f5f-843beec71fea)
uses gradient-domain/Poisson constraints to create terrain. Such fitting can
enforce continuity and prescribed boundaries; its demonstrated purpose is terrain
authoring, not accuracy-preserving observation fusion. In Atlas a fitted collar
would need declared constraints, modifications and synthetic provenance. A
constrained solution's smoothness would not establish Earth elevations.

[Roth et al. (2002)](https://www.isprs.org/proceedings/xxxiv/part4/pdfpapers/210.pdf)
describe multi-sensor fusion using registration, corresponding grids, quality
models and weighted estimates. [Bagheri et al.](https://elib.dlr.de/116067/1/1810.11415-1.pdf)
derive local error weights from training/reference evidence. Neither justifies
inventing confidence from pixel size. The [TanDEM-X specification](https://tandemx-science.dlr.de/pdfs/TD-GS-PS-0021_DEM-Product-Specification_v3.2.pdf)
also illustrates why a random-error layer is incomplete: systematic offsets are
not covered by its height-error map.

### Production practice preserves different product roles

[USGS 3DEP](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services?qt-science_support_page_related_con=0)
distinguishes project-derived elevation from seamless/common-reference products
and dynamic multiresolution delivery. Its source-quality and reference policies
are prerequisites, not proof that any two DEMs can be blended safely.

[ArcticDEM's current mosaic description](https://www.pgc.umn.edu/data/arcticdem/)
retains time-dependent strips separately from median mosaics, uses dated source
information and water policies, and describes mosaic adjustment toward Copernicus
to reduce tile discrepancies. That production choice is a declared derived
product policy; it does not establish permission to modify Meridian's protected
Swiss terrain. Its height conventions also distinguish source data from viewers.

[Datla & Mohan (2021)](https://people.iith.ac.in/ckm/assets/pdfs/jour10.pdf)
correct systematic Cartosat errors before ordered feather mosaicking. Their
hierarchical ordering is acquisition/mosaic organisation, not terrain LOD.
Across these examples, immutable source observations, corrected/derived mosaics
and display products must remain distinguishable. Epoch changes are not solved
by numerical registration.

### Nested terrain continuity is not cross-source truth

[Geometry Clipmaps (Losasso & Hoppe, 2004)](https://hhoppe.com/geomclipmap.pdf)
uses a prefiltered hierarchy of one surface with fine/coarse transition regions.
The [GPU implementation](https://developer.nvidia.com/gpugems/gpugems2/part-i-geometric-complexity/chapter-2-terrain-rendering-using-gpu-based-geometry)
describes morphing and level activation. These methods assume related levels;
they do not reconcile unrelated DTM/DSM estimates. Skirts, T-junction repair and
geomorphs manage rendering continuity rather than establish elevation validity.

**M/H:** the Swiss-parent result independently supports a regional pyramid. Actual
MapLibre behavior remains the retained single-raster-dem stream with loaded-parent
reuse, not a new clipmap renderer. An offline derived raster-dem can use the
existing path; arbitrary skirts/morph controls or simultaneous source fusion
cannot be inferred from that compatibility. Data reconciliation, representation
construction and rendering continuity should be evaluated separately.

## Reinterpreting Meridian's failed feathering (M + E interpretation)

The old controls used Swiss versus AWS, not the better-characterized Copernicus
reference. Hard substitution was unacceptable. The fixed 250 m control reduced
ideal sampled edge jumps from 111.52 to 1.32 m, but altered its collar by up to
+130.64/−59.12 m. It preserved deeper interior, not all authoritative terrain.
The adaptive 3° diagnostic reduced the jump to 1.24 m while modifying ≥500 m
interior by 37.953 m RMS and producing a depression/channel artifact. Diagnostic
width p95 was 2.24 km, beyond the crop's 1 km inward support. These ideal control
metrics differ from the original 70.17 m one-metre composed jump.

Feathering is therefore not universally disproved. What failed was the assumption
that smoothing an arbitrary crop join made a defensible representation. Missing
prerequisites included a justified common reference, accepted registration/error
model, supported transition geometry and enough unconstrained overlap. A wider
collar could hide more discrepancy while harming more terrain. Co-registration
or datum handling cannot be presumed to cure broad geomorphic differences.
The weight-gradient term explains why the adaptive control could create a new
landform; it does not identify the original source errors.

The 10 km asset remedies shortage of raw support, not these other prerequisites.
Its stable candidate population remains heavily concentrated in NE, sparse in
SE, and affected by glacier/change exclusions. Stable Swiss-minus-Copernicus
median −0.60/NMAD 1.78/RMS 5.93 m is substantially better than AWS, yet includes
a narrow-ridge outlier+116.78 m. Good central or pooled statistics cannot certify
a perimeter seam. Stable fitting support and suitable visible seam terrain are
related but different concepts.

## Reduced candidate matrix

All rows are method families, **not adopted algorithms**. References and their
limits above establish E; proposed Atlas use remains H.

| Family | Meaning and regional preservation | Preconditions / mountain risks | Provenance, pyramid/MapLibre fit, complexity | Decision |
| --- | --- | --- | --- | --- |
| Priority selection with support-constrained seam | Select observations without averaging; pure Swiss protected interior. A hard seam is acceptable only if actual boundary mismatch is acceptable. | Common-frame accounting; compatible local support; defensible corridor. No inherent protection against tens-of-metres jumps, glaciers or ridge error. | Pure contributors remain identifiable. Must assess each level's valid frontier; offline selection fits raster-dem. Moderate corridor analysis. | Best next **feasibility question**, not a proven solution. |
| Priority-preserving narrow transition; possibly background-only outward | Derived estimate in a declared collar, preserving Swiss interior. May alter common terrain outside it. | Seam/overlap first; documented frame/error model; real constraints on gradients and widths. Outward proxy is extrapolation; large disagreement can invent terrain. | Source weights/method/support must survive; reproduce parents from the derived representation. Raster-dem compatible; medium/high modelling burden. | Conditional later control only if corridor evidence warrants it. |
| Robust registration / low-frequency correction | Correct only demonstrated measurement/reference error; not a generic visual transition. Regional elevations change if it is the correction target. | Distributed stable overlap; held-out spatial validation; plausible error and transformation. Local fitting may extrapolate into ice or erase real shape. | Operation, target, uncertainty and revisions retained. Preprocessing compatible; scientific validation dominates complexity. | No current evidence justifies a new correction. |
| Frequency-separated / uncertainty-weighted fusion | Combines complementary signals or estimates; generally changes both sources and extrema. | Valid frequency/error separation or calibrated uncertainties; common frame and registration; temporal/surface comparability. Missing local error model. | Contributions may require more than scalar weights; parent chain must derive from output. Offline compatible; high evidential burden. | Not the next bounded experiment. |
| Constrained gradient/Poisson surface or render-only morph/skirt | Fitting creates a synthetic surface; rendering changes appearance/mesh without resolving elevation truth. | Boundary/gradient constraints or genuinely related LODs. Smooth solutions may deform landforms; crack hiding may hide wrong elevations. | Distinguish process lineage from convex contribution weights. Custom rendering not demonstrated in current stack; high complexity. | Do not use as a scientific seam cure. |

None handles temporal change merely by averaging it. None supplies missing Swiss
observations. No candidate's numerical weights are automatically confidence.

## Requirements and missing evidence

| Requirement | Evidence and present status |
| --- | --- |
| Related regional parents plus per-level full/partial support | M parent diagnostic; demonstrated. Same-level handoff must still be assessed. |
| Source surface/epoch identity | M metadata architecture; DSM/DTM and unknown per-cell epochs preserved. Vegetation, ice and temporal errors not apportioned. |
| Declared common-height operation for numerical fusion | E Swiss/NGA practice; route exists, combined accuracy/frame assumptions still need explicit acceptance. Native diagnostic remains heterogeneous. |
| Registration acceptance, not compulsory correction | E Nuth/Kääb and held-out extrapolation evidence; M sector instability. No accepted shift. |
| Protected interior independent of source and delivery boundary | M crop/feathering/parent results. Fixed 1.5 km interior; actual source support and whole-tile delivery frontiers differ. |
| Spatially distributed stable/reference support | E co-registration; M7.003 km² candidate support is uneven. Not a validated closed perimeter or uncertainty model. |
| Explicit seam or transition purpose/constraints | M false walls; E priority mosaicking; H corridor feasibility untested. Hydrological or structural constraints cannot be invented. |
| Contributor and processing identity | M existing masks/model; E weighted mosaics. Preserve pure versus derived terrain, support, original revisions, transformation and any weight/correction fields. |
| Local uncertainty if claiming uncertainty-weighted fusion | E multi-sensor/HEM practice. Currently absent; advertised accuracy/grid spacing is insufficient. Not required just to test a seam corridor. |
| Independent renderer assessment | M loaded geometry/relief levels differ; E clipmaps. A scientifically acceptable representation may still need LOD continuity work. |

The existing Atlas metadata model can reference these concepts through source
quality, vertical semantics, lineage, spatial support and contribution resources.
No schema extension is justified now. Seam costs, contributor weights and accepted
error uncertainty must remain distinct. Source and product metadata do not belong
in Weather, Traverse or IGOR configuration. No production import was added.

## Rejected shortcuts

- One fitted offset for spatially variable disagreement; fitted bias called a datum.
- Arbitrary fixed/adaptive feather widths as a correctness criterion, or growing
  them until screenshots look smooth.
- Correcting protected Swiss terrain merely to agree with a lower-quality product.
- Assuming all broad disagreement is Swiss bias and only high-frequency Swiss
  information deserves preservation.
- Sector-by-sector fitting accepted solely on lower RMS; extrapolation from sparse
  stable terrain into glaciers without validation.
- A low-slope seam automatically considered safe, or one favorable boundary patch
  considered proof of a closed regional join.
- Partial parents delivered as fully supported terrain; tile envelopes called
  source coverage; high delivery zoom called accuracy.
- Skirts or morphing described as terrain reconciliation; common parents described
  as compatible with unrelated children because they load successfully.

## Single smallest next experiment — not performed (H)

**A support-constrained, same-level seam-corridor feasibility diagnostic, with no
height modification.** Replace the question “which blend?” with “does the retained
support contain a physically plausible place for a bounded source handoff?”

Use existing retained difference/stable-support fields and parent support records
to test whether a connected candidate corridor can surround the protected interior
within legitimate Swiss support. Include west, south and corners, not only the
favorable northern/eastern sectors. Distinguish actual source coverage from
complete-tile frontiers at relevant levels. Assess disagreement, slope/roughness,
change exclusions and support in their physical units; examine bottlenecks and
sensitivity rather than hiding bad segments in one weighted score. Compare raw
native-reference residuals with the **already retained** common-frame diagnostic
as a sensitivity check; neither becomes an accepted transformation by default.

The output is maps, candidate corridors and a documented feasibility/failure
assessment, not a DEM, fitted surface, blend or production seamline. A stable-fit
mask is not automatically a seam mask: excluded terrain remains visible evidence
and may block a defensible route. A missing connected route is a useful negative
result. Only a favorable result would justify selecting one narrow transition
control with a separate height-frame policy and protected-interior constraint.

**Support conclusion:** 10×10 km with ≥3.5 km surrounding source support is enough
to attempt this diagnostic without another acquisition. It is **not established**
as sufficient for distributed co-registration, a physically justified correction
surface, or a complete transition collar. Sparse SE stable support, glaciers and
level-dependent delivery edges may defeat the attempt. There is no evidence here
for extending acquisition now or for adopting a general hierarchy contract.

No new numerical diagnostic was needed in this review: retained measurements
already establish why method selection must precede another terrain modification.

## Research discipline, reproduction and production status

This is a synthesis of established methods and Meridian's negative results, not a
new fusion algorithm. Priority mosaicking, adaptive feathering, uncertainty fusion,
co-registration and LOD morphing are external prior art. The improved same-family
LOD result is Meridian evidence. Applying a corridor strategy to these controlled
products is an untested direction. The closed 012A–G programme remains closed.

Production remains AWS visual terrain and independently configured AWS analytical
elevation at z15/256 pixels. IGOR remains map-anchored 315° with the strengthened
curve; exaggeration 1.45. Weather, Traverse, satellite, projection/lifecycle and
startup dependencies are unchanged. No evaluation server or large external data
was used. This report changes research/navigation documentation only.

To reproduce this **review**, inspect the frozen records (product-generation
commands are linked above; do not run them merely to reread evidence):

```powershell
git show 3e54ca8:docs/atlas/regional-parent-diagnostic.md
git show 3e54ca8:docs/atlas/global-reference-assessment.md
git show 3e54ca8:docs/atlas/riffelhorn-terrain-reconciliation.md
git diff 3e54ca8 -- src scripts package.json package-lock.json
node --test scripts/atlas/test_terrain_policies.mjs scripts/atlas/test_terrain_metadata.mjs scripts/atlas/test_global_reference_metadata.mjs scripts/atlas/test_terrain_hierarchy.mjs
git diff --check
```

No terrain-generation command is added because no product was generated. Review
validation checks local document links/anchors, method-reference retrieval scope,
retained numerical claims and absence of implementation changes. Focused existing
terrain tests are a boundary regression check; documentation changes do not
require another application build, browser run or external-data checksum pass.

**Validation results:** all 33 focused Node terrain-policy/model/hierarchy tests
passed. All 132 local links/anchors in the five changed documents resolve; UTF-8
and `git diff --check` checks pass. Retained identities and numerical claims were
cross-checked against the predecessor reports. The implementation/configuration
diff from the baseline is empty. No lint, TypeScript, full application suite,
build or browser evaluation was rerun because no executable code changed.

## Reference ledger and review limits (E)

Accessed 2026-10-05. Links in method sections are the canonical references. “Full”
means retrieved article/document text was inspected, not every cited reference
inside it. Indexed abstracts/guides support only the stated bounded claims;
blocked full-text retrieval is not represented as full verification.

| Reference | Retrieval scope / relevance |
| --- | --- |
| Nuth & Kääb 2011, DOI 10.5194/tc-5-271-2011 | Publisher article abstract; framework, supplemented by official xDEM methods. |
| Li et al. 2023, DOI 10.5194/tc-17-5299-2023 | Full publisher text; spatial/elevation extrapolation risks and registration distinctions. |
| xDEM coregistration | Full official documentation; inliers, affine versus bias methods. |
| Swisstopo LHN95 / height transformations / REFRAME | Official product/API text; system differences and component accuracy. English/German accuracy wording differs; no combined chain accuracy inferred. |
| PROJ Swiss and NGA grid READMEs | Full distribution records; references, transformations, licensing and reproduction. |
| GDAL VRT / warp | Full current manuals; selection, nodata, sampling and possible vertical operations; version caveat retained. |
| ASP dem_mosaic | Full stable manual; priority, weights and support-changing operations. |
| Petrasova et al. 2017, DOI 10.1186/s40965-017-0019-2 | Full publisher text; local-update weighting, assumptions and failure modes. |
| GRASS r.patch.smooth | Full current addon manual; compatible grids and experimental mask caveat. |
| USGS Seymour 2023, DOI 10.5066/P9POPM96 / DEMFusion v1.0.1 | Official release page plus indexed versioned guide text; direct guide retrieval unavailable. No code execution or Alpine validation claimed. |
| Chon et al. 2010, DOI 10.1016/j.isprsjprs.2009.09.001 | Indexed publisher abstract; imagery seam minimax principle only. |
| Karkee et al. 2008, DOI 10.1016/j.biosystemseng.2008.09.010 | Indexed publisher abstract/method excerpt; dataset-specific frequency separation. |
| Burt & Adelson 1983 | Full paper; image multiband blending, explicitly an elevation analogy. |
| Guérin et al. 2022, DOI 10.1111/cgf.14460 | Indexed Eurographics record and author summary/code description; publisher page blocked. Terrain-authoring purpose, not a validated fusion method. |
| Roth et al. 2002, ISPRS XXXIV/4 | Full proceedings PDF; registered multisensor fusion and quality models. |
| Bagheri et al., author manuscript | Full DLR PDF; error-weight learning from reference evidence, not invented confidence. |
| TanDEM-X product specification v3.2 | Indexed official specification excerpts; random-error-map limitations. Full PDF retrieval unavailable. |
| USGS 3DEP products/services | Full official page; canonical projects versus seamless/common-reference delivery. |
| PGC ArcticDEM | Full current official description; strip/mosaic policy and source/viewer semantics. |
| Datla & Mohan 2021, DOI 10.1016/j.cageo.2020.104619 | Full author-hosted paper; corrected, ordered DEM mosaicking. |
| Losasso & Hoppe 2004 / GPU Gems 2 terrain chapter | Full author paper and official implementation chapter; related-surface LOD transitions. |

This bounded review does not establish universal Alpine seam costs, local error
covariance, exact per-cell acquisition epochs, a validated full perimeter or a
combined Swiss→EGM2008 accuracy. Those limitations are prerequisites to decide,
not permission to substitute intuitive smoothing.
