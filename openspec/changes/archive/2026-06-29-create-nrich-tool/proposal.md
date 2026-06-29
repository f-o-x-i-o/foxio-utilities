## Why

ks-scout genera listas de leads con empresas que claramente necesitan EE externa, pero no incluye datos de contacto verificables. Sin email o LinkedIn, no se puede hacer outreach. nrich cierra ese gap: enriquece cada lead con contacto real usando múltiples fuentes, priorizando Apollo.io por ser la más confiable.

## What Changes

- Nuevo tool `nrich/` — script Python autónomo que recibe un YAML de leads y produce un YAML enriquecido con contacto
- Pipeline de 3 etapas en orden de prioridad: Apollo.io → LinkedIn scraping → búsqueda web de email
- Reporte por consola al finalizar: contactos encontrados por cada fuente, cantidad de descartados
- Dependencias: Apollo API key (config), Google API key opcional, requests/httpx

## Capabilities

### New Capabilities
- `contact-enrichment`: Pipeline de 3 etapas para obtener emails verificados. Apollo como fuente primaria, LinkedIn como secundaria, búsqueda web como fallback. Soporte para rate limiting, timeouts, y checkpoint/reanudación.

### Modified Capabilities

## Impact

- Nuevo directorio `nrich/` con su propio `pyproject.toml` y dependencias
- Lee de `ks-scout/output/` por defecto (o path explícito)
- Escribe YAML enriquecido en el mismo directorio con sufijo `_enriched`
- Dependencias nuevas: SDK de Apollo.io, Google Custom Search API (opcional), httpx
- Reporte por consola con estadísticas de enriquecimiento
