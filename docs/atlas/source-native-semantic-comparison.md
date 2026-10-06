# Atlas source-native semantic comparison

## Question, result and scope

**SUCCESS — bounded semantic crosswalk stress test**, 2026-10-06. Real source
claims support the hybrid physical-property direction from the
[domain review](physical-surface-semantics.md), with native meaning and mapping
loss retained. This is not a product ranking, ground-truth assessment, surface
classifier or frozen evidence contract. A small common vocabulary is useful as a
projection of evidence; it is insufficient as the sole record of the world.

Starting Git: clean `main`, `75ea9d837c86506b0e278f79e209a8533e9664b7`
(`Review Atlas physical surface semantics`); fetch origin confirmed 0 ahead / 0
behind. The [source inventory](physical-surface-sources.md), current architecture,
[Tryfan proof](tryfan-second-region-proof.md), [Riffelhorn terrain record](terrain-hierarchy-prototype.md)
and [appearance baseline](swissimage-source-derived-baseline.md) supplied the
scopes and existing evidence. Elevation and multiscale remain closed; externally
provisioned multiview remains parked. No new terrain or imagery is acquired.

Evidence labels below distinguish **SOURCE FACT**, **MEASURED COMPARISON**,
**MERIDIAN INTERPRETATION** and **UNRESOLVED**. Ordinary semantic harmonisation
and vector/raster intersection are established methods, not Meridian inventions.

## Frozen footprints and patches

The [plan](semantic-comparison-plan.json) was written before acquiring semantic
results; SHA256 `62739330a5931120dbdcf14743b5be6f8acc5da5dfc3acbe6747e0aaa0daacd7`.
The existing Tryfan window is 9 km², not a newly invented 4 km² crop. Riffelhorn
retains exactly the 4 km² SWISSIMAGE footprint. Patch names describe sampling
opportunities, not asserted surface classes.

| Site / native comparison CRS | Full bounds: west, south, east, north |
| --- | --- |
| Tryfan / EPSG:27700 | 264900, 357800, 267900, 360800 |
| Riffelhorn / EPSG:2056 | 2624000, 1091000, 2626000, 1093000 |

| Patch | Centre in site's CRS | Square side | Selection rationale |
| --- | --- | ---: | --- |
| Tryfan summit | 266405, 359387 | 400 m | Existing summit reference; mountain surface opportunity |
| Tryfan southern-observer | 265876.05347833806, 358339.7631202109 | 400 m | Existing photographic observer; mixed-surface opportunity |
| Tryfan northern-context | 266400, 360450 | 400 m | Fixed north-central lower context; vegetation/water opportunity |
| Riffelhorn ordinary | 2625240, 1092530 | 60 m | Exact retained appearance probe |
| Riffelhorn steep | 2624805, 1092330 | 60 m | Exact retained problematic appearance probe |
| Riffelhorn summit | 2624810, 1092252 | 150 m | Exact retained summit appearance probe |
| Riffelhorn southern-quadrant | 2625750, 1091250 | 500 m | Predetermined southeast part of southern half; glacier/debris opportunity |

Each patch is inside its established footprint. No patch moved after inspection.
No water-case benchmark was added: water labels encountered within these mountain
windows are recorded without starting the separate water feature/state check.

## Selected sources, rights and bounded acquisition

**SOURCE FACT / MEASURED ACCESS.** Two families at Tryfan, three at Riffelhorn:
WorldCover supplies the shared categorical control; NRW supplies historical
habitat/mosaic evidence; GeoCover supplies a deliberately different geological
proposition; GLAMOS supplies glacier identity and overlying debris. Symmetry is
not forced. None supplies an actual canopy-height or per-cell cover-fraction field
in this retained set.

| Source / version | Retained subset | Rights gate and research evidence |
| --- | --- | --- |
| ESA WorldCover 2021 v200 | Native COG windows: N51W006, N45E006; 334×554 and 218×312 cells; 4,918 / 5,046 bytes | CC BY 4.0; ESA WorldCover 2021 and modified Sentinel credit; modifications declared |
| NRW Phase 1 family, service snapshot 2026-10-06 | WFS vegetation Voronoi: 193 complete intersecting features, 558,917 bytes; survey areas: 2, 589,835 bytes | OGL v3 with NRW/OS attribution/database notices; reusable research subsets and derived evidence with notices |
| GeoCover public bedrock / unconsolidated layers, snapshot 2026-10-06 | API envelope responses: 23 / 8 polygons, 985,424 / 97,673 bytes | swisstopo free-geodata terms, source acknowledgement © swisstopo; processing/distribution allowed |
| GLAMOS SGI2016 r2020 | Smallest published ZIP 9,787,779 bytes; 1 glacier / 6 debris records intersect window | CC BY 4.0; GLAMOS dataset citation, modified subset/analysis identified |

Primary gates: [WorldCover access/rights](https://esa-worldcover.org/en/data-access),
[NRW catalogue and licence](https://datamap.gov.wales/layergroups/geonode:nrw_terrestrial_phase_1_habitat_survey),
[swisstopo terms](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices),
[GLAMOS release/licence](https://doi.glamos.ch/data/inventory/inventory_sgi2016_r2020.html).
Required attribution information and URLs are retained in the
[source manifest](semantic-comparison-sources.json). The unabridged NRW notice
remains in retained official metadata, including OS licence AC0000849444.

Exact source URLs, queries, hashes, retained filesystem UTC dates, COG window
transforms and parent ETag/Last-Modified checks are in that manifest. A live
service timestamp is not an immutable product revision; retained response hashes
pin this experiment. No claim is made that future WFS/API calls return identical
bytes. Reanalysis from retained files is offline and deterministic.

Semantic source payloads total **12,029,592 bytes**; counted source/document
receipts total **24,555,804 bytes**, including the JNCC handbook/code list and
WorldCover manual. Separate budget-inspection metadata adds about 2.6 MB;
extracted GLAMOS subset copies total 1,269,196 bytes. Large/full native feature
geometries remain external, never in Git. The national GLAMOS inventory is
unavoidable excess from its smallest official distribution; only intersecting
features are used. COG range reads include compressed block excess: total wire
bytes and complete parent-file hashes are unknown. Whole 3-degree WorldCover
rasters were not acquired. Bbox APIs retain complete intersecting polygons beyond
the benchmark; analysis clips them without expanding the benchmark.

TLM was considered, not acquired: its official 2026-02 national Shapefile archive
is 3,591,345,815 bytes; WEST cover geometry alone is 420,779,341 compressed bytes.
Bounded ZIP-directory metadata established this cost. GeoCover's small public
queries answer the substrate/exposure contrast without that payload. This is a
source-selection adjustment, not a change to patches or analysis rules. UKCEH's
restricted raster, paid products, national Welsh data and aerial frames were not
acquired. Forest-height products were not forced into mostly treeless patches.

## Native claims, time, observation lineage and grain

**SOURCE FACT.** Raw comparison values remain native; common interpretations are
separate. The [results](semantic-comparison-results.json) retain native codes,
Welsh/JNCC names, polygon IDs, cell counts, glacier attributes, pair tables and
mapping losses. Full feature properties/geometries remain in hashed source files.

| Source | What a value claims | Lineage / time / grain / quality |
| --- | --- | --- |
| WorldCover | This native raster cell is classified into the source's annual cover class | Sentinel-1/2 derived classification; reference 2021, v200 publication 2022; nominal 10 m, native EPSG:4326 step 1/12000°; no acquired local posterior; product validation is not pixel confidence |
| NRW vegetation Voronoi | Historical survey habitat interpretation, sometimes a derived component subdivision or composition label | Field-survey programme; upland Ratcliffe/Birks and Welsh-modified Phase 1 lineage; EPSG:27700 polygons; component Voronoi boundaries are prepared geometry, not guaranteed observed physical edges |
| NRW survey areas | Programme-area survey-date context | Aberconwy 1995–1996, Arfon & Dwyfor 1987–1989 intersect; these are not proven acquisition dates of every upland component |
| GeoCover bedrock | Mapped lithostratigraphic/geological unit, potentially beneath cover | Geological mapping, typically 1:25,000; local survey epoch/MMU unestablished; service dataStatus 20260901 is not observation time; geological chronology is rock/deposit age |
| GeoCover unconsolidated | Mapped unconsolidated deposit over bedrock, e.g. slope debris or moraine | Independent layer; neither current bare-cover fraction nor RGB material classification; local geometry/interpretation accuracy unknown |
| GLAMOS glacier | Membership within inventoried glacier B56-07, Gornergletscher | Aerial/stereophotogrammetric TLM basis with glaciological revision; retained glacier `year_acq=2015`, release 2020; nominal inventory 2016 is not per-feature date |
| GLAMOS debris | Inventoried debris cover associated with that glacier | Six records have `year_acq=2016`, release 2020; published underlying `sgi-id` connects debris and glacier; vectors, no guaranteed raster-like resolution |

WorldCover's exact source definitions remain in
[PUM v2.0, table 3](https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/docs/WorldCover_PUM_V2.0.pdf):
tree/shrub/herbaceous classes use 10% cover criteria; bare/sparse includes soil,
sand and rock with vegetation no greater than 10% through the year. Snow/ice is
persistent cover; water means more than nine months of the year. Built-up excludes
urban green and treats extraction/waste separately. Tree cover can include other
cover beneath canopy. Global overall accuracy 76.7±0.5% is population validation,
not confidence at Tryfan or Riffelhorn. Neither class threshold nor nominal pixel
size proves local homogeneity. Local semantic MMU is not established here.

The [JNCC resource and Welsh code list](https://jncc.gov.uk/resources/9578d07b-e018-4c66-9c1b-47110f14df2a)
provide the retained code interpretation. Examples: I.1.2 scree; I.1.2.1
acid/neutral scree; D.1.1 dry acid heath; D.3 lichen/bryophyte heath; B.1.1
unimproved acid grassland; G.1 standing water; NA not accessed land; `?` denotes an
illegible original habitat code. D.5 is a real legend conflict: the Welsh name is
wet heath/acid-grassland mosaic, while the corresponding JNCC entry says dry.
The comparison preserves both and declines a wet/dry common mapping.
Handbook guidance suggests routine 0.1 ha units at 1:10,000 or 0.5 ha at 1:25,000,
with smaller exceptions. This is guidance, not verified MMU for these converted
NRW polygons; a tiny Voronoi fragment is not a tiny independently surveyed habitat.
No local accuracy/posterior is supplied by the retained records.

[NRW metadata](https://datamap.gov.wales/layergroups/geonode:nrw_terrestrial_phase_1_habitat_survey)
explicitly distinguishes component subdivisions from checkerboard mosaic
visualisation. The selected vegetation layer still carries 27 distinct composition
labels. Percentages are scoped to native mosaic evidence, not automatically to
our cut patch. Portal publication 16 August 2023 is not survey epoch.

The [official GeoCover restructuring notice](https://www.geo.admin.ch/en/new-structure-of-the-swissgeocover2d-datasets-on-mapgeoadminch)
separates bedrock units and overlying unconsolidated deposits. The older combined
layer is being retired; this experiment pins the new public layer IDs. Results
carry native German/French lithology, geological chronology and linked sheet
references; Serpentinit is not converted into a claim that every surface pixel is
exposed serpentinite. `not applicable` and null attributes remain different.

All pairs are temporally qualified. NRW versus 2021 cover is not simultaneous
survey truth; 2015 glacier and 2016 debris versus 2021 cover are also mismatched.
Changes in glacier/debris/snow are possible explanations, not measured change
here. GeoCover local observation time is unknown. No source was selected simply
for being newer, and no epoch discrepancy is used to declare a source wrong.

## Spatial method and limits

**MEASURED COMPARISON.** Native angular raster grids remain intact. PROJ
`always_xy` transformations place cell centres in the site's metre CRS; native
cell area is weighted ellipsoidally by row. Vector intersections use their
native projected CRS. No common-raster resampling, interpolation, categorical
blending or inferred material labels is performed. All source geometries pass
validity checks; invalid geometry would fail, not be silently repaired. Published
3D GeoCover coordinates are preserved in raw files; comparison uses XY only.

There are 173,967 WorldCover cell centres inside Tryfan and 66,862 inside Riffelhorn.
Top-row angular cells measure about 5.578×9.274 m and 6.457×9.263 m respectively;
that describes delivered angular sampling, not better-than-10 m classification
accuracy. Cell-centre and exact polygon areas are deliberately different measures.
Full-window centre-area differences are +0.029% / −0.016%. In 60 m patches, edge
sampling is material: ordinary has 70 centres representing 4,186.692 m² against
3,600 m² polygon area; steep has 54 representing 3,229.837 m². Their raster
percentages describe this selected centre population, not exact fractional
coverage of every square metre. No exact boundary agreement or local accuracy is
claimed. Vector slivers/overlap at sub-square-metre scale are retained numerically.

An STRtree only accelerates native point/polygon intersection. Multiple claims
are retained, not forced exclusive. Pair areas are centre-weighted incidence
between claims. They are not a truth confusion matrix or a quality score. Native
polygons are unioned within identical labels for area summaries; cross-property
layers stay separate. No imagery is classified to settle disagreement.

## Native-source results at Tryfan

Percentages below: WorldCover native selected centre population; NRW native
polygon area divided by fixed patch area. They cannot be subtracted as an exact
cell-by-cell area residual.

| Patch | WorldCover native result | NRW native result |
| --- | --- | --- |
| Summit | 98.16% grassland, 0.94% tree cover, 0.90% bare/sparse | 87.80% D.1.1 dry acid heath; 10.14% D.5; 2.05% I.1.2 scree |
| Southern observer | 86.34% grassland, 10.87% bare/sparse, 2.49% built-up, 0.29% trees | 29.58% D.1.1; 20.84% D.3; 45.36% native mosaic-labelled geometry, including 100% D.3 and mixed heath/rock or grass/heath claims |
| Northern context | 72.25% permanent water, 25.68% grassland, 1.49% built-up, 0.58% trees | 65.19% G.1 standing water; 19.75% mosaic-labelled; 5.15% NA not accessed; 4.34% no returned vegetation polygon; additional grass/heath/running-water claims |

The full 9 km² window is 88.92% WorldCover grassland, 4.97% trees, 4.82% water,
0.83% bare/sparse and 0.45% built-up; tiny shrub/moss labels also exist. NRW union
covers 99.48% of the footprint; mosaic-labelled polygons cover 19.16%, NA 0.59%,
and missing returned polygon support 0.52%. These categories are not equivalent
absence reasons. A record labelled `Mosaic of:100% D.3` is not evidence of multiple
materials; mixed labels are evaluated individually.

Across native NRW mineral-exposure labels I.1 / I.1.2 / I.1.2.1, centre-weighted
incidence totals 337,004.470 m²; 280,504.913 m² carries WorldCover grassland and
only 1,863.230 m² bare/sparse. This striking non-equivalence is **not** an accuracy
finding. Historical ecological inventory, prepared Voronoi support, 2021 cover
thresholds, mixed vegetation, differing grain and possible change are all relevant.
A summit camera location does not make its 400 m square homogeneous bare rock.
No camera or patch was changed to find a more dramatic disagreement.

**What Atlas can know:** dated native habitat interpretations, specified scree
and rock-inventory distinctions where present, broad annual cover classes, mixed
composition records, survey-area context and support gaps. Some native classes
embed ecological or management meaning rather than purely physical material.

**What Atlas cannot know:** current metre-scale rock versus loose clasts, actual
vegetation fractions within these cut patches, exact mosaic component locations,
canopy/understorey structure, current moisture/snow or trustworthy local accuracy.
Some historical dominant/scattered-species fields exist in raw records but are not
converted into current vegetation structure or inferred classes.

## Native-source results at Riffelhorn

| Patch | WorldCover native result | Independent inventory/geology result |
| --- | --- | --- |
| Ordinary, 60 m | 48.57% moss/lichen, 38.57% bare/sparse, 12.86% grassland | Geological polygons: 53.58% Serpentinit unit, 46.42% Ophiolith unit; no returned glacier/debris/deposit polygon at patch |
| Steep, 60 m | 100% bare/sparse in 54 selected centres | Serpentinit geological unit over whole patch; no exposure fraction, no direct proof of loose versus solid surface |
| Summit, 150 m | 98.70% bare/sparse, 0.78% snow/ice, 0.52% moss/lichen | Serpentinit geological unit over whole patch; no glacier/debris inventory intersection |
| Southern quadrant, 500 m | 99.47% snow/ice, 0.53% bare/sparse | 100% glacier B56-07 inventory membership (2015); 23.79% debris-cover inventory (2016); geological unit remains underneath, with lithological detail unestablished |

In the full 4 km² footprint, WorldCover has 44.11% bare/sparse, 27.34% snow/ice,
15.21% grassland, 12.47% moss/lichen, 0.83% water and 0.04% shrubland. GeoCover
bedrock polygons cover 93.99% and unconsolidated deposits 6.01%; this complementarity
in the returned map must not be mistaken for a complete direct surface-exposure
survey. Native deposits include 130,458.970 m² moraine, 104,154.847 m² slope debris
and 5,977.290 m² generic unconsolidated material. Surface vegetation, snow and
other cover can coexist with these geological propositions.

GLAMOS glacier area within footprint is **1,384,679.981 m² (34.62%)**, debris
**774,841.924 m² (19.37%)**. Their exact polygon overlap is **774,841.484 m²**;
0.440 m² of debris lies outside the retained glacier geometry. It is a tiny
geometric/date discrepancy, not proof of detached debris or a new glacier object.
Debris records explicitly reference the underlying glacier identity, making
layered semantics demonstrable without inferring ice from RGB.

Within selected centres inside the 2015 outline, the 2021 WorldCover incidence is
1,035,081.191 m² snow/ice, 326,618.254 m² bare/sparse, 24,167.752 m² water and
1,076.725 m² moss/lichen: approximately 74.63 / 23.55 / 1.74 / 0.08%. This is
agreement/disagreement between different propositions and dates, not current
inventory accuracy. In the southern patch, 58,448.032 m² of centre-weighted debris
incidence carries snow/ice and 1,316.133 m² bare/sparse. A later snow/ice cover
label does not logically erase an earlier debris inventory; snow cover, map grain,
classification error, inventory dates and change cannot be separated here.

**What Atlas can know:** dated Gornergletscher identity and mapped extent; separate
debris cover and its parent glacier; native geological units/deposits; broad
2021 cover interpretations. **Unknown:** current glacier boundary, exposed ice
versus snow at a specific date, debris thickness/grain, exact exposure of mapped
bedrock, fine vegetation/material fractions and steep-face physical material.
“No glacier inventory intersection” is a result of this inventory query, not a
proof that snow or ice cannot occur there. Geological age is not acquisition time.

## Small test vocabulary and explicit mapping loss

**MERIDIAN INTERPRETATION.** This experiment uses independent predicates, not one
exclusive class: woody vegetation; nonwoody vegetation; mineral exposure;
water cover; persistent snow/ice cover; artificial cover/structure. Glacier
membership and geological/deposit identity are additional source-scoped claims,
not forced into those cover predicates. Mixed composition and wet-substrate
claims remain native when the small test vocabulary cannot express them.

Relationship direction is **native proposition → test interpretation**.
Broader/narrower concern meaning, not pixel size. Compatible is not a proof of
classification accuracy; exact is reserved for retaining the same proposition.
No incompatible pair is manufactured merely to populate a relation enum.

| Native claim → proposed interpretation | Relationship | Information discarded or unresolved |
| --- | --- | --- |
| WorldCover tree/shrub → woody vegetation | Narrower | Tree versus shrub, thresholds, under-canopy cover, plantation/flooded context |
| WorldCover grassland or moss/lichen → nonwoody vegetation | Narrower | Growth form, threshold, species and mixture |
| NRW dry acid heath → woody vegetation | Narrower | Dwarf-shrub habitat, acid condition, mixture and survey meaning |
| NRW scree → mineral exposure inventory | Narrower | Loose versus solid and ecological subtype if reduced to generic mineral |
| WorldCover bare/sparse → its broad mineral/sparse-cover proposition | Compatible | Still cannot distinguish soil/sand/rock, loose material or actual fraction |
| WorldCover bare/sparse → exposed bedrock or scree | Partial overlap | Vegetation and other mineral materials; not an exact rock mask |
| WorldCover snow/ice → persistent ice alone | Broader | Snow versus ice; cannot identify glacier object |
| WorldCover snow/ice → glacier membership | Ambiguous / partial overlap | Persistent snow outside glaciers; debris-covered glacier; no identity |
| GLAMOS glacier polygon → dated glacier membership | Compatible, exact claim retention | No intrinsic current exposed-ice fraction |
| GLAMOS debris → loose cover above identified glacier | Narrower | Glacier identity and dated layered relation lost by mineral-only collapse |
| NRW mire/flush → open water | Partial overlap; equivalence rejected | Wet vegetation/soil and hydrological regime do not mean open-water cover |
| NRW D.5 → specifically wet or dry heath | Ambiguous | Documented Welsh/JNCC name mismatch, not repaired silently |
| GeoCover bedrock → current exposed-rock cover | Unmappable | Geological substrate proposition does not establish surface exposure |
| NRW NA / illegible `?` → physical surface class | Unmappable | Observation/access or transcription absence, not a material |
| NRW buildings → artificial structure; WC built-up → artificial cover | Narrower / compatible at their own scope | Object versus area, roads/other built cover, no land-use/function equivalence |

An assertion that a geological-age attribute is an acquisition date is
**incompatible in property type**. It is rejected rather than crosswalked. A
source-native inventory and annual cover label can disagree without themselves
being incompatible data: their predicates, grain and epochs differ.

False equivalences encountered: bare/sparse ≠ exposed rock; grassland ≠ dry acid
heath; snow/ice cover ≠ glacier identity; debris ≠ absence of glacier; bedrock unit
≠ current exposure; wetland/mire ≠ open water. Tree cover and planted woodland
also retain different definitions; neither becomes forestry land use.

### Mixed and proportional evidence

Native labels include `50% B.1.1,24% C.1.1,24% I.1.2,2% E.2.1` and
`98% I.1.2.1,2% B.1.1`, which explicitly combine habitat/mineral components.
An illegible `2% ?` component survives alongside 98% known grassland. Composition
is neither a confidence score nor a uniform allocation of each percentage to every
cell. The original polygon/mosaic identity and preparation scope must travel with
it. The acquired Voronoi geometry does not prove subpatch component fractions.

GLAMOS independently demonstrates glacier identity plus debris surface cover.
No hidden ground under vegetation, snow-covered rock, soil depth or glacier debris
thickness is inferred. Continuous properties remain valuable, but this set contains
**no true local continuous fractional field**. Published habitat percentages are
support-scoped composition evidence. It would be false to generate a vegetation
fraction raster from categorical codes or call these percentages a local canopy
field. That negative limit is sufficient here; no extra source is added to fill a
continuous-data quota.

## Quality, unknown and absence

**SOURCE FACT / MERIDIAN INTERPRETATION.** None of the acquired semantic records
supplies per-location classification confidence that can be compared across all
families. WorldCover product/class validation statistics refer to a validation
population; NRW survey/legend guidance is not a per-polygon posterior; GeoCover
interpretation/generalisation and GLAMOS inventory lineage are different quality
statements. Mosaic percentages, coordinate precision and publication recency are
not confidence. No product-wide accuracy is transformed into pixel certainty.

| Encountered condition | Required meaning, without freezing enum names |
| --- | --- |
| WorldCover native 0 | Product nodata; absent in these selected populations, not a measured physical zero |
| NRW NA | Survey access/observation absence; 0.59% of full window and 5.15% northern patch |
| NRW `?` component | Historical code illegible, while other components remain known |
| No returned polygon at a point | No assertion from queried layer; not absence of vegetation, deposits, glacier or a material |
| Source cannot distinguish rock/scree | Ontology/grain limitation, even where data exists |
| D.5 names disagree | Mapping/definition ambiguity, not a missing cell |
| Claims differ across products | Potential semantic/temporal/grain/classification conflict; no adjudicated truth |
| Old glacier/habitat inventory | Current state unknown; date retained rather than silently updated |
| GeoCover `not applicable` versus null | Explicit inapplicability differs from missing/unestablished attribute |
| RGB or geometry available but no claim derived | Observation exists; semantic inference not performed |
| No glacier feature in patch | Class/inventory membership absent in this snapshot; not absence of seasonal snow or buried ice |

These materially different cases require first-class unknown/absence reasons.
“Not classified” is not always “not observed”: NA, illegibility and ontology gaps
are different. Source support and target property applicability must be known
before interpreting a negative assertion. No complete-world absence proof is
produced here.

## Existing Atlas evidence and semantic gaps

**SOURCE/PRODUCT FACT.** This is an inventory of already established evidence,
not a fresh classification or a new geometry/appearance experiment.

| Window | Existing observation/product evidence | What it does not yet assert |
| --- | --- | --- |
| Tryfan | Retained NRW 1 m DTM and verified DSM; regional terrain product `tryfan-welsh-regional-v2`; existing geographic photographs/natural-colour research records; production AWS terrain and MapTiler imagery | DTM morphology is not rock/scree material. DSM-minus-ground is not automatically vegetation. Photos have limited footprints/view direction; common imagery contributors/epochs are unknown. No semantic model has been run. |
| Riffelhorn | Swiss 0.5 m distributed terrain, regional support revision `1a44a0644de1bde73a3ba84d1b761dc0aa17d48cc971e5f6b5d2c14fb329d7ea`; regional parents `b92c9a3dfa05a87e4fcce4a6e6638efd2d9ab8e86537f52833ff1ed6def78672`; four SWISSIMAGE 2023 tiles `2624-1091`, `2624-1092`, `2625-1091`, `2625-1092`; appearance identity `f6edd630206ed02f255176935d72126cbc6ad7987b12d2986edbe6d05619bc1b`; common AWS/MapTiler | Orthophoto RGB is not semantic material, albedo or viewing-direction completeness. Native 10 cm distribution / nominal 25 cm information does not classify rock or loose clasts. Glacier change cannot be inferred from geometry residuals alone. |

See [Tryfan source/product identities](tryfan-second-region-proof.md),
[Tryfan observed natural colour](../earth-lab/tryfan-010-observed-natural-colour.md),
[Riffelhorn source catalogue](riffelhorn-data-catalog.json) and
[SWISSIMAGE evidence manifest](swissimage-source-derived-baseline.json).
The comparison reads these durable identities; it does not repeat their terrain,
appearance or provisioning validations. Existing photographic limitations persist:
the steep patch has substantial orthographic stretch (retained p95 6.19×), and
original observation occlusion was not established. More source pixels or a
semantic label cannot supply missing observation directions. No multiview work
was reopened.

| Patch group | Described / weakly described | Conflicting or unexpressed properties | Possible existing evidence, without performing inference |
| --- | --- | --- | --- |
| Tryfan summit | Old heath/scree habitat and broad annual cover | Current solid versus loose mineral exposure; vegetation/rock fractions; ecological/native grass-heath mismatch | DTM for form; geographically supported photos/common imagery where visible |
| Tryfan southern observer | Historical lichen/heath/rock mosaics; annual grass/bare/built classes | Actual current component positions/fractions; material grain, current plant structure and dated change | Retained observer photography plus geometry; no wall-to-wall calibrated observation assumed |
| Tryfan northern context | Water/grass/native habitat, NA and missing polygon support | Current shoreline/state and classification gap; no current canopy/ground layers | Existing imagery and geometry; water-feature/state reasoning remains a later task |
| Riffelhorn ordinary/steep/summit | Broad cover; native geological substrate | Fine visible rock versus loose clasts; true local plant fraction; snow timing; difficult-face material and unobserved parts | SWISSIMAGE where support is sufficient; fixed Swiss terrain; common imagery with unknown epoch |
| Riffelhorn southern quadrant | Glacier identity plus debris layer and snow/ice category | Current ice/snow/debris state, thickness, boundary change and fine cover fractions | Retained 2023 orthophoto and geometry, with mixed-year/illumination/projection limits |

**MERIDIAN INTERPRETATION — inference role: LIMITED.** There is a demonstrated
role for narrowly scoped future semantic inference or manual interpretation:
current visible solid mineral versus loose material and spatially supported
vegetation/mineral fractions at finer grain than these inventories. Those
properties are not supplied as contemporaneous fine fields by the selected
products. Existing imagery may contain evidence where observation support is
adequate. Recoverability, classification accuracy and acceptable uncertainty have
**not** been established. Old inventories are useful priors/evidence, not training
truth by default. Exact plant species, soil depth, debris thickness, hidden ground
and dark/poorly supported cliff properties are not justified inference targets
merely because RGB exists. No broad autonomous classification programme follows
from this result.

## Cross-region meaning and regional/global handoff

**MERIDIAN INTERPRETATION.** Broad vegetation, mineral exposure, water and
snow/ice cover concepts transfer, but with scope and native definitions attached.
Welsh acid grassland/heath/mire ecology and Swiss geological/glacier identity are
source/domain-specific detail. Nothing in this comparison converts them into one
identical ontology. Geological material can be valuable external evidence without
opening a deep-geology model inside the surface foundation.

Property-scoped fallback is **conditionally viable**, not proven as automatic
ranking. The actual support gaps illustrate its limits:

- If NRW has NA or no polygon, WorldCover can supply its dated broad cover claim,
  retaining the original missing-access/support reason. It cannot supply a missing
  acid-heath subtype, current vegetation fraction or scree identity.
- If a glacier/debris inventory has no returned feature, WorldCover snow/ice can
  supply a cover interpretation only. It cannot stand in for glacier membership,
  debris layer or current glacier boundary. No feature does not authorize deleting
  a glacier or asserting exposed bare ground.
- Global cover cannot fill missing GeoCover lithology. Conversely, geological
  substrate cannot replace unknown current exposure. Only predicates with a
  documented compatible relation can be compared/substituted, with time, support,
  grain and quality changes visible.

A regional/global handoff changes observation basis, ontology, epoch, grain/MMU
and validation scope. Different layers may coexist rather than choose one winner.
No categorical blend, date-based ranking or seamless semantic fallback is
implemented. This task tests actual missing/native supports inside the fixed
windows, not a fabricated expanded regional service boundary.

## Evidence-contract requirements revealed, not frozen

These are empirical requirements for the later contract task, not entity names,
enums or schemas:

1. Preserve native code/value, ontology/version, definition reference, feature or
   raster-cell support and original identifiers. Preserve preparation-generated
   subdivisions versus surveyed boundaries and parent mosaic support.
2. Keep any common interpretation separate, with relation direction, mapping
   method/revision, information loss and ambiguity. A mapping may be partial or
   unavailable; it must not overwrite the original claim.
3. Time belongs to each claim/layer: acquisition range, inventory epoch, release
   and service snapshot are different. Unknown acquisition time is valid.
4. Permit independent categorical, proportional and object-membership claims,
   with a layered relation where published. Do not force one class or manufacture
   a continuous local fraction from mosaic percentages.
5. Preserve observation lineage, source processing, spatial grain/MMU uncertainty,
   CRS/analysis operation and provenance. Common vocabulary is not a universal
   confidence or accuracy model.
6. Preserve quality statement kind/population; unknown/absence reason and property
   applicability; contradictory definitions; rights/attribution and mapping lineage.
7. Fallback must be scoped to compatible properties and must preserve ontology,
   temporal, grain and support differences. Source absence is not physical absence.

The cover/exposure, feature/structure, time-qualified state and evidence/lineage
responsibilities survive as a **hybrid candidate decomposition**. Names remain
provisional; nothing is attached to TerrainProduct or AppearanceProduct. No
semantic runtime, UI, tile layer, classifier, NDVI, segmentation, weather parameter
assignment or Traverse/traversability inference was created.

## Decision gates and next step

| Gate | Decision / evidence |
| --- | --- |
| Hybrid physical-property direction supported? | Yes: habitat mixtures and glacier-plus-debris claims cannot be expressed faithfully by one exclusive cover class |
| Small common vocabulary sufficient alone? | No; useful only alongside native semantics and independent properties (hybrid B/C/E outcome) |
| Native semantics first-class? | Yes: scree versus bare/sparse, heath versus grass, geological versus exposed material, glacier identity versus snow/ice |
| Partial/ambiguous/unmappable relationships needed? | Yes: actual mixed support, D.5 conflict, WC snow/ice-to-glacier and geological-to-cover mismatch |
| Unknown/absence reason first-class? | Yes: access absence, illegible code, missing feature, ontology gap, date uncertainty, inapplicability and unperformed inference differ |
| Property-scoped regional/global fallback viable? | Conditional: broad cover can be offered separately; no compatible fallback established for specific ecology, lithology or glacier/debris identity |
| Meridian-derived inference role? | LIMITED, with specific fine/current exposure/fraction gaps; recoverability/accuracy unresolved, no implementation authorized here |
| Overall result? | SUCCESS for the semantic stress test, not proof of local map truth or of a future inference model |
| Proceed to separate water feature/state check? | Yes. No foundational blocker requires another mountain comparison. |

**Exact next task:** one separately authorized, bounded water-feature/state check
using a small lowland/estuary case, testing persistent feature identity versus
dated extent/reference condition and absence. Do not select/acquire that case
here. The minimal evidence contract follows later, informed by both checks.
No classifier or extra mountain-semantic experiment is recommended now.

## Reproduction, diagnostic evidence and validation

Data root: `meridian-data/derived/atlas/semantic-comparison-v1`. Source payloads,
original geometries, GLAMOS extracted copies and the diagnostic `native-support.png`
remain external. Git contains only tooling, synthetic tests, frozen plan, receipts,
lightweight numeric/native-label summaries and this report. The map is a native
support diagnostic, not an Atlas layer; colours do not establish equivalence.
WorldCover colours show native classes, NRW colours show native code families and
mosaic/NA support, and glacier/debris/deposit polygons remain independent. NRW white regions include explicit NA and gaps, distinguished in the numeric
record; Swiss white regions mean no returned inventory/deposit assertion. Neither
is a physical cover classification.
PNG SHA256 `b4532573091e6abceac20155e8d792b2b1576bf313562aeba41c605fbea26a76`.

Run from repository root with the external research environment; dependencies are
pinned in [research requirements](../../scripts/atlas/semantic-research-requirements.txt).
The application does not import these scripts or require those assets/dependencies.

```powershell
$semanticData = 'C:/Users/gbsam/Documents/Projects/meridian-data/derived/atlas/semantic-comparison-v1'
$semanticPython = 'C:/Users/gbsam/Documents/Projects/meridian-data/earth-lab/.venv/Scripts/python.exe'
# Explicit network acquisition only after reading the recorded source-specific terms.
& $semanticPython -X utf8 scripts/atlas/semantic_sources.py --data $semanticData
# Offline deterministic analysis and asset-free synthetic tests.
& $semanticPython -X utf8 scripts/atlas/test_semantic_compare.py
& $semanticPython -X utf8 scripts/atlas/semantic_compare.py --data $semanticData
& $semanticPython -X utf8 scripts/atlas/plot_semantic_compare.py --data $semanticData
# Optional intentional publication of lightweight diagnostics, never raw source geometry.
& $semanticPython -X utf8 scripts/atlas/semantic_compare.py --data $semanticData --publish
```

A changed live snapshot must not silently replace the frozen experiment. Analysis
validates both local receipts and frozen Git source hashes. Network acquisition
can reproduce query/extraction mechanics, not guarantee unchanged mutable services.
WorldCover parent source byte hashes remain unknown; native subset hashes and
window definitions are the retained reproducibility boundary. CRS operations use
installed PROJ transformations, not a newly downloaded local datum grid; the
operation and declared accuracy are retained in each site diagnostic. Small
coordinate/edge uncertainties matter at the 60 m patches; no survey-grade boundary
accuracy is claimed.

Validation: eleven asset-free synthetic tests cover frozen footprints, LV95/BNG
control/roundtrip, physical angular-cell dimensions, mosaic unknowns, access
absence, overlapping/hole geometry, multi-claim incidence, invalid geometry and
non-equivalent property mappings. Offline source hashes/geometry parsing, complete
NRW response counts, native CRS transforms and polygon/cell summaries pass.
Independent reruns produce byte-identical diagnostics and map. Native WorldCover
window re-reads match every retained class value and transform. The recorded
PROJ operations declare 2 m (BNG) and 1 m (LV95) accuracy, not centimetre alignment. No local accuracy
reference survey is available, so no truth validation is implied. Source rights,
definitions, epochs and official access documentation were checked. Production
file hashes, source diff, documentation references and final diff are verified in
the development log. Application tests/build are unnecessary: no shared runtime
code changes and normal startup/CI has no new data or service dependency.

Production remains AWS visual terrain through TerrainHierarchy, independent AWS
analytical z15, exaggeration 1.45, unchanged IGOR, MapTiler satellite-v2 and normal
opacity/suppression/lifecycle/projection. Weather and Traverse are unchanged.
No terrain reconciliation, imagery correction, aerial acquisition, multiview work,
water case or evidence-contract implementation occurred. Stop this comparison here.
