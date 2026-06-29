## Context

nrich ya genera `_enriched.yaml`. Los pipelines downstream necesitan JSON con un esquema específico que incluye campos de estado de campaña (`sequenceStep`, `status`, `messages`) que nrich no gestiona. Estos campos se inicializan con valores por defecto.

## Goals / Non-Goals

**Goals:**
- Generar siempre 2 JSON junto al YAML actual (sin flag, sin cambios en CLI)
- JSON para leads con email → `_with_email.json` (para campaign manager)
- JSON para leads solo LinkedIn → `_linkedin_only.json` (para tracker)
- Campos de campaña inicializados con defaults

**Non-Goals:**
- No tocar el formato del YAML existente
- No agregar flags ni opciones nuevas
- No modificar el pipeline de enriquecimiento

## Decisions

### 1. Generación siempre activa
**Decisión:** Los JSON se generan siempre, sin flag. El costo es mínimo (json.dumps) y evita olvidos.
**Alternativa:** Flag `--json` — descartada por simplicidad.

### 2. ID único con uuid4
**Decisión:** Cada contacto recibe un `id` generado con `uuid.uuid4().hex[:13]` para coincidir con el formato del `linkedin_orphans.json` existente (IDs de 13 chars).
**Alternativa:** Incremental, hash del nombre — descartada porque los IDs deben ser únicos entre archivos.

### 3. Timestamps como Unix ms
**Decisión:** `addedAt` y `nextActionAt` se setean a `int(time.time() * 1000)`.

### 4. Sin modificar el YAML existente
**Decisión:** Los JSON se generan a partir de los `EnrichedLead` ya procesados, en paralelo al YAML.

## Risks / Trade-offs

| Riesgo | Mitigación |
|--------|------------|
| Esquema JSON inconsistente con lo que espera el tracker | Usar exactamente el template del `linkedin_orphans.json` existente |
| IDs duplicados entre corridas | uuid4 garantiza unicidad global |
