# nrich — Enrich ks-scout leads with contact info

Pipeline de 3 etapas para obtener datos de contacto de leads generados por ks-scout.

## Cómo funciona

Por cada lead:

1. **Domain discovery** — deduce el dominio real de la empresa (no el de Kickstarter)
2. **Apollo.io** — busca decision makers y emails verificados. Si encuentra → corta
3. **LinkedIn** — busca perfil de LinkedIn vía DuckDuckGo. Guarda URL, sigue buscando email
4. **Web search** — busca email en resultados de búsqueda + fetch de páginas

Los leads sin ningún contacto se descartan.

## Uso

```bash
# Auto-descubre el último leads en ks-scout/output/
python -m nrich

# Input explícito
python -m nrich --input ../ks-scout/output/leads_20260629.yaml

# Ver versión
python -m nrich --version
```

## Config

Copiar `config.example.yaml` a `config.yaml` y poner:

| Key | Dónde obtenerla |
|-----|----------------|
| `apollo.api_key` | Apollo.io → Settings → API Keys |
| `google_cse.*` | Opcional. Google Custom Search JSON API |

Sin Google CSE configurado funciona igual (usa solo DuckDuckGo).

## Output

Genera `<input>_enriched.yaml` con los leads que tienen contacto. Cada lead incluye:

```yaml
contact:
  email: user@company.com        # si se encontró
  linkedin: https://linkedin...  # si se encontró  
  source: apollo | linkedin | web_search
  confidence: high | medium | low
```
