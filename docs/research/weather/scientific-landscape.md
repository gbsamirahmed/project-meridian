# Independent Weather scientific landscape

Weather Research 001 (WR001), 10 October 2026. The external landscape was established before detailed legacy-code review. This is a scientific discovery map and investigation specification, not a textbook, validated runtime or frozen Weather contract. Start at [programme entry](README.md); track actual progress in the [register](research-register.md).

## Evidence vocabulary

**ES — ESTABLISHED SCIENCE:** physical/statistical concepts, not Meridian results. **OP — OPERATIONAL PRACTICE:** an institution's documented methods. **PD — PROVIDER DOCUMENTATION:** version-sensitive product/access claims. **PR — PEER-REVIEWED RESULT:** findings within a paper's experiment. **EI — ENGINEERING INFERENCE:** proposed consequences for Meridian. **U — UNRESOLVED:** requires investigation. Labels attach to claims, not whole providers. No capability is experimentally validated here. Dated references and access limitations are in the [source ledger](sources.md).

## Atmospheric disciplines and relationships

| Domain / ES foundations | Relationships / why it matters | Selective depth |
|---|---|---|
| Atmospheric structure and thermodynamics | Pressure, density, temperature, energy and phase changes determine vertical structure; potential temperature helps describe stability | Foundational. Air, skin and apparent temperatures differ; moisture convention/liquid–ice saturation matter; no universal lapse-rate correction |
| Dynamics and synoptic meteorology | Pressure gradients, rotation, friction, fronts, cyclones, jet streams and advection connect large-scale circulation to local weather | Foundational interpretation; upper-air patterns are context, not summit forecasts |
| Moisture and cloud microphysics | Condensation, evaporation and hydrometeor/ice processes affect precipitation, fog, cloud and radiation | Quantity semantics foundational; precipitation phase/icing/parameterisation require specialised work |
| Radiation and surface exchange | Short-/long-wave fluxes, albedo, emissivity, soil, vegetation and snow affect energy and temperatures | Foundational units and intervals; UV and terrain irradiance later; rendered shadow is not measured irradiance |
| Boundary layer and turbulence | Surface heating, roughness, stability and transport affect mixing, gusts and shallow cloud | Foundational limitations; deep gust/fog/exposure work. Parameterised turbulence is not a resolved gust history |
| Stability, convection and mesoscale processes | Buoyancy, inhibition, moisture, shear, sea breezes and outflows condition storm development | CAPE/CIN meaning foundational; diagnosis does not prove a storm at a point; nowcasting/severe weather separate |
| Orography and microclimates | Forced ascent, lee effects, channelled flow, inversions and valley/ridge circulation | High outdoor relevance; terrain alone cannot reconstruct missing atmospheric state |
| Coupled Earth systems | Land, snow/ice, oceans/waves and composition interact with weather | Identify hydrometeorology, coastal exposure, fire weather, air quality and seasonal context; not initial implementation requirements |

Primary ES/OP references: [WMO instruments guide](https://community.wmo.int/site/knowledge-hub/programmes-and-initiatives/instruments-and-methods-of-observation-programme-imop/guide-instruments-and-methods-of-observation-wmo-no-8), [UCAR/COMET boundary-layer teaching](https://www.meted.ucar.edu/tropical/textbook_2nd_edition/print_6.htm), [Met Office weather processes](https://weather.metoffice.gov.uk/learn-about/weather/how-weather-works). The guide landing page still labels 2021/2018 editions; deeper studies must pin the actual volume/chapter/edition, not claim a latest instrument-specific uncertainty budget from this entry. COMET describes the turbulence closure problem: unresolved transport requires assumptions. That motivates uncertainty research, not invented local detail.

## Prediction, observations and scales

OP: [Met Office forecasting](https://weather.metoffice.gov.uk/learn-about/how-forecasts-are-made) and [assimilation](https://www.metoffice.gov.uk/blog/2025/what-is-data-assimilation-and-how-does-the-met-office-do-it) distinguish observations, model background, estimated initial state and expert refinement. Analysis does not directly observe every location. ES: initial-condition/model errors interact and grow with lead; ensembles sample uncertainty, not automatically calibrated probability. [ECMWF uncertainty research](https://www.ecmwf.int/en/research/modelling-and-prediction/quantifying-forecast-uncertainty).

| Approach | Scientific role / important limitations | Meridian investigation |
|---|---|---|
| Global physical NWP | Circulation, multi-level fields, boundary conditions; unresolved processes parameterised | Context/reference candidates, not local truth |
| Regional / limited-area / convection-permitting | Finer process/terrain representation, dependent on boundaries, assimilation and physics | Effective resolution, storm displacement and local validation; finer grid does not prove greater skill |
| Deterministic | One predicted trajectory | Useful scenario with explicit uncertainty limits |
| Ensemble / probabilistic | Member distributions and events, potentially calibrated | Member dependence, thresholds, support/time and calibration identity; agreement is not accuracy |
| Post-processing | Bias correction, statistical calibration, blending and site adjustment | Representative observations, train/test separation, leakage, method/version and regime stability |
| ML / hybrid | Learned dynamics or corrections alongside physical systems | Training data, extremes, distribution shift, conservation and operational access need separate evidence |
| Analysis / reanalysis / hindcast | Estimated current/past state or retrospective forecasts, potentially revised | Not future forecast or independent ground truth; shared training/reference errors matter |
| Nowcasting | Observation extrapolation/blending, rapid updates, short horizons | Growth/decay, radar blocking, latency and transitions to NWP deserve their own track |

PR: [NeuralGCM](https://www.nature.com/articles/s41586-024-07744-y) (2024) is evidence for hybrid research within its evaluated tasks. [Storm Ciarán comparison](https://www.nature.com/articles/s41612-024-00638-w) (2024) examines an extreme case, not universal model ranking. PD: [AIFS operational ensemble](https://www.ecmwf.int/en/about/media-centre/news/2025/ecmwfs-ensemble-ai-forecasts-become-operational) and [current dataset](https://www.ecmwf.int/en/forecasts/datasets/aifs-machine-learning-data) establish a changing operational ML landscape; performance claims need independent regional/variable verification. GraphCast, GenCast, Pangu and other research models are identified, not selected; code/weights/data/operational-feed rights differ. GenCast's article access was incomplete here; no new quantitative paper conclusion is asserted.

ES/OP: stations sample exposure and averaging interval; radar infers hydrometeors from scattering; satellites measure radiance and retrievals infer properties; radiosondes sample trajectories; aircraft and marine observations have sampling constraints. [WMO observing system](https://community.wmo.int/site/knowledge-hub/programmes-and-initiatives/global-observing-system-gos). Instrument error, siting, calibration, QC flags, representativeness and latency must survive acquisition. Private/citizen sensors require separate consent/rights/calibration research.

Grid spacing is not effective predictive resolution or observed feature size. Model orography differs from physical terrain. Vertical levels may be pressure, height or terrain-following layers; below-ground levels need explicit handling. Time steps differ from observation averaging and accumulation intervals. Interpolation changes support and cannot recover sub-grid phenomena. Predictability varies by process, scale, regime and lead: seasonal anomalies are not daily hiking forecasts. ES/OP explanation: [Forecast User Guide](https://www.ecmwf.int/en/elibrary/81307-ecmwf-forecast-user-guide) (May 2018, conceptual reference, not current operational specification).

## Scientific data semantics — research obligations, not a schema

| Dimension | Preserve and investigate |
|---|---|
| Identity | Institution, model/version, product, experiment/control/member, native parameter/table version and immutable input; friendly aliases insufficient |
| Time | Initialisation/reference, analysis, issue/release, acquisition, observation/averaging interval, valid time, lead, accumulation start/end and revision. UTC/time zone/calendar conventions explicit |
| Horizontal | Grid/mesh, CRS/earth model, axis order/scanning, cell support, staggering and model terrain; curvilinear/reduced grids are not ordinary Web Mercator tiles |
| Vertical | Pressure, geopotential/geometric height, above model ground versus sea level, hybrid formula and auxiliary fields; pressure vertical velocity Pa/s differs from m/s |
| Quantity | Units/sign/vector basis; water equivalent versus snow depth; instantaneous/mean/max/sum/rate and interval reset; method-qualified transformations |
| Missingness / QC | Missing/unavailable/outside support/invalid QC/below ground versus true zero; sentinels and flags not physical values |
| Probability | Member set/weights, event threshold/operator, spatial/temporal support, calibration/training identity; class/member fraction/calibrated probability distinct |
| Provenance / lifecycle | Source–preparation–derivation lineage, revisions and source replacement; exact snapshot/horizon/freshness/expiry; stale is neither live nor necessarily false |

Standards: [GRIB2/ecCodes](https://codes.ecmwf.int/grib/format/grib2/) for identification/grids/product templates/packing; [BUFR](https://codes.ecmwf.int/bufr/) for structured observations with descriptor/QC review still needed (table entry retrieval unavailable here); [NetCDF](https://www.unidata.ucar.edu/software/netcdf) is a data-model/array family, not semantics alone. Reference released [CF 1.11](https://cfconventions.org/Data/cf-conventions/cf-conventions-1.11/cf-conventions.html) for coordinates, cell methods, missingness and vertical formulas; the living CF URL returned a draft, so it is not silently adopted. [Zarr v3](https://zarr-specs.readthedocs.io/en/latest/v3/core/index.html) specifies storage, not meteorological truth. [OGC EDR 1.1](https://docs.ogc.org/is/19-086r6/19-086r6.html) supports environmental queries; WIS2/WCMP2 concern discovery/exchange, [CAP 1.2](https://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2-os.html) alerts. Investigate code tables, CF names and provenance standards later. No final format/API/universal schema selected.

## Validation and uncertainty

| Different claim | Evidence needed; not obtained in WR001 |
|---|---|
| Correct decoding | Source message/metadata, independent decoder, unit/grid/time/missingness and known-value checks |
| Correct interpretation / derivation | Native meaning/support, justified interpolation, independent analytic/physical cases and versioned method |
| Forecast skill | Out-of-sample matched observations, defined region/regime/lead/variable, persistence/climatology baseline, sampling uncertainty and observation error |
| Outdoor decision suitability | Local representativeness, specific user task/limits and specialist evidence; skill alone does not prove route/avalanche safety |

[CAWCR verification recommendations](https://www.cawcr.gov.au/projects/verification/Rec_FIN_Oct.pdf) (Nurmi, 2003; historical methods reference) identify continuous, categorical and probabilistic evaluation. Bias and MAE/RMSE answer different questions. Event/base-rate effects, Brier/CRPS, reliability, sharpness and spread diagnostics need appropriate samples; spatial methods address displacement/intensity and extremes need event-specific evaluation. Calibration evaluated on training data is insufficient. Method choice, confidence intervals and observation independence remain to be scoped. Source checks should cover accumulations/reset, vector rotation, below-ground levels, dateline/pole/seams, quantisation and physical consistency/conservation where appropriate. Agreement between models is not a truth oracle; visual appeal/resolution is not skill. Preserve immutable inputs and negative results.

## Mountain and outdoor questions

ES/EI: ridge acceleration, sheltering, valley/slope winds, inversions, orographic/lee precipitation, low cloud, fog, convection, freezing variability and rapid snow/ice changes may be unresolved. Summit wind differs from a 10 m value over model terrain. Universal lapse rates or wind multipliers cannot be assumed reliable. Cloud base requires a vertical definition/ground reference; visibility/icing need specialised evidence. Atlas supplies context, not missing atmosphere. Flood, avalanche, surface safety and route suitability are separate questions.

Complement [Met Office mountain forecasts](https://weather.metoffice.gov.uk/guides/mountain/forecast), [MWIS](https://www.mwis.org.uk/forecasts/) and specialist services with labelled links unless exact reuse rights are established. [SAIS methodology](https://www.sais.gov.uk/how-we-produce-avalanche-reports) combines weather, snowpack observations and regional expertise; ordinary snowfall fields cannot replace it. Preserve warning authority, region, update/cancellation and limitations. No risk score, local downscaling or hazard prediction produced.
