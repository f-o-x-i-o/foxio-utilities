## ADDED Requirements

### Requirement: Generate JSON outputs for downstream pipelines
nrich SHALL generate two JSON files alongside the enriched YAML output, following the structure of `linkedin_orphans.json`.

#### Scenario: Leads with email produce _with_email.json
- **GIVEN** the pipeline has processed all leads
- **WHEN** at least one lead has a contact with an email address
- **THEN** nrich SHALL write `<basename>_with_email.json`
- **AND** each entry SHALL contain: `id`, `name`, `headline`, `companies`, `company`, `email`, `linkedinUrl`, `addedAt`, `sequenceStep`, `nextActionAt`, `stepHistory`, `coldSequenceStep`, `coldStepHistory`, `messages`, `status`, `notes`, `website`, `source`, `link_type`

#### Scenario: Leads with only LinkedIn produce _linkedin_only.json
- **GIVEN** the pipeline has processed all leads
- **WHEN** at least one lead has a LinkedIn URL but no email
- **THEN** nrich SHALL write `<basename>_linkedin_only.json`
- **AND** the `email` field SHALL be an empty string

#### Scenario: JSON structure matches template
- **GIVEN** a processed lead ready for JSON export
- **WHEN** building the JSON entry
- **THEN** the `id` SHALL be a 13-character hex string (via uuid)
- **AND** `addedAt` and `nextActionAt` SHALL be Unix timestamps in milliseconds
- **AND** `sequenceStep`, `coldSequenceStep` SHALL be 0
- **AND** `stepHistory`, `coldStepHistory`, `messages` SHALL be empty arrays
- **AND** `status` SHALL be `"warming_up"`
- **AND** `link_type` SHALL be `"personal"` for person contacts, `"company"` for company pages
- **AND** `source` SHALL be `"apollo"` or `"google"` based on the enrichment source
- **AND** `notes` SHALL be empty string
- **AND** the full contact name SHALL go in `name`
- **AND** the headline SHALL be derived from contact title
- **AND** `companies` SHALL be a single-element array with the company name
