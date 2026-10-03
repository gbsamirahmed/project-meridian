# Terrain representation: literature and research record

Reviewed 2026-10-03. Companion to the [research map](../atlas-research-map.md)
and [final Meridian synthesis](../../earth-lab/atlas-terrain-representation-synthesis.md).
This is a representative cross-disciplinary review, not an exhaustive systematic
review or an implementation plan. No paper, model or dataset was integrated.

## Evidence and source status

**E — external evidence** describes what the cited publication/document establishes.
**M — Meridian evidence** refers to linked experiments only. **H — direction**
identifies an untested local application, including each Meridian status below.
External maturity never implies local demonstration. A technique's output is not
necessarily an independent observation or ground truth.

Sources below are primary papers, author/institution records, official standards,
mapping-agency documentation or author-maintained implementations. Publisher/author
abstracts were inspected for the Chen review, Song–Qin 2022/2024, Casella–Franzini
and Jenny papers; their numerical performance has not been independently reproduced.
Full papers were consulted for Richter, Santini–Palombo, James–Robson, Olbedo,
Waechter, Debevec, Wood and Losasso–Hoppe. The Soenen citation was checked against
the author's publication list; forest-specific scope is clear, but the full paper
was not accessible in this review. Doneus's publisher page was rate-limited;
the openness definitions here are also supported by the maintained RVT technical
documentation, not a claim to have reproduced that paper. Living project/agency
pages were checked on the review date. Some publisher retrievals were unavailable;
author copies and technical
documentation are identified explicitly. Search snippets are discovery aids, not
evidence. DOI links can redirect or require access; URLs checked syntactically do
not guarantee future availability. Recheck releases, licences and applicability
before evaluation. Computational implications below are qualitative unless a source
provides a specific benchmark; they are not Meridian performance measurements.

## Topographic correction

**Problem/terminology (E):** a sloping surface receives different illumination from
a horizontal reference. Topographic correction seeks radiometrically comparable
reflectance, usually for remote-sensing analysis. It is not simply brightening a
rendered mountain and is not synonymous with atmospheric correction.

- **Chen, R.; Yin, G.; Zhao, W.; Yan, K.; Wu, S.; Hao, D.; Liu, G. (2023).**
  *Topographic Correction of Optical Remote Sensing Images in Mountainous Areas:
  A Systematic Review*, IEEE Geoscience and Remote Sensing Magazine 11(4), 125–145.
  [DOI](https://doi.org/10.1109/MGRS.2023.3311100),
  [institutional abstract/record](https://www.pnnl.gov/publications/topographic-correction-optical-remote-sensing-images-mountainous-areas-systematic).
  Reviews a large 1980–2022 literature. Much evaluated imagery is decametric or
  coarser; the review does not certify correction of sub-metre Alpine orthophotos.
- **Richter, R.; Kellenberger, T.; Kaufmann, H. (2009).** *Comparison of Topographic
  Correction Methods*, Remote Sensing 1(3), 184–196.
  [DOI](https://doi.org/10.3390/rs1030184),
  [full institutional copy](https://gfzpublic.gfz.de/pubman/item/item_238938_1/component/file_238937/13324.pdf).
  Cosine correction rescales using solar zenith and local incidence; near-grazing
  incidence makes division unstable. Minnaert uses a fitted power; C-correction
  introduces a regression-derived offset. Their comparisons do not identify one
  universally superior correction. Empirical parameters do not establish physical
  albedo, especially in deep shadow.
- **Soenen, S. A.; Peddle, D. R.; Coburn, C. A. (2005).** *SCS+C: A Modified
  Sun-Canopy-Sensor Topographic Correction in Forested Terrain*, IEEE TGRS 43(9),
  2149–2160. [DOI](https://doi.org/10.1109/TGRS.2005.852480),
  [author publication record](https://people.uleth.ca/~derek.peddle/).
  SCS and SCS+C address canopy/terrain illumination geometry. A forest-specific
  correction is not automatically the appropriate exposed-rock model.
- **Santini, F.; Palombo, A. (2019).** *Physically Based Approach for Combined
  Atmospheric and Topographic Corrections*, Remote Sensing 11(10), 1218.
  [DOI](https://doi.org/10.3390/rs11101218),
  [paper copy](https://pdfs.semanticscholar.org/5a76/dfd2eba31406bf9a4b0a8c93a7bdcdf77f55.pdf).
  A Lambertian radiative-transfer formulation separates direct/diffuse contributions
  and atmospheric/background effects using MODTRAN. Terrain geometry and shadow
  handling affect direct illumination. The model requires acquisition/sensor and
  atmospheric assumptions, not just RGB values; uniform atmosphere, diffuse-light
  approximations and reflectance assumptions constrain interpretation.

**Inputs → outputs:** georeferenced radiometry, DEM-derived slope/aspect, Sun/view
geometry and, for physical models, atmosphere and surrounding reflectance estimates
→ corrected radiance/reflectance and quality masks. Direct Sun, diffuse sky and
terrain-reflected illumination must not be conflated. Cast shadow removes direct
light but not all illumination. Recovering a signal with poor SNR remains uncertain.
Empirical per-band fits are relatively simple; transfer calculations, surrounding
terrain and shadow visibility add cost and metadata requirements.

**M:** [012G](../../earth-lab/riffelhorn-012g-projection-and-illumination.md) tested
one low-frequency luminance gain, **none of this physical correction family**.
Its HDR evidence prevents attributing final dark output solely to empty source.
**H / status: candidate for evaluation, untested by Meridian.** Determine whether
processed mosaics retain suitable radiometry and acquisition lineage before choosing
a correction. A method successful on vegetation or satellite imagery is not a
validated rock-face de-shadowing solution.

## Inverse rendering and albedo recovery

**Problem (E):** intrinsic-image decomposition separates reflectance from shading;
inverse rendering estimates scene properties through an image-formation model.
Albedo is illumination-independent only within declared reflectance assumptions.
A conceptual accounting model is:

```text
observed image = reflectance × illumination + other imaging effects
illumination  = visible direct Sun + diffuse sky + reflected surrounding light
```

This is not an exact inversion formula for an arbitrary processed orthophoto.

- **Song, S.; Qin, R. (2022).** *A Novel Intrinsic Image Decomposition Method to
  Recover Albedo for Aerial Images in Photogrammetry Processing*, ISPRS Annals
  V-2-2022, 23–30. [Paper/DOI](https://doi.org/10.5194/isprs-annals-V-2-2022-23-2022),
  [author manuscript](https://arxiv.org/abs/2204.04142).
  Uses aerial photogrammetric geometry in outdoor image decomposition; recovered
  appearance is intended to support relighting rather than retain photographed
  illumination as texture. It does not establish inversion from one unknown mosaic.
- **Song, S.; Qin, R. (2024).** *A General Albedo Recovery Approach for Aerial
  Photogrammetric Images through Inverse Rendering*, ISPRS Journal of Photogrammetry
  and Remote Sensing 218, 101–119.
  [DOI](https://doi.org/10.1016/j.isprsjprs.2024.09.001),
  [primary manuscript abstract](https://arxiv.org/abs/2409.03032).
  Extends aerial albedo recovery through an explicit inverse-rendering approach.
  Scene geometry and illumination assumptions supply constraints for appearance
  intended for relightable reconstructed scenes. Published scope is aerial
  photogrammetry, not proof of recoverable Riffelhorn cliff reflectance.

**Inputs → outputs:** posed aerial images, reconstructed geometry/normals,
radiometric and illumination assumptions → estimated reflectance/albedo and shading,
potentially relightable textures. Multiple observations help constrain ambiguity;
geometry/render iterations require more computation than a brightness filter.
Indirect light, sky, interreflection, specular/non-Lambertian surfaces, atmosphere,
geometry errors, uncertain shadows and camera processing remain practical limits.
Albedo/illumination scale ambiguity and missing observations must remain explicit.

**M:** 012F demonstrates photographed/rendered light conflict; 012G does not test
intrinsic decomposition or albedo recovery. **H / status: candidate, untested.**
The useful unknown is whether available radiometry/geometry/time lineage permits
a defensible decomposition, not whether a stronger contrast curve looks pleasing.

## Olbedo 2026

**Song, S.; Huang, D.; Deng, D.; Xiong, H.; Tang, Y.; Zhao, Y.; Qin, R. (2026).**
*Olbedo: An Albedo and Shading Aerial Dataset for Large-Scale Outdoor Environments*.
[Primary paper](https://arxiv.org/abs/2602.22025),
[full manuscript](https://arxiv.org/html/2602.22025v1),
[author project](https://gdaosu.github.io/olbedo/),
[implementation/release record](https://github.com/GDAOSU/Olbedo).

**E:** the February 2026 paper describes 5,664 UAV images across four outdoor
urban/park environments, with albedo/shading, depth, normals, Sun/sky components,
camera poses and confidence information. Photogrammetric geometry and inverse
rendering generate annotations; these are not direct ground-truth reflectance
measurements. The capture/processing assumptions include linear RAW-derived images.
Geometry/shadow uncertainty and global albedo-scale ambiguity remain relevant.
It supplies a concrete outdoor baseline, not an Alpine cliff validation.

The author repository advertises code, inference/model and dataset availability
(and identifies the work as CVPR 2026). It distinguishes dataset CC BY 4.0, Apache
2.0 code and separate model licences, including RAIL++-M / Adobe Research conditions.
Availability does not grant one universal licence across every component.

**Inputs → outputs:** its image/geometry supervision supports outdoor decomposition
and relighting evaluation; trained inference produces estimated components, not
new measurements. Training/inference and large multiview preparation have hardware
and storage implications; no Meridian cost was measured.
**H / status: external possible baseline, deferred.** No model/data download,
dependency or reproduction here. Future use would first verify release terms,
input-domain compatibility, confidence behaviour and out-of-domain Alpine failure
cases. **M:** it changes no conclusion of 012G.

## Acquisition-Sun and illumination reconstruction

**Reda, I.; Andreas, A. (2004).** *Solar Position Algorithm for Solar Radiation
Applications*, Solar Energy 76(5), 577–589.
[DOI](https://doi.org/10.1016/j.solener.2003.12.003),
[laboratory publication record](https://research-hub.nlr.gov/en/publications/solar-position-algorithm-for-solar-radiation-applications-2/).
**E:** solar ephemerides provide Sun direction from time/location using documented
astronomical calculations; this foundation should not be reinvented.

**H — conceptual method:** acquisition location/time + Sun direction + terrain
normal/visibility → predicted direct incidence and cast shadow; add sky and
terrain-reflected terms if their support permits. Compare these with radiometry
to distinguish plausible dark material, shadow/aspect and exposure effects.
Persistent low exposure is not itself measured albedo. Accurate clocks/time zones,
camera/strip lineage, datum/coordinate conversion and geometry are necessary;
clouds, indirect illumination and camera processing are additional unknowns.
Terrain visibility calculations are costlier than the ephemeris itself.

**M:** current Riffelhorn mosaic has a plausible flight date, not exact per-pixel
time/strip mapping. No acquisition-Sun or capture-shadow reconstruction was tested.
**Status:** ephemeris established externally/reusable; local illumination recovery
untested. **Open:** can official records tie each observed surface to adequate
capture metadata? The [Swiss opportunity](#swisstopo-2026-opportunity) is not proof
that exact timestamps have already been recovered.

## Steep-terrain photogrammetry and observation

- **Casella, V.; Franzini, M. (2016).** *Modelling Steep Surfaces by Various
  Configurations of Nadir and Oblique Photogrammetry*, ISPRS Annals III-1, 175–182.
  [Primary paper/DOI](https://doi.org/10.5194/isprs-annals-III-1-175-2016).
  Compares nadir/oblique acquisition configurations on a sandpit scarp using
  independent surveyed checkpoints. Acquisition configuration affects steep-surface
  reconstruction. That particular site does not establish a universal Alpine limit.
- **James, M. R.; Robson, S. (2014).** *Mitigating Systematic Error in Topographic
  Models Derived from UAV and Ground-Based Image Networks*.
  [Primary paper/DOI](https://doi.org/10.1002/esp.3609).
  Explains systematic deformation associated with image-network/self-calibration
  geometry; convergent observations can improve conditioning. More pixels alone
  do not solve every acquisition error.

**E:** SfM estimates cameras/structure; multiview stereo estimates denser surfaces
from correspondence. Inputs are overlapping calibrated/estimable images and a
well-conditioned network; outputs include geometry, poses and appearance observations.
Oblique views may expose faces hidden or poorly sampled in nadir views. Occlusion,
weak texture, moving material, inconsistent light and poor network geometry remain
failure modes. More views increase matching/visibility work and storage.

**M:** 012G's ideal heightfield surface-density model is `16 × cos(slope)` nominal
native information elements/m², not 100 independent elements from its 10 cm grid.
It explains stretching but does not reconstruct the original flight rays, MTF,
visibility or actual independence of resampled pixels.
**H / status: candidate observation-quality framework.** A surface can be
heightfield-compatible yet photographically unobserved. A true orthophoto uses
surface geometry and visibility to correct displacement/hidden areas; it does not
manufacture a vertical face's appearance. **Open:** which available images actually
observe each steep face? Changing mesh topology cannot answer that question.

## Multiview texture reconstruction

**Waechter, M.; Moehrle, N.; Goesele, M. (2014).** *Let There Be Color! Large-Scale
Texturing of 3D Reconstructions*, ECCV.
[DOI](https://doi.org/10.1007/978-3-319-10602-1_54),
[author paper](https://download.hrz.tu-darmstadt.de/pub/FB20/GCC/paper/Waechter-2014-LTB.pdf),
[author implementation](https://github.com/nmoehrle/mvs-texturing).

**E:** posed images and a mesh yield a texture atlas through visibility/image-quality
selection, neighbouring-face consistency and seam/radiometric adjustment. The
method uses image evidence and photometric outlier handling rather than choosing
the largest nominal image resolution blindly. Selection/optimisation and atlas
generation incur work proportional to visible candidates and texture extent.
Occluded faces, wrong geometry/poses, temporal changes and missing images cannot
be repaired by seam blending; a seamless atlas is not necessarily illumination-free.

**H — possible future research model:** surface → candidate observations →
visibility/angle/projected-resolution/quality scoring → selected or blended
observation → appropriately normalized/recovered appearance. Angle scoring is one
design criterion, not a claim that every published method uses the same score.
**Status: candidate, untested by Meridian.** 012B/F/G used one baked mosaic rather
than source-image selection. **Open:** availability of posed observations,
confidence/provenance retention across blending, and distinction between fixing
seams versus recovering albedo. This is not required Atlas architecture.

## View-dependent appearance

- **Debevec, P.; Yu, Y.; Borshukov, G. (1998).** *Efficient View-Dependent Image-Based
  Rendering with Projective Texture-Mapping*.
  [DOI](https://doi.org/10.1007/978-3-7091-6453-2_10),
  [author project](https://www.pauldebevec.com/Research/VDTM/),
  [paper](https://www.cs.princeton.edu/courses/archive/spring01/cs598b/papers/debevec98.pdf).
  Selects/blends observed images with respect to a novel viewpoint and approximate
  geometry. Visibility and alignment matter; this is not arbitrary relighting.
- **Wood, D. N.; Azuma, D. I.; Aldinger, K.; Curless, B.; Duchamp, T.; Salesin, D. H.;
  Stuetzle, W. (2000).** *Surface Light Fields for 3D Photography*.
  [DOI](https://doi.org/10.1145/344779.344925),
  [author publication record](https://homes.cs.washington.edu/~curless/publications/),
  [paper](https://cseweb.ucsd.edu/~ravir/6160/papers/p287-wood.pdf).
  Represents radiance as a function of surface location and viewing direction,
  retaining angular appearance under the observed lighting. It does not determine
  a complete material response under every possible new illumination.

**Inputs → outputs:** geometry plus many positioned appearance observations →
direction-dependent surface appearance. Strength: preserve effects one flat texture
cannot describe. Limits: angular coverage, storage, calibration and fixed-light
capture; more dimensions cost more than one texture per location.
**H / status: advanced/deferred.** Rock, snow, ice and water need not be Lambertian,
but Meridian has not measured a view-dependent discrepancy requiring this family.
Do not reinterpret fixed photographed shadows as a measured BRDF. **Open:** what
task/scale could justify angular data and its acquisition/delivery burden?

## Terrain visualization and cartographic lighting

**E:** physical illumination simulates specified light; cartographic relief shading
deliberately communicates form. Neither goal automatically optimizes the other.

- **Mark, R. (USGS, 1992).** *Multidirectional, Oblique-Weighted, Shaded-Relief
  Image of the Island of Hawaii*, Open-File Report 92-422.
  [Official report](https://pubs.usgs.gov/of/1992/of92-422/).
  Combining directions reduces dependence on one beam orientation; the composite
  is a visualization, not one physical Sun position.
- **Zakšek, K.; Oštir, K.; Kokalj, Ž. (2011).** *Sky-View Factor as a Relief
  Visualization Technique*, Remote Sensing 3(2), 398–415.
  [DOI](https://doi.org/10.3390/rs3020398),
  [author organization](https://iaps.zrc-sazu.si/en/svf).
  Sky visibility relates to surrounding horizons and helps reveal relief beyond
  one directional hillshade. Search distance and sampling determine scale and cost.
- **Doneus, M. (2013).** *Openness as Visualization Technique for Interpretative
  Mapping of Airborne Lidar Derived Digital Terrain Models*.
  [DOI](https://doi.org/10.3390/rs5126427).
  Positive/negative openness are surrounding-terrain angular descriptors, not new
  measured surface detail. See the maintained
  [Relief Visualization Toolbox documentation](https://rvt-py.readthedocs.io/en/latest/)
  for hillshade, sky-view, openness and local-relief implementations and parameters.

**Inputs → outputs:** DEM and chosen scale/directions → readable shaded/derivative
images. Curvature describes changes of form; local relief removes a broad trend;
openness/sky-view use horizons. Ambient-occlusion-like treatments can communicate
concavity without asserting a real shadow. Noise, edge effects, exaggerated small
features and parameter scale can mislead. Horizon operators cost more than local
slope/normal calculations. No universal readability metric is established here.

**Swiss practice (E, teaching documentation):** ETH Zürich's relief-shading resource
describes [design principles](https://ikgrelief.ethz.ch/design/),
[local light-direction choices](https://ikgrelief.ethz.ch/design/light-direction/),
[aerial perspective](https://ikgrelief.ethz.ch/design/aerial-perspective/) and
[generalisation](https://ikgrelief.ethz.ch/design/generalization/).
Deliberate emphasis, scale-dependent detail and controlled contrast serve terrain
comprehension. Its guidance omits cast shadows and reflected-light highlights in
traditional relief maps to avoid obscuring form. These are cartographic choices,
not a universal prohibition on shadows in 3D. Height-related contrast in a relief
map is not automatically camera-depth atmosphere in a perspective scene.

**M:** [012F](../../earth-lab/riffelhorn-012f-terrain-lighting.md) reveals existing
geometry with stronger directional shading; RGB gains are limited and cast shadows
are not accepted as a blanket improvement. It did not evaluate this entire field.
**H / status: candidate; no automatic new lighting Lab.** Need task/scale acceptance
criteria and honest separation of source colour, physical light and cartographic
emphasis. Historical Swiss practice is not an implementation specification.

**FATMAP source boundary:** the repository's
[qualified first-hand account](../../earth-lab/riffelhorn-visual-synthesis-and-experiment-design.md#fatmap-evidence-and-its-limits)
mentions custom terrain rendering/lighting and high-resolution normals. It is
limited public industry evidence, not a published algorithm. No proprietary normal
source, shader, cliff topology or acquisition policy should be inferred.

## Terrain generalisation and scale

**Jenny, B. (2021).** *Terrain Generalization with Line Integral Convolution*,
Cartography and Geographic Information Science 48(1), 78–92.
[DOI](https://doi.org/10.1080/15230406.2020.1833762),
[author institutional record](https://research.monash.edu/en/publications/terrain-generalization-with-line-integral-convolution/),
[IGN implementation](https://github.com/IGNF/dem_lic).

**E:** structure-aware generalisation uses terrain-directed convolution and adaptive
smoothing to remove excessive detail while retaining important ridge/valley form.
The output is a deliberately generalized elevation representation, not higher
measurement accuracy. Direction fields, filtering scale and treatment of transitions
affect both preservation and computational cost. The existence of an agency
implementation does not validate its parameters for Meridian.

**Inputs → outputs:** DEM plus intended map scale/structural treatment → generalized
DEM or relief. Ordinary low-pass filtering can suppress meaningful landforms;
structural preservation requires explicit goals. Slope, aspect and normals are
derived quantities whose generalisation also needs declared scale; their averaging
must respect directional meaning rather than treating angles as arbitrary scalars.

**M:** landscape/intermediate/close benchmarks repeatedly show different visible
information; ~600 m cliff displacement often becomes sub-pixel. That is not proof
of one optimal terrain generalisation. **H / status: candidate, untested.** These
may be distinct representation regimes involving geometry, normal/detail, imagery,
atmosphere and transitions. **Open:** which form must remain invariant for navigation
or terrain comprehension, and which declared generalisation can improve legibility?
Do not replace canonical measurement geometry with a display-oriented product
without keeping its derivation/provenance explicit.

## Large-scale terrain delivery

- **Losasso, F.; Hoppe, H. (2004).** *Geometry Clipmaps: Terrain Rendering Using
  Nested Regular Grids*, ACM Transactions on Graphics 23(3).
  [Author project/paper](https://hhoppe.com/proj/geomclipmap/),
  [full paper](https://hhoppe.com/geomclipmap.pdf).
  Nested viewer-centred grids provide a bounded multiresolution working set and
  incremental updates. It is a heightfield delivery/rendering technique, not a
  solution to unobserved cliff appearance. The original demonstration also uses
  synthetic detail; that is not required by the delivery mechanism or appropriate
  evidence of measured terrain.
- **Open Geospatial Consortium (2023, version 1.1).** *3D Tiles*, document 22-025r4.
  [Official standard](https://www.ogc.org/standards/3dtiles/),
  [normative document](https://docs.ogc.org/cs/22-025r4/22-025r4.html),
  [maintained specification](https://github.com/CesiumGS/3d-tiles/blob/main/specification/README.adoc#core-geometric-error).
  Hierarchical spatial content and geometric error support streaming/refinement
  of heterogeneous geospatial 3D content. Runtime screen-space error connects
  represented error to camera/output scale; it is not a sensor-accuracy claim.
- **Cesium project (living specification, version 1.0).** *Quantized-Mesh Terrain
  Format*. [Official specification](https://github.com/CesiumGS/quantized-mesh).
  Tiled triangulated terrain uses quantized coordinates and optional normal/water
  extensions. Efficient encoding does not recover missing measurements or generally
  model overhang topology.

**Inputs → outputs:** spatial/multiresolution products and error/extent metadata →
selectively delivered renderable content. Benefits include bounded memory and
view-dependent workload; costs include preprocessing, tile boundaries, error
management, streaming/storage and client complexity. Scientific provenance remains
an application concern, not something guaranteed by selecting a format.

**H / status:** established/reusable external engineering principles; specific Atlas
adoption deferred. A possible global/coarse → regional → local → true-3D where
justified hierarchy is a research model, not a required architecture. **M:** none
of the Riffelhorn Labs implemented planet-scale streaming. **Open:** real product
scope, client limits, acceptable errors and heterogeneous source rights/provenance.

## Swisstopo 2026 opportunity

**Official sources (E):** swisstopo, 23 April 2026,
[*New aerial imaging sensor*](https://www.swisstopo.admin.ch/en/new-aerial-imaging-sensor);
31 August 2026,
[*Digital aerial images*](https://www.swisstopo.admin.ch/en/digital-aerial-images).

The sensor announcement describes replacement of ADS100 by two Leica DMC-4S frame
cameras, multiple terrain observations from different angles (at least ten),
surface-model-based true-orthophoto production and Alpine native imagery improving
from 25 to 20 cm. It announces initial new-generation regional products for autumn
2026. That is neither 10 cm native coverage everywhere nor verified replacement
coverage of the present Riffelhorn tiles. True orthophotos do not guarantee observed
vertical faces or illumination-free texture.

The original-image documentation describes 2026-onward RGBN frame imagery,
31,520×13,440, 8-bit TIFF/Deflate, roughly 1 GB/image, with projection centres,
omega/phi/kappa orientation and calibration through `.gori`, plus metadata in
GeoPackage/CSV. Projection centres use LV95/LHN95 (vertical EPSG:5729), whereas the
current Riffelhorn heights use LN02 (EPSG:5728). A future integration would require
an explicit vertical-reference compatibility check. Original-image access is
described through ordering/quotation; do not assume immediate free bulk download
or that every calibration/product component shares identical terms.

**M — current evidence:** the retained 2023 SWISSIMAGE mosaic and 2021/2022 LiDAR
remain unchanged. No newer asset, original photo, model or sample was downloaded.
**H / status: future opportunity, deferred.** Posed multiview frames could provide
a stronger basis for visibility-aware appearance and acquisition-light research,
subject to coverage, radiometry, rights and lineage. Exact UTC timestamps/per-pixel
mosaic lineage were not verified from the available documentation; pose metadata
is not proof that those fields are recovered. **Open:** what actually exists for
this AOI, under which access/redistribution conditions, and with what acquisition
time/quality confidence? Do not silently swap the source stack.

## What this review changes

**E:** many component problems belong to mature fields, although outdoor appearance
recovery remains imperfect and data-dependent. **M:** failed Riffelhorn estimators
and brightness correction remain negative local results with their exact scope.
**H:** deliberate Atlas planning should separate geometry, observation visibility,
appearance, rendering and scale before selecting an established method to evaluate.
This review authorizes no acquisition, dependency, experiment or production refactor.
Use the [research-first workflow and contribution discipline](../atlas-research-map.md#default-research-workflow).
