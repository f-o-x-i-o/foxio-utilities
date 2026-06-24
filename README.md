# ks-scout

CLI tool to discover **Kickstarter hardware projects that likely need EE consultancy help**. Crawls live and recently-ended campaigns, scores them by funding traction, fetches detailed descriptions, runs them through an LLM classifier, and outputs a ranked table of leads.

## Quick start

```bash
# Install
uv sync

# Set your LLM API key (DeepSeek is default, Groq also supported)
export DEEPSEEK_API_KEY=sk-...

# Run with defaults
ks-scout

# Accumulate results over time — append mode, skips duplicates
ks-scout --append

# Run with custom filters
ks-scout --categories hardware,gadgets --min-pledged-usd 100000 --limit 10

# JSON output for scripting
ks-scout --output json --limit 5
```

## LLM providers

Two providers supported — switch via `~/.config/ks-scout/config.toml`:

| Provider | Model | Env var | Free tier? |
|---|---|---|---|
| **DeepSeek** (default) | `deepseek-chat` | `DEEPSEEK_API_KEY` | No, dirt cheap |
| **Groq** | `llama-3.3-70b-versatile` | `GROQ_API_KEY` | Yes |

```toml
# DeepSeek
[llm]
provider    = "deepseek"
model       = "deepseek-chat"
api_key_env = "DEEPSEEK_API_KEY"

# Or Groq (free tier)
[llm]
provider    = "groq"
model       = "llama-3.3-70b-versatile"
api_key_env = "GROQ_API_KEY"
```

If you don't create a config file, DeepSeek is the default.

## Saving and accumulating results

```bash
# One-shot save — overwrites the file each run
ks-scout --save output/leads.txt

# Append mode — adds new results, skips duplicates (by URL)
ks-scout --append

# Append to a custom file
ks-scout --save mis_leads.txt --append
```

When using `--append`:
- Results go to `output/leads.txt` by default (folder created automatically)
- Duplicate URLs are detected and skipped
- Numbering continues from where the file left off
- If all results are duplicates, nothing is written and you get a message

## How it works

```
Discover (REST /discover/advanced)
  ↓
Filter (funding %, country, USD pledged)
  ↓
Traction filter (funding velocity)
  ↓
Fetch details (GraphQL — story, risks, creator bio)
  ↓
First-project filter (creators with ≤1 prior campaign)
  ↓
LLM classify (DeepSeek or Groq → HIGH/MED/LOW EE gap)
  ↓
Rank by composite score → table output
```

Every stage is cached in SQLite (`~/.cache/ks-scout/cache.db`).

## What each file does

| File | Purpose |
|---|---|
| `cli.py` | Main entry point — Click CLI, pipeline orchestration, filtering |
| `discover.py` | Fetches projects from Kickstarter's `/discover/advanced` JSON endpoint |
| `detail.py` | Fetches full project data via Kickstarter GraphQL API |
| `classify.py` | Sends project text to LLM → classifies EE gap as HIGH/MED/LOW (routes to Groq or DeepSeek depending on config) |
| `score.py` | Traction scoring (funding velocity) and composite ranking |
| `cache.py` | SQLite cache with TTLs for project lists, details, and LLM results |
| `http_client.py` | Rate-limited httpx client with CSRF token handling for GraphQL |
| `output.py` | Output formatting — Rich table, JSON, Markdown, text file with append/ dedup support |
| `config.py` | TOML config loading from `~/.config/ks-scout/config.toml` |

## Configuration

Copy the example config and edit:

```bash
mkdir -p ~/.config/ks-scout
cp config_example.toml ~/.config/ks-scout/config.toml
```

Defaults (all optional):

```toml
[llm]
provider    = "deepseek"
model       = "deepseek-chat"
api_key_env = "DEEPSEEK_API_KEY"

[cache]
project_list_ttl_hours  = 6
project_detail_ttl_days = 7
db_path                 = "~/.cache/ks-scout/cache.db"

[http]
user_agent      = "ks-scout/0.1 (personal research tool)"
rate_limit_rps  = 1.0
```

## Key design decisions

- **Two LLM backends** — Groq for free-tier usage, DeepSeek for dirt-cheap paid inference. Switch via config, no code change needed.
- **Country filter** hardcodes China/Hong Kong exclusion (manufacturing-first teams rarely need external EE help)
- **First-project filter** keeps only creators with 0–1 prior campaigns — first-timers are the best EE leads
- **Traction score** = (% funded / 100) / elapsed fraction of campaign, floored at 5% elapsed to avoid division by tiny numbers for just-launched campaigns
- **LLM prompt** is biased toward HIGH when in doubt — false positives are cheaper than missing a lead
- **Append mode** saves to `output/` folder, deduplicates by URL, continues numbering — designed for daily runs that build a lead list over time
- **No tests yet** — this is an internal tool

## CLI reference

```
Usage: ks-scout [OPTIONS]

  Discover live and recently-ended Kickstarter hardware projects that likely
  need EE help.

Options:
  --categories TEXT            Comma-separated category slugs.
                               [default: hardware,gadgets,diy-electronics,sound]
  --min-funded-pct INTEGER     Minimum % funded. [default: 51]
  --min-traction FLOAT         Minimum traction score. [default: 1.2]
  --limit INTEGER              Max rows in final output. [default: 20]
  --no-cache                   Bypass all caches for this run.
  --verbose                    Print intermediate scoring and classifier reasoning.
  --output [table|json|markdown]
                               Output format. [default: table]
  --min-pledged-usd INTEGER    Minimum USD pledged. [default: 50000]
  --ended-within-days INTEGER  Include ended campaigns closed within N days.
                               [default: 7]
  --save PATH                  Save results to a plain text file.
  --append                     Append results to save file, skip duplicates
                               (implies --save output/leads.txt if no --save given).
  --config PATH                Config file path (default: ~/.config/ks-scout/config.toml)
  -h, --help                   Show this message and exit.
```

## Available categories

`hardware`, `gadgets`, `diy-electronics`, `sound`, `wearables`, `3d-printing`, `robots`, `software`, `technology`
