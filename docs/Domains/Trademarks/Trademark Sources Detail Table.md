# Trademark Sources — Detail Table

Companion to the thin catalog header (`catalog_id`, domain, name, `source_url`, category, description, tags, priority, platform, source_type).

One detail row per trademark source (`catalog_id` / TMK-xxxx). Most columns are nullable — offices do not expose every channel.

**Table name (proposed):** `trademark_source_details`  
**Key:** `catalog_id` (FK → `sources.catalog_id` where `domain = trademarks`)

---

## Identity & jurisdiction

| Column | Type | Notes |
|--------|------|--------|
| `catalog_id` | text PK/FK | TMK-0001 … |
| `country` | text | Display name (e.g. United States) |
| `country_code` | text | ISO 3166-1 alpha-2 when applicable; regional orgs use codes like `EU`, `WIPO`, `ARIPO` |
| `jurisdiction` | text | National / regional / state / court — free text or enum later |
| `office` | text | Trademark office or body name |
| `dataset_name` | text | Optional label when the source is a named dataset/API product |

## Access channels (URLs)

Prefer specific endpoints over a generic homepage. The thin catalog `source_url` stays the primary “open this source” link; these refine it.

| Column | Type | Notes |
|--------|------|--------|
| `search_url` | text | Public trademark search UI |
| `registry_url` | text | Register / status lookup |
| `filing_url` | text | Online filing portal |
| `gazette_url` | text | Official gazette / bulletin |
| `journal_url` | text | Journal / publication list (if distinct from gazette) |
| `api_url` | text | Base REST/GraphQL endpoint |
| `api_docs_url` | text | Developer docs / OpenAPI |
| `bulk_download_url` | text | Bulk data landing page |
| `developer_portal` | text | Dev portal home (if distinct from docs) |
| `fees_url` | text | Fee schedule |
| `forms_url` | text | Forms / downloadable filings |
| `rss_feed` | text | Official RSS/Atom if any |

## Access mechanics

| Column | Type | Notes |
|--------|------|--------|
| `access_type` | text | e.g. `search`, `rest_api`, `bulk_download`, `scraper`, `gazette` (may differ from thin `source_type`) |
| `authentication` | text | none / api_key / oauth / account / unknown |
| `response_format` | text | JSON / XML / HTML / CSV / PDF / mixed |
| `pagination` | text | cursor / offset / page / none / unknown |
| `rate_limits` | text | Published limits or “unknown” |
| `query_parameters` | text | Short notes on main query knobs (mark, owner, class, …) |
| `languages` | text | UI/API languages (comma-separated or JSON later) |

## Classification & legal context

| Column | Type | Notes |
|--------|------|--------|
| `classification_system` | text | Nice / Vienna / local / none |
| `nice_version` | text | Nice edition/version if stated |
| `opposition_board` | text | Opposition / TTAB-equivalent body |
| `court` | text | Primary IP court of appeal if relevant |

## Coverage & ops

| Column | Type | Notes |
|--------|------|--------|
| `coverage` | text | What the source covers (marks, owners, classes, dates, …) |
| `update_frequency` | text | real-time / daily / weekly / batch / unknown |
| `license` | text | Terms of use / open data license |
| `status` | text | active / degraded / retired / unverified |
| `last_verified` | date | Last human or job verification |
| `notes` | text | Free-form caveats |

---

## Dedup notes (from prior draft)

Merged and removed overlaps:

| Removed / merged | Kept as |
|------------------|---------|
| Country + Country Code + country | `country` + `country_code` |
| Jurisdiction + country variants | `jurisdiction` |
| Trademark Office + office | `office` |
| Dataset Name | `dataset_name` |
| Access Type | `access_type` |
| Data Access URL / Base API URL / api_url | `api_url` (+ thin `source_url`) |
| API Documentation URL + developer_portal | `api_docs_url` + `developer_portal` |
| Authentication (twice) | `authentication` |
| Update Frequency (twice) | `update_frequency` |
| License (twice) | `license` |
| Status / Last Verified / Notes / Coverage / Pagination / Rate Limits / Query Parameters / Response Format | same names, snake_case |

**Column count:** 35 detail fields + `catalog_id` (not counting thin header columns already on `sources`).

---

## Standard enrichment set (26 columns)

Current standard for detail fill / seed (Batch 001 REPULLED and forward).

- Spec: [`Trademark_Source_Details_Abridged_Columns.csv`](Trademark_Source_Details_Abridged_Columns.csv)
- Blank template: [`Trademark_Source_Details_Abridged_Template.csv`](Trademark_Source_Details_Abridged_Template.csv)
- Batch 001 (TMK-0001–0050): [`trademark_details_catalog_batch_001_TMK-0001-0050_REPULLED.xlsx`](trademark_details_catalog_batch_001_TMK-0001-0050_REPULLED.xlsx)
- Next batch stub (TMK-0051–0100): [`trademark_details_catalog_batch_002_TMK-0051-0100.xlsx`](trademark_details_catalog_batch_002_TMK-0051-0100.xlsx)

**Included:** identity + `search_url` · `status_lookup_url` · `filing_url` · `registry_url` · `gazette_url` · `journal_url` · `api_url` · `api_docs_url` · `bulk_download_url` · `response_format` · `pagination` · `query_parameters` · `access_type` · `authentication` · `rate_limit` · `supports_nice_classes` · `supports_image_search` · `update_frequency` · `status` · `last_verified` · `notes`

**API keys:** not in the enrichment sheet. Stored on the detail row (`api_key_encrypted`) via the source detail page under API URL (PATCH/DELETE).

**Deferred** (full schema / majors only later): advanced/owner/image/assignment/renewal/legal URLs; swagger/graphql/ftp/rss/robots; vienna/design/boolean/fuzzy/phonetic/similarity flags; `dataset_name` · `developer_portal` · `forms_url` · `fees_url` · `languages` · `nice_version` · `opposition_board` · `court` · `coverage` · `license`.
