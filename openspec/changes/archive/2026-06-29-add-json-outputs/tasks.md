## 1. JSON output writer

- [x] 1.1 Implement `write_json_outputs(enriched_leads, input_path)` in `io.py`
- [x] 1.2 Build the JSON entry per lead: id, name, headline, companies, company, email, linkedinUrl, addedAt, campaign defaults
- [x] 1.3 Split into `_with_email.json` and `_linkedin_only.json` based on contact type
- [x] 1.4 Call `write_json_outputs()` from pipeline after `write_enriched()`
