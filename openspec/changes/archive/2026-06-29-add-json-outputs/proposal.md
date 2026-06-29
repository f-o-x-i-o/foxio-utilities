## Why

nrich produce un YAML enriquecido con leads que tienen contacto, pero los pipelines de Foxio (foxio-tracker y foxio-campaign-manager) consumen JSON con un formato específico. Actualmente hay que transformar manualmente el output de nrich para alimentar esos sistemas. Este cambio agrega la exportación directa a JSON.

## What Changes

- Siempre se generan 2 archivos JSON junto al YAML enriquecido:
  - `<basename>_linkedin_only.json` — leads con LinkedIn pero **sin email** (para foxio-tracker)
  - `<basename>_with_email.json` — leads con email (para foxio-campaign-manager)
- El formato JSON sigue la estructura del `linkedin_orphans.json` existente
- Cada contacto recibe un `id` único generado, `addedAt` timestamp, y campos por defecto (`sequenceStep: 0`, `status: "warming_up"`, etc.)

## Capabilities

### Modified Capabilities
- `contact-enrichment`: Agregar exportación JSON además del YAML actual. Dos archivos separados según si el lead tiene email o solo LinkedIn.

## Impact

- `nrich/src/nrich/pipeline.py` — después de `write_enriched()`, generar los 2 JSON
- `nrich/src/nrich/io.py` — nueva función `write_json_outputs()`
- Sin nuevas dependencias (JSON es nativo de Python)
