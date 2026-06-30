---
name: skill-distiller
description: Destila skills de DESARROLLO DE SOFTWARE reutilizables del historial de Claude Code de uno o varios proyectos. Recorre los transcripts de las apps indicadas, los condensa a pura señal (qué se probó, qué falló y por qué, qué terminó funcionando) y los sintetiza vía map-reduce en skills candidatas — de decisión de stack y de PROCESO (el camino de desarrollar). Descarta todo lo no-dev (marketing, ventas, contenido, negocio). Úsala para capitalizar el conocimiento construido durante el vibe-coding de una o más apps.
---

# skill-distiller

Convierte el historial de desarrollo (vibe-coding) de una o más apps en skills
reutilizables. Detecta dos tipos: **skills de decisión de stack** ("para el caso
X usá Y") y **skills de proceso** (el camino: rutinas de debug, orden de
scaffolding, cómo se destrabó un problema).

## SCOPE — solo desarrollo de software
Extraé ÚNICAMENTE skills de software/ingeniería: stack y tecnologías, arquitectura,
build/deploy/hosting, debug, testing, config, comandos, workflows de dev. **Descartá
todo lo que no sea dev**: marketing, ventas/outbound, contenido, market research,
negocio, finanzas, tareas personales. Si una sesión no toca código/infra, salteala.

**Asset bundleado:** `condense.py` (vive al lado de este SKILL.md). Comprime ~40x
el JSONL crudo dejando solo la señal. Llamalo con la ruta absoluta de ESTE
directorio de skill.

## Paso 0 — Ubicar los transcripts
Claude Code guarda el historial en `~/.claude/projects/<ruta-con-guiones>/*.jsonl`
(la ruta absoluta del proyecto con `/` y `.` reemplazados por `-`). Listá y matcheá:
```bash
ls ~/.claude/projects | grep -iE 'appA|appB|appC'
```
Confirmá con el usuario qué dir corresponde a cada app antes de seguir.

## Paso 1 — Condensar (tirar el ruido, dejar la señal)
Por cada app, corré el asset:
```bash
python3 "<SKILL_DIR>/condense.py" ~/.claude/projects/<dir-appA> > /tmp/appA.md
```
(`<SKILL_DIR>` = la carpeta donde está este SKILL.md.)
Flags: `--thinking` incluye razonamiento (más volumen), `--cap N` ajusta el máximo
de chars por bloque (default 600). Cada `.md` puede pesar ~100-150K tokens:
**NO lo leas entero de una.**

## Paso 2 — MAP (extracción por sesión, en paralelo con subagents)
Cada `.md` está dividido por marcadores `## SESSION:`. Para cada sesión (o grupo
de 2-3 si son cortas) despachá UN subagent con esta consigna:

> Leé este tramo de transcript condensado. **Solo te interesa el desarrollo de
> software**: si la sesión es de marketing/ventas/contenido/negocio/personal,
> respondé exactamente `SKIP (no-dev)` y nada más. Si es de dev, extraé una FICHA:
> - **Objetivo** de la sesión (1 línea).
> - **Stack/tech tocado**: lenguajes, frameworks, servicios, hosting.
> - **Tropezones**: cada cosa que se probó y FALLÓ → síntoma/error exacto → por qué.
> - **Pivots**: "se cambió de X a Y porque Z".
> - **Lo que terminó funcionando**: la receta ganadora, reproducible.
> - **Skills de proceso**: rutina/método/orden que se repitió o destrabó el
>   problema (ej: "cómo debuggear un deploy que no levanta", "orden para
>   scaffoldear", "cómo verificar que el build cargó"). Esto es el CAMINO, no el stack.
> Seco, sin narrativa. Si una sección no aplica, omitila.

## Paso 3 — REDUCE (fichas → skills candidatas)
Descartá las fichas `SKIP (no-dev)`. Con el resto, agrupá los aprendizajes
**de software** en **skills candidatas**, enfocadas:
- **Decisión de stack**: "Para el caso X → usá Y (validado en app A/B)."
- **Proceso/método**: workflows reutilizables del camino de desarrollo.
- **Anti-patterns**: "NO uses X porque Z" (trazado a en qué app mordió).

Mostrá la LISTA de candidatas primero (nombre + 1 línea) y dejá que el usuario
elija cuáles materializar. No generes todas a ciegas.

## Paso 4 — Emitir SKILL.md
Por cada skill aprobada, creá `<nombre>/SKILL.md` con frontmatter (`name`,
`description`) + cuerpo seco. Formato que round-trippea con `npx skills`.
