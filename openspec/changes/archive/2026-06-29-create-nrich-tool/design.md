## Context

ks-scout genera leads YAML con datos de Kickstarter (empresa, creator, score, evidencia) pero sin datos de contacto. No se puede hacer outreach directo. nrich es el eslabón siguiente en la pipeline: toma esos YAML, los enriquece con contacto real.

El pipeline actual de Foxio necesita contacto verificado para alimentar las campañas de Apollo. Este tool centraliza esa lógica en un solo módulo independiente.

## Goals / Non-Goals

**Goals:**
- Pipeline de 3 etapas priorizadas: Apollo → LinkedIn → búsqueda web de email
- Detención temprana por lead (si Apollo da email, no buscar más)
- Reporte por consola con stats: encontrados por fuente, descartados, total
- Output YAML enriquecido con campo `contact` y metadata de fuente
- Idempotente: sobre el mismo input produce el mismo output (salvo cambios en fuentes externas)
- Ejecutable vía CLI: `python nrich/nrich.py --input leads.yaml`

**Non-Goals:**
- No es un scraper de LinkedIn (no navega, no hace login) — busca URLs públicas de LinkedIn via web search
- No es CRM — no escribe a Apollo ni a ninguna base de datos
- No tiene interfaz web ni API server
- No maneja autenticación OAuth (solo API keys vía config)

## Decisions

### 1. Etapa Apollo como primaria
**Decisión:** Primero buscar decision makers en Apollo API. Si algún decision maker tiene email `verified`, se usa ese y se detiene para ese lead.
**Rationale:** Apollo es la fuente más confiable (emails verificados). Foxio ya tiene API key y los endpoints de People Search + Enrich están dominados. Evita gastar créditos de Apollo en leads ya resueltos.
**Alternativa:** Hacer todo en paralelo y deduplicar — descartada por desperdicio de recursos y complejidad innecesaria.

### 2. Etapa LinkedIn sin API
**Decisión:** Buscar perfil de LinkedIn del contacto via web search (Google Custom Search API o similar), no via API de LinkedIn (que requiere aprobación de partner).
**Rationale:** LinkedIn no da acceso público a emails sin API de Sales Navigator. La búsqueda web al menos puede dar el handle de LinkedIn, que sirve para outreach manual. Se extrae la URL del perfil del texto de resultado de búsqueda.
**Alternativa:** Usar Scraping API de terceros (Apify, Proxycurl) — se agrega como mejora futura si la tasa de éxito es baja.

### 3. Etapa web search como fallback final
**Decisión:** Si Apollo y LinkedIn no dieron resultado, buscar patrón de email en resultados de búsqueda web (nombre + dominio + "email" / "contact").
**Rationale:** Es el método más ruidoso pero el único recurso cuando no hay datos estructurados. Se indica como `source: web_search` y `confidence: low` en el output.
**Riesgo:** Falsos positivos — se requiere filtro básico (formato email regex + dominio del lead).

### 4. Output YAML con campo `contact`
**Decisión:** Cada lead enriquecido recibe un campo `contact:` con estructura `{name, email, source, confidence}`. Si no se encuentra nada, el lead no se incluye en el output final.
**Rationale:** Coherencia con el formato de entrada (YAML con lista de leads). Simplifica el pipeline: lo que sigue (outreach) solo ve leads con contacto.

### 5. Python puro con httpx
**Decisión:** httpx para HTTP (soporta async, timeouts, retry). Config local en YAML. pyproject.toml minimal.
**Rationale:** El entorno ya usa Python (ks-scout es Python). httpx es moderno, bien tipado, con soporte async (útil para paralelizar búsquedas web si hace falta más adelante).

## Risks / Trade-offs

| Riesgo | Mitigación |
|--------|------------|
| Apollo rate limit (600/h) | Backoff exponencial, sleep entre búsquedas, batch con pausas |
| Falsos positivos en web search | Solo incluir emails que matcheen el dominio del lead |
| LinkedIn sin API → tasa baja de éxito | Documentado como limitación; mejora futura con Proxycurl/Apify |
| Cambios en API de Apollo | Versionado del endpoint, tests de integración periódicos |
| Sin contacto → lead descartado → leads buenos perdidos | Reporte explícito de descartados para revisión manual |
