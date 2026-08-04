# Drata SOC 2 Learning Center - 41 Articles

**Source**: https://drata.com/learn/soc-2  
**Parsed**: 41 articles across 8 categories  
**Status**: Ready for discovery and insertion into Courses domain

## Article Breakdown by Category

### Getting Started (8 articles)
1. Beginners Guide
2. Checklist
3. For Startups
4. Overview
5. Trust Principles
6. Type 2 Certification
7. Type 2 Compliance
8. Who Needs Soc 2

### Best Practices (7 articles)
1. Avoid Audit Exceptions
2. Compliance For Startups
3. Earn Customer Trust
4. How To Choose The Right Vendor
5. How To Streamline
6. Pick Right Audit Firm
7. Vendor Selection

### Preparation/Requirements (11 articles)
1. Audit Exceptions
2. Audit What To Expect
3. Compliance Requirements
4. Controls
5. Cost
6. How Long It Takes
7. How To Prepare For Your First Audit
8. Penetration Tests
9. Questions To Ask An Auditor
10. Readiness Assessment

### Reporting and Documentation (5 articles)
1. Report Overview
2. System Description
3. Trust Services Criteria
4. Readiness Assessment

### Differences vs Similarities (5 articles)
1. Certification Or Attestation
2. Type 1 Explained
3. Type 1 Vs Type 2
4. Soc 1 Vs Soc 2
5. Soc 1 Vs Soc 2 Vs Soc 3

### Automation/Maintenance (1 article)
1. Automation

### Additional Resources (4 articles)
1. 5 Reasons Your Company Does Not Need SOC 2
2. Bridge Letter
3. Common Misconceptions
4. Frequently Asked Questions
5. Myths
6. Soc 3 Everything
7. Top Mistakes

## Technical Integration

**Connector**: `drata`  
**Platform**: `course`  
**Source Type**: `curriculum`  
**Source URL**: `https://drata.com/learn/soc-2`

### Discovery Process
- When discovery is triggered for Drata source, the `drata_scraper.py` fetches and parses all 41 articles
- Each article is converted to a `CourseLesson` with:
  - Unique ID: `drata-soc2-{1..41}`
  - Title: Derived from URL slug
  - Category: Manually categorized for UX
  - Kind: `text` (article-based)
  - Has Video: `false`

### Data Storage
- Articles are persisted as `Record` objects in PostgreSQL with `domain=library`
- Dedup key format: `course:{source_id}:{lesson_id}`
- Each record stores metadata in `fields` JSONB including category and description

## Next Steps
1. Add Drata as a discoverable course source in the UI
2. User clicks "Discover" to trigger the parse
3. Worker runs `run_course_discover(drata)` which calls `fetch_and_parse_drata()`
4. 41 lesson records created in database
5. Frontend fetches and displays articles organized by category
