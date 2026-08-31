# Meridian Product Direction

## Purpose of this document

This document explains what Meridian is trying to become and why. It is a living statement of product direction, not a feature roadmap or technical specification.

- `README.md` describes the application as it currently exists and how to run it.
- The source code is authoritative for implementation details.

This document separates established direction from hypotheses and open questions so that exploratory ideas do not silently become commitments.

## Current position

Meridian is currently a client-only weather-map prototype built with React and MapLibre. It demonstrates a navigable map with 3D terrain, location selection and search, gridded weather retrieval, spatial weather overlays, and forecast exploration across time.

The prototype is a technical starting point, not a settled product design. Its current features and architecture should be preserved during ordinary work, but they should not automatically be treated as the ideal final form.

## Central idea

Meridian is intended to make weather conditions spatially understandable.

Conventional weather products often separate a forecast from the landscape. Values, icons, charts, and broad weather maps can describe conditions, but they may not clearly show what those conditions mean for a particular area, route, ridge, valley, or period of time.

Meridian should explore weather as part of the geography itself. A user should be able to understand not only the forecast at one coordinate, but also how conditions vary across an area and develop over time.

The central elements are:

- Geographic context
- Weather data
- Terrain
- Time
- Clear visual communication

The result should be useful and visually compelling. Visual quality is not merely decorative: it should make terrain and weather patterns easier to understand.

## Outdoor relevance

Outdoor use is an important source of product direction, particularly for activities where terrain and changing conditions matter. Potential use cases include:

- Understanding forecast conditions around mountains and exposed terrain
- Comparing conditions across nearby places
- Seeing how weather may vary along or around a proposed route
- Exploring how conditions develop during the hours of an outdoor day
- Identifying important changes in precipitation, cloud, visibility, wind, temperature, or other relevant variables

These are directions, not a final prioritised feature list. Meridian is not currently a safety system, a professional forecasting tool, or a substitute for authoritative forecasts and personal judgement. It should not imply guarantees that its data cannot support.

## Product principles

1. **Spatial understanding comes first.** Weather should be connected to place and area, not reduced to a single forecast card.
2. **Terrain should carry information.** 3D terrain and relief should help users interpret geography and conditions rather than serving only as decoration.
3. **Time is a core dimension.** Users should be able to understand how conditions develop, not just view one static forecast state.
4. **Clarity over data volume.** More layers and numbers do not automatically produce a better product. Each visualisation should answer an identifiable question.
5. **Outdoor relevance without false authority.** Meridian can support outdoor planning, but it must not imply precision, certainty, or safety guarantees that its data cannot provide.
6. **Honest representation.** Interpolation, forecast resolution, uncertainty, and other limitations should not be visually disguised as greater precision.
7. **Exploration before premature infrastructure.** The current purpose is to discover the strongest product and visualisation ideas, not to add large systems merely to make the prototype appear production-ready.
8. **Current implementation is not permanent product policy.** Preserve working behaviour during ordinary changes, while allowing later architectural reconsideration when a clear product need supports it.

## Weather visualisation

Meridian should move beyond treating weather as isolated values at a selected point. Important ideas to explore include:

- Continuous spatial layers rather than only point markers
- Movement through forecast time
- Multiple weather variables viewed in geographic context
- Visualisations that remain understandable over complex terrain
- Clear distinction between measured, modelled, interpolated, and derived information
- Honest communication of uncertainty and limited data resolution when relevant

The goal is not to place every available dataset on a map. A layer should help answer a meaningful user question and remain legible alongside the terrain and other interface elements.

Realistic atmospheric presentation and analytical clarity may conflict. Meridian has not decided whether its weather rendering should be realistic, stylised, or a deliberate combination of both. That remains a design question to investigate rather than an established requirement.

## Terrain and FATMAP inspiration

FATMAP is a reference for the quality and legibility of mountain terrain, not a specification to copy. The relevant ambition is a 3D landscape in which users can readily understand:

- Mountain shape
- Ridges and valleys
- Slopes and aspects
- Relative elevation
- The relationship between terrain, routes, and environmental conditions

High-quality terrain should support comprehension rather than act as an impressive background. Reaching this level may eventually require better elevation data, terrain meshes, imagery, rendering, or preprocessing than the prototype currently uses. Those choices remain unresolved and should be investigated before becoming architectural commitments.

## Relationship with Merlin Maps

Merlin Maps is a separate hiking-routing project owned by a friend. A useful conceptual distinction is:

- Merlin Maps helps answer: "Where do I go?"
- Meridian helps answer: "What are the conditions there?"

Routes could give Meridian a geographic structure through which to explain changing conditions, while Meridian could add environmental context to route planning. There may therefore be substantial value in combining routing, terrain, and weather intelligence.

The relationship is not settled. Possibilities include keeping the projects separate while sharing ideas or data, Meridian providing weather and terrain capabilities within Merlin Maps, Merlin providing routing within Meridian, or a later combined product.

Do not assume integration, shared ownership, a shared codebase, or a particular technical architecture. Any integration requires an explicit future decision involving the owner of Merlin Maps.

## What is established

- Meridian is centred on spatial weather understanding.
- Weather, geography, terrain, and time are the project's central elements.
- Outdoor and mountain use is an important source of use cases.
- Visual quality should support comprehension.
- The current prototype is exploratory rather than a finished product.
- Merlin Maps is separate, and any integration remains undecided.

## What remains open

The following are open questions, not requirements:

- Who the first primary user should be
- Whether the initial focus should be mountain users specifically or broader weather exploration
- The first planning task Meridian should solve exceptionally well
- Whether to prioritise desktop exploration, mobile outdoor use, or a staged progression between them
- The balance between realistic atmospheric rendering and analytical legibility
- Which weather variables deserve priority
- How uncertainty and forecast resolution should be communicated
- How far to pursue FATMAP-level terrain and what data and rendering pipeline that would require
- Whether routing belongs within Meridian
- Whether and how Meridian should integrate with Merlin Maps
- Whether the long-term product remains client-only or eventually requires supporting infrastructure

## Near-term purpose

For now, Meridian should be treated as a platform for evaluating weather-map interactions and visualisations. Near-term work should help answer:

- Which spatial weather layers are genuinely informative?
- How should terrain and weather be composed visually?
- How should a user move through forecast time?
- What information is useful when examining an outdoor location or route?
- Where does the current coarse weather grid create misleading or unattractive results?
- Which improvements create meaningful understanding rather than visual novelty?

Do not infer a detailed feature roadmap from these questions. The next priorities should emerge from evaluating the prototype and choosing a clear initial user problem.

## Maintaining this document

Update this document when product decisions are actually made. Preserve a clear distinction between:

- Established direction
- Current hypotheses
- Open questions
- Rejected or superseded ideas

Do not silently convert exploratory ideas into commitments. When a decision changes, record the change clearly enough that future work does not rely on outdated assumptions.
