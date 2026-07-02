---
name: openspec-greenfield-explore
description: Guardarraíl para la etapa explore de un proyecto OpenSpec grande (greenfield o adopción). Establece dónde vive cada tipo de información (specs/ = solo lo construido, blueprint/ = objetivo, project.md/config = contexto, ROADMAP = orden), evita el anti-patrón de escribir specs futuras a mano en openspec/specs/, y deja el andamiaje listo para el loop propose→apply→archive. Usala al arrancar un proyecto con OpenSpec, al cerrar una sesión de /opsx:explore con visión de producto completo, o cuando /opsx:apply "no encuentra changes".
---
<!-- foxio-library
saved: 2026-07-01
from:  /Users/simon/Development/HyS-Sport (destilada de la auditoría + realineamiento OpenSpec)
docs:  https://github.com/Fission-AI/OpenSpec — docs/explore.md, docs/workflows.md, docs/overview.md
-->

# OpenSpec greenfield: explore sin deuda

## El modelo mental (léelo antes que nada)

OpenSpec tiene dos carpetas con roles **opuestos**:

- `openspec/specs/` = la verdad actual, **lo que YA está construido**. La escribe el
  `archive` al mergear deltas — **nunca una persona o agente a mano**.
- `openspec/changes/<nombre>/` = lo que **debería** cambiar: proposal + design + tasks +
  delta specs (`## ADDED / MODIFIED / REMOVED Requirements`).

Y una regla que no es obvia: **`/opsx:explore` no persiste NADA**. No crea carpeta, no
escribe artefactos — es conversación pura. Todo lo que explores y no captures en archivos
o en el propose siguiente, se muere con el chat.

## Los domicilios de la información

Un proyecto grande genera cuatro tipos de información. Cada uno tiene UN domicilio:

| Qué es | Dónde vive | Quién lo escribe |
|---|---|---|
| Verdad construida | `openspec/specs/` | el archive, automáticamente |
| Visión / specs objetivo | `openspec/blueprint/` + `ROADMAP.md` | vos, durante/después del explore |
| Contexto permanente (stack, dominio, convenciones) | `openspec/project.md` + `config.yaml → context` | vos, al inicio |
| Trabajo en curso | `openspec/changes/<tajada>/` | el propose |

Dato verificado (no confíes en la intuición acá): la skill de propose **no usa rutas
hardcodeadas** — lee el bloque `context` que le entrega el CLI, y ese bloque sale de
`config.yaml`. Si el blueprint no está mencionado ahí, los proposes no saben que existe.

## Workflow para programa grande greenfield

Un programa grande = **cadena de changes chicos**, no un change grande. La doc oficial:
*"One logical unit of work per change"*; partí cuando *"scope exploded to different work
entirely"*.

```
openspec init  +  llenar project.md / config.yaml context
/opsx:explore (visión)  →  VOS capturás conclusiones en blueprint/ + ROADMAP.md
loop:
  /opsx:propose <tajada-vertical>   ← delta spec (## ADDED) tomando blueprint como materia prima
  /opsx:apply
  /opsx:archive                     ← specs/ crece un escalón, siempre verdadero
```

Al final del proyecto, `specs/` ES la documentación completa del sistema — construida
incrementalmente. Cuando una capability queda completa, su spec de blueprint **se borra**
(la verdad ya vive en specs/).

## Checklist al cerrar el explore (dejar el andamiaje listo)

- [ ] `project.md`: intent + stack + convenciones, y documenta explícitamente la
      separación specs/ (construido) vs blueprint/ (objetivo).
- [ ] `config.yaml → context`: una línea que diga dónde vive el blueprint y que specs/
      refleja SOLO lo construido. Es lo único que leen los proposes.
- [ ] `openspec/blueprint/README.md`: qué es la carpeta, cómo se consume, cuándo se
      borra cada spec.
- [ ] `CLAUDE.md` del repo: regla arriba de todo — "specs/ no se escribe a mano" —
      para las sesiones que NO entran por el flujo openspec.
- [ ] `ROADMAP.md`: tajadas verticales ordenadas, cada ítem referencia su spec de blueprint.
- [ ] `openspec/specs/` está **vacío** (greenfield puro) o contiene **solo lo real**
      (adopción sobre código existente).
- [ ] El output del explore quedó capturado en archivos. Si solo está en el chat, no existe.

## Anti-patrones (síntoma → causa → fix)

- **"`/opsx:apply` no encuentra nada" / `openspec list` vacío** → especificaste el
  sistema en `specs/` en vez de proponer changes. specs/ es invisible para apply.
  Fix: blueprint + propose por tajada.
- **specs/ describe features que no existen** → inversión del modelo (specs/ usado como
  blueprint). Fix: `git mv openspec/specs/<x> openspec/blueprint/<x>` — renames 100%,
  historial intacto con `git log --follow`. Las specs parciales se quedan pero se
  recortan a lo implementado; lo recortado vuelve al blueprint.
- **Un propose que especifica el sistema entero** → waterfall disfrazado. Partir en
  unidades entregables; se pueden llevar changes en paralelo y cerrar con bulk-archive.
- **Conclusiones del explore solo en la conversación** → explore no escribe artefactos
  por diseño. Capturá vos, en el momento, a blueprint/ROADMAP/project.md.
- **Editar las skills generadas (`.claude/skills/openspec-*`)** → las regenera
  `openspec update` y se pisan. La configuración tuya va en config.yaml / project.md /
  CLAUDE.md, que son tuyos.
- **Especificar todo upfront no es el pecado** — el pecado es el domicilio. Si tu modo
  natural es capturar el dominio completo primero, perfecto: eso se llama blueprint,
  no specs/.

## Caso validado: HyS Sport (2026-07-01)

16 specs del sistema completo escritas directo en `specs/` antes de construir nada.
Síntoma: al hacer apply, "ninguna de esas cosas figuraba en changes". Un solo change
(init-project) había corrido bien el ciclo completo propose→apply(TDD)→archive — la
mecánica funcionaba; el problema era solo el domicilio de las specs. Fix aplicado: 11
specs no construidas → `blueprint/` vía git mv (renames limpios), 4 parciales quedaron
en specs/ (recorte pendiente), README + config.yaml + project.md + CLAUDE.md apuntando
al blueprint. `openspec validate --specs` 4/4. Costo total del realineamiento: un branch,
dos commits.
