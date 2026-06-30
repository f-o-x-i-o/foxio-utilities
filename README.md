# foxio-utilities

Miscellaneous scripts, CLI tools, and skills that power [Foxio Design](https://foxio.design) — a hardware/embedded engineering consultancy.

Each tool lives in its own subdirectory with its own README, dependencies, and configuration.

## Tools

| Directory | What it does |
|---|---|
| [`ks-scout/`](ks-scout/) | Kickstarter lead discovery — finds hardware projects likely to need EE help |
| [`apollo-lookup/`](apollo-lookup/) | Check whether companies (e.g. ks-scout leads) figure in Apollo.io — by name, no credits |
| [`foxio-quote/`](foxio-quote/) | Skill: client quote / presupuesto as print-clean HTML from a refined template + pricing model |
| [`skill-distiller/`](skill-distiller/) | 🧪 **En fase de prueba** — skill: destila skills de desarrollo de software del historial de Claude Code (condensa transcripts → map-reduce → skills candidatas) |

## Setup

Each tool is self-contained. Go into its directory and follow that tool's README.

Most Python tools use [uv](https://docs.astral.sh/uv/) for dependency management:

```bash
cd ks-scout
uv sync
```

## References

Docs de referencia reusables (NO skills) en [`references/`](references/) — recetas/notas para reusar entre proyectos:
- **references/addTddToOpenSpec.md** — habilitar tareas test-first (TDD) en un repo OpenSpec greenfield.

## License

Internal tooling — not licensed for redistribution.
