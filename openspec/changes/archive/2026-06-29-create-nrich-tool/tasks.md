## 1. Project scaffold

- [x] 1.1 Create `nrich/` directory with `pyproject.toml` (httpx, PyYAML dependencies)
- [x] 1.2 Create `nrich/config.yaml` template (Apollo key, Google CSE key placeholder, rate limits)
- [x] 1.3 Create `nrich/config.example.yaml` with dummy values for version control
- [x] 1.4 Create `nrich/nrich.py` entry point with `--input` argument parser

## 2. YAML I/O layer

- [x] 2.1 Implement `read_leads(path)` — parse ks-scout YAML, validate list format
- [x] 2.2 Implement `write_enriched(leads, input_path)` — write `<basename>_enriched.yaml`
- [x] 2.3 Implement auto-discovery of latest `leads_YYYYMMDD.yaml` in `ks-scout/output/`

## 3. Config and logging

- [x] 3.1 Implement `load_config()` — read `nrich/config.yaml`, validate required keys
- [x] 3.2 Implement console logging with structured report format

## 4. Apollo stage

- [x] 4.1 Implement `search_apollo_people(domain)` — People Search with seniority filter
- [x] 4.2 Implement `enrich_by_apollo_id(person_id)` — get verified email
- [x] 4.3 Implement Apollo rate limiting (backoff on 429, max 600 calls/hour)
- [x] 4.4 Integrate Apollo stage into main pipeline: stop on `verified` email

## 5. LinkedIn stage

- [x] 5.1 Implement `search_linkedin(creator_name, company)` — web search for LinkedIn URL
- [x] 5.2 Implement extraction of LinkedIn profile URL from search results

## 6. Web search email fallback

- [x] 6.1 Implement `search_email_web(creator_name, company, domain)` — search for email
- [x] 6.2 Implement email extraction and domain validation (only match lead's domain)

## 7. Main pipeline and report

- [x] 7.1 Implement `enrich_lead(lead, config)` — orchestrates the 3 stages per lead
- [x] 7.2 Implement main loop: process all leads, collect stats
- [x] 7.3 Implement console report: counts per source, discarded, elapsed time
- [x] 7.4 Implement exit codes: 0 if ≥1 enriched, 1 if zero enriched
