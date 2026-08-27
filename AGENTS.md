# Meridian Agent Instructions

## Product context

Meridian is an exploratory weather-mapping project intended to make spatial weather conditions intuitive and visually compelling, particularly for outdoor use. Possible future directions include high-quality 3D terrain, richer weather visualisation, route planning, and integration with the separate Merlin Maps hiking-routing project. These are possibilities, not settled requirements or permission to implement them prematurely.

The product owner is not deeply familiar with TypeScript, React, or this codebase. Perform requested implementation work directly and autonomously, while explaining important decisions in plain language.

## Working approach

- When a change is requested, inspect the relevant code, follow existing patterns, implement it autonomously, make reasonable supporting edits, run appropriate checks, and fix problems caused by the work. Do not request approval for ordinary edits or implementation details.
- Ask the product owner only when a decision would materially affect product direction, architecture, cost, privacy, external services, or scope, or when the request is genuinely ambiguous. Otherwise, make a sensible decision and explain it afterward.
- Prefer focused, comprehensible changes over unnecessary rewrites or abstractions.
- Avoid new dependencies when existing tools or a small local implementation are sufficient.
- Preserve unrelated working-tree changes and do not overwrite work outside the task.
- Do not delete substantial functionality, perform destructive Git operations, commit, push, create or switch branches, or open pull requests unless explicitly requested.

## Architecture and services

- Preserve the current client-only architecture unless a task explicitly requires reconsidering it.
- Do not introduce a backend, database, authentication system, paid service, analytics or tracking, or an API-key requirement without first discussing the need and trade-offs with the product owner.
- Keep MapLibre's imperative lifecycle (map instances, sources, layers, controls, and event handlers) separate from ordinary React rendering unless there is a clear technical reason to change that boundary.
- Do not treat speculative future ideas as settled requirements.
- Keep documentation aligned with meaningful architecture or setup changes. The source code is authoritative for implementation details; broader architecture and setup documentation belongs in `README.md` or dedicated documentation rather than this file.

## Communication and verification

- Explain significant technical and architectural decisions in plain language suitable for someone who is not deeply familiar with web development.
- After implementation, run relevant lint and production-build checks and any additional checks appropriate to the changed area.
- Clearly distinguish pre-existing failures from failures caused by the current work.
- For every user-facing change, provide exact instructions for running the application and concrete steps to verify the result visually.
- In PowerShell, use `npm.cmd` rather than `npm` because the current execution policy blocks `npm.ps1`.

## Common commands

```powershell
npm.cmd install
npm.cmd run dev
npm.cmd run lint
npm.cmd run build
npm.cmd run preview
```
