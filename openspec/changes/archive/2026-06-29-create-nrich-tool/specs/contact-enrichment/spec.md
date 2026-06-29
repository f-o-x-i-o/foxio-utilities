## ADDED Requirements

### Requirement: nrich accepts input YAML from ks-scout
nrich SHALL accept a YAML file path as its primary input. The YAML SHALL be a list of leads with the format produced by ks-scout, where each lead has at minimum `name`, `creator` (company/creator name), and `url` fields.
- **GIVEN** no `--input` argument
- **WHEN** nrich runs
- **THEN** it SHALL look for the most recent `leads_YYYYMMDD.yaml` file in `ks-scout/output/`

#### Scenario: Input via --input flag
- **WHEN** user runs `nrich --input path/to/leads.yaml`
- **THEN** nrich SHALL read and parse that YAML file
- **AND** SHALL validate that the file contains a list with at least one entry

### Requirement: Apollo stage — search decision makers
nrich SHALL connect to Apollo.io API to search for decision makers at each lead's organization. It SHALL extract the organization domain from the lead URL or creator name, then call Apollo People Search with seniorities: owner, founder, c_suite, partner, vp, head, director.
- **GIVEN** a lead with a identifiable domain
- **WHEN** Apollo People Search returns people
- **THEN** nrich SHALL sort them by seniority priority (founder/owner → c_suite → vp/head/director)

#### Scenario: Apollo returns decision makers
- **WHEN** Apollo People Search returns at least one person for the domain
- **THEN** nrich SHALL check which of them have `has_email: True`
- **AND** SHALL enrich each such person by their Apollo ID to get the email

### Requirement: Apollo stage — verified email stops pipeline
If any decision maker from Apollo has an email with `email_status: verified`, nrich SHALL use that email, record `source: apollo` and `confidence: high` in the output, and SHALL NOT execute further stages for that lead.
- **GIVEN** Apollo enrichment returns an email with `email_status: verified`
- **WHEN** determining whether to proceed to the next stage
- **THEN** nrich SHALL mark the lead as resolved and skip LinkedIn and web search stages

#### Scenario: Apollo has verified email
- **WHEN** Apollo enrich returns `("email@example.com", "verified")`
- **THEN** nrich SHALL populate `contact.email` with that email
- **AND** set `contact.source` to `"apollo"`
- **AND** set `contact.confidence` to `"high"`
- **AND** skip LinkedIn and web search for that lead

#### Scenario: Apollo has no verified email
- **WHEN** Apollo enrichment returns no email, or email_status is not `"verified"`
- **THEN** nrich SHALL continue to the LinkedIn stage for that lead

### Requirement: LinkedIn stage — web search for LinkedIn URL
If Apollo stage produces no verified email, nrich SHALL search the web for a LinkedIn profile URL of the lead's creator/team members. The search query SHALL combine the person's name and company name with "LinkedIn".
- **GIVEN** a lead with a creator name and company
- **WHEN** Apollo did not yield a verified email
- **THEN** nrich SHALL search for `"<creator name>" "<company>" LinkedIn`
- **AND** SHALL extract a LinkedIn profile URL if found

#### Scenario: LinkedIn URL found
- **WHEN** the web search returns a LinkedIn profile URL
- **THEN** nrich SHALL populate `contact.linkedin` with the URL
- **AND** set `contact.source` to `"linkedin"`
- **AND** set `contact.confidence` to `"medium"`
- **AND** continue to web search for email (do NOT stop on LinkedIn alone)

### Requirement: Web search email fallback
If Apollo and LinkedIn stages did not produce a verified email, nrich SHALL search the web for an email address associated with the creator and company. It SHALL use search queries combining the creator/company name with "email" or "contact".
- **GIVEN** no verified email from Apollo and no email from LinkedIn
- **WHEN** searching the web for an email
- **THEN** nrich SHALL find any email address in search results
- **AND** SHALL filter to only include emails whose domain matches the lead's organization domain

#### Scenario: Web search finds matching email
- **WHEN** web search returns an email address matching the lead's domain
- **THEN** nrich SHALL populate `contact.email` with that address
- **AND** set `contact.source` to `"web_search"`
- **AND** set `contact.confidence` to `"low"`

#### Scenario: Web search finds no email
- **WHEN** all three stages produce no email for a lead
- **THEN** nrich SHALL mark the lead as discarded
- **AND** NOT include it in the final enriched YAML output

### Requirement: Output enriched YAML
nrich SHALL write a new YAML file with only the enriched leads (those with contact info). Each lead SHALL retain all original fields from the input and add a `contact` field.
- **GIVEN** a set of enriched leads
- **WHEN** nrich finishes processing
- **THEN** it SHALL write a YAML file to the same directory as the input
- **AND** name it `<input_basename>_enriched.yaml`
- **AND** only include leads that have at least `contact.email` or `contact.linkedin`

#### Scenario: Output file structure
- **WHEN** nrich writes the enriched output
- **THEN** the output SHALL be a valid YAML list with the same structure as the input
- **AND** each lead SHALL have an additional `contact` field
- **AND** the `contact` field SHALL contain `email` (if found), `source`, and `confidence`

### Requirement: Console report
At the end of execution, nrich SHALL print a summary report to stdout with contact counts per source, discarded leads, and total processing time.
- **GIVEN** execution is complete
- **WHEN** nrich prints the report
- **THEN** the report SHALL show:
  - Total leads in input
  - Leads enriched by Apollo
  - Leads enriched by LinkedIn
  - Leads enriched by web search
  - Leads discarded (no contact found)
  - Total execution time

#### Scenario: Report formatting
- **WHEN** nrich completes
- **THEN** it SHALL print a formatted table to stdout
- **AND** exit with code 0 if at least one lead was enriched
- **AND** exit with code 1 if NO leads were enriched

### Requirement: Configuration file
nrich SHALL read configuration from a `config.yaml` file in its own directory, supporting Apollo API key, Google Custom Search API key (optional), and rate limit settings.
- **GIVEN** no config file exists
- **WHEN** nrich starts
- **THEN** it SHALL show an error with instructions to create `nrich/config.yaml`
- **AND** exit with code 1

#### Scenario: Valid config
- **WHEN** `nrich/config.yaml` exists with a valid Apollo API key
- **THEN** nrich SHALL proceed with enrichment
- **AND** SHALL use the configured API keys for each stage
