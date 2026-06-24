# foxio-utilities

Miscellaneous scripts, CLI tools, and skills that power [Foxio Design](https://foxio.design) — a hardware/embedded engineering consultancy.

Each tool lives in its own subdirectory with its own README, dependencies, and configuration.

## Tools

| Directory | What it does |
|---|---|
| [`ks-scout/`](ks-scout/) | Kickstarter lead discovery — finds hardware projects likely to need EE help |

## Setup

Each tool is self-contained. Go into its directory and follow that tool's README.

Most Python tools use [uv](https://docs.astral.sh/uv/) for dependency management:

```bash
cd ks-scout
uv sync
```

## License

Internal tooling — not licensed for redistribution.
