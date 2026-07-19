# Government Intelligence Domain
## Source Catalog and Implementation Planning Specification — Version 1.0

**Catalog date:** 2026-07-16  
**Cataloged sources:** 223  
**Scope:** U.S. federal government sources plus official procurement entry points for all 50 states and the District of Columbia.  
**Status:** Planning and source-selection document. Technical connector design is intentionally excluded.

> This document is the canonical source inventory for implementing the Government domain of the Intelligence Platform. > It identifies the sources to be evaluated and connected, their access paths, automation potential, priority, and the commercial intelligence each source can support.

---

# 1. Domain Mission

The Government domain collects official and near-primary public data that can reveal:

- contracts and subcontracting opportunities;
- grants, research funding, assistance programs and prize challenges;
- contract awards, incumbents, modifications and likely recompetes;
- agency spending, budget growth and public investment priorities;
- regulations, legislation, executive actions and policy changes;
- public-sector organizations, registered contractors and compliance risks;
- infrastructure, health, energy, transportation and environmental demand;
- public assets, surplus property and government-funded technologies;
- state procurement opportunities across all U.S. jurisdictions.

The Government domain should answer practical questions such as:

- What government opportunities are open now?
- Which opportunities have changed or are closing soon?
- Who previously won similar work, for how much, and through which contract vehicle?
- Which agencies are increasing spending in a market?
- Which regulations or laws will create new compliance or service demand?
- Which grants and research programs match a company, nonprofit, patent or product?
- Which government-funded technologies, software or assets are available for licensing, acquisition or reuse?

---

# 2. Catalog Scope and Limitations

## Included

- Official federal APIs, bulk downloads, RSS feeds, GIS services, open-data portals and public databases.
- High-value official portals where no reliable public API is available.
- State procurement-office entry points for every state and the District of Columbia.
- Sources that can enrich other domains, including Finance, Business, Healthcare, Geography, Software, Taxes and Real Estate.

## Not yet included

- Every county, city, school district, public university, transit authority, utility and special district procurement portal.
- Every agency-specific RSS feed or document repository.
- International government procurement systems.
- Detailed connector specifications, endpoint parameters, pagination, schemas, rate limits or code.
- Commercial aggregators when an official government source is available.

## Verification standard

Each catalog row includes an official access or documentation link. Before coding begins, every source must pass a final implementation-readiness review covering access stability, authentication, current terms, commercial use, refresh cadence and a sample retrieval.

---

# 3. Source Classification

| Field | Values used in this catalog |
|---|---|
| Automation | Auto; Semi-auto; Manual |
| Priority | P1 = first implementation; P2 = high-value secondary wave; P3 = valuable but fragmented or portal-based; P4+ = deferred |
| Business Value | Very High; High; Medium; Low |
| Access | REST API; bulk download; CSV/XML; RSS; GIS; open-data platform; portal; HTML; authenticated portal |

### Automation meaning

- **Auto:** Stable machine-readable interface suitable for scheduled ingestion.
- **Semi-auto:** Some automation is possible, but access may depend on portals, exports, account sessions, linked systems or periodic manual review.
- **Manual:** Human retrieval or review remains the primary access method.

---

# 4. Catalog Summary

- **Total sources:** 223
- **Automatic sources:** 129
- **Semi-automatic sources:** 94
- **P1 sources:** 100
- **P2 sources:** 79
- **P3 sources:** 44

## Sources by category

| Category | Count |
|---|---:|
| State Procurement | 51 |
| Labor Statistics | 4 |
| Banking | 3 |
| Courts | 3 |
| Cybersecurity | 3 |
| Defense Procurement | 3 |
| Fiscal Data | 3 |
| Grants | 3 |
| Healthcare | 3 |
| R&D Funding | 3 |
| Regulations | 3 |
| Research Funding | 3 |
| Awards | 2 |
| Business Activity | 2 |
| Committees | 2 |
| Compliance | 2 |
| Defense Research | 2 |
| Demographics | 2 |
| Education | 2 |
| Energy | 2 |
| Entities | 2 |
| Financial Filings | 2 |
| Legislation | 2 |
| Prices | 2 |
| Procurement | 2 |
| Public Health | 2 |
| Publications | 2 |
| Spending | 2 |
| Statutes | 2 |
| Surplus Assets | 2 |
| Trade | 2 |
| Votes | 2 |
| Acquisition | 1 |
| Acquisition Rules | 1 |
| Agency Directory | 1 |
| Agriculture | 1 |
| Air Quality | 1 |
| Archives | 1 |
| Assistance | 1 |
| Aviation | 1 |
| Behavioral Health | 1 |
| Biologics | 1 |
| Biomedical Literature | 1 |
| Broadband | 1 |
| Budget | 1 |
| Certifications | 1 |
| Climate | 1 |
| Clinical Research | 1 |
| Commodity Markets | 1 |
| Communications | 1 |
| Community Risk | 1 |
| Construction | 1 |
| Contract Vehicles | 1 |
| Disasters | 1 |
| Economic Indicators | 1 |
| Economic Statistics | 1 |
| Energy Regulation | 1 |
| Environment | 1 |
| Environmental Compliance | 1 |
| Executive Policy | 1 |
| Export Controls | 1 |
| FOIA | 1 |
| Facilities | 1 |
| Federal Holidays | 1 |
| Federal Jobs | 1 |
| Federal Property | 1 |
| Federal Workforce | 1 |
| Finance | 1 |
| Flood Risk | 1 |
| Food | 1 |
| Foreign Influence | 1 |
| Funds | 1 |
| Geography | 1 |
| Geologic Hazards | 1 |
| Geospatial | 1 |
| Government Finance | 1 |
| Hazard Risk | 1 |
| Health Products | 1 |
| Healthcare Capacity | 1 |
| Healthcare Finance | 1 |
| Healthcare Payments | 1 |
| Healthcare Providers | 1 |
| Healthcare Relationships | 1 |
| Higher Education | 1 |
| IT Spending | 1 |
| Immigration | 1 |
| Integrity | 1 |
| Investment Advisers | 1 |
| Judicial Statistics | 1 |
| Justice | 1 |
| Lobbying | 1 |
| Local Health | 1 |
| Management Policy | 1 |
| Marketplace | 1 |
| Medical Devices | 1 |
| Minerals | 1 |
| Oversight | 1 |
| Per Diem | 1 |
| Pharmaceuticals | 1 |
| Political Finance | 1 |
| Pricing | 1 |
| Prize Challenges | 1 |
| Procurement Law | 1 |
| Product Safety | 1 |
| Public Lands | 1 |
| R&D Awards | 1 |
| Regulatory Burden | 1 |
| Regulatory Planning | 1 |
| Research | 1 |
| Road Infrastructure | 1 |
| Rulemaking | 1 |
| Sanctions | 1 |
| Securities | 1 |
| Set-Asides | 1 |
| Software | 1 |
| Soils | 1 |
| Space | 1 |
| Subawards | 1 |
| Subcontracting | 1 |
| Supplier Discovery | 1 |
| Tax Statistics | 1 |
| Technology | 1 |
| Toxic Releases | 1 |
| Transit | 1 |
| Transportation | 1 |
| Vehicle Safety | 1 |
| Water | 1 |
| Water Quality | 1 |
| Weather | 1 |
| Weather Disasters | 1 |

---

# 5. Priority Implementation Waves

## Wave 1 — Immediate P1 feeds

Start with sources that are official, machine-readable and directly connected to actionable opportunities:

1. SAM.gov Contract Opportunities
2. USAspending
3. SAM.gov entities and exclusions
4. Grants.gov and Simpler.Grants.gov
5. Federal Register, Regulations.gov, eCFR and Congress.gov
6. Treasury Fiscal Data, Census, BLS and BEA
7. CMS, CDC, FDA and NIH
8. EPA, FEMA, NOAA and USGS
9. EIA, NREL, FERC, BTS, FHWA and FCC
10. SEC EDGAR, FDIC and Federal Reserve datasets

## Wave 2 — High-value portals and bulk datasets

Add sources with strong business value but less-uniform access, including GSA pricing tools, DLA DIBBS, FERC eLibrary, GAO bid protests, state procurement portals, federal property, auctions, courts and specialized agency datasets.

## Wave 3 — State and local expansion

After state procurement entry points are validated, expand each state into its underlying bid platform, award database, vendor registry, contract repository, grants system and public-spending portal. County and municipal systems should then be cataloged by market priority rather than all at once.

---

# 6. Government Source Catalog

Columns:

- **ID:** permanent source identifier;
- **Category:** primary government source category;
- **Source / Owner:** official source and responsible organization;
- **Data available:** records expected from the source;
- **Coverage:** federal or state jurisdiction;
- **Access:** interface or retrieval method;
- **Auto:** automation classification;
- **Priority / Value:** implementation order and expected commercial usefulness;
- **Opportunity:** example actionable output;
- **Access link:** direct official documentation or source entry point.

## State Procurement

**Sources:** 51

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0173 | **Alabama Procurement Office**<br>State of Alabama | State solicitations, contracts, vendor registration, procurement rules and awards | Alabama | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Alabama government contracts | [Open](https://purchasing.alabama.gov/) |
| GOV-0174 | **Alaska Procurement Office**<br>State of Alaska | State solicitations, contracts, vendor registration, procurement rules and awards | Alaska | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Alaska government contracts | [Open](https://doa.alaska.gov/dgs/purchasing/) |
| GOV-0175 | **Arizona Procurement Office**<br>State of Arizona | State solicitations, contracts, vendor registration, procurement rules and awards | Arizona | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Arizona government contracts | [Open](https://spo.az.gov/) |
| GOV-0176 | **Arkansas Procurement Office**<br>State of Arkansas | State solicitations, contracts, vendor registration, procurement rules and awards | Arkansas | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Arkansas government contracts | [Open](https://www.transform.ar.gov/procurement/) |
| GOV-0177 | **California Procurement Office**<br>State of California | State solicitations, contracts, vendor registration, procurement rules and awards | California | Portal; API/export varies | Semi-auto | P2 | Very High | Discover and monitor California government contracts | [Open](https://www.dgs.ca.gov/PD) |
| GOV-0178 | **Colorado Procurement Office**<br>State of Colorado | State solicitations, contracts, vendor registration, procurement rules and awards | Colorado | Portal; API/export varies | Semi-auto | P2 | High | Discover and monitor Colorado government contracts | [Open](https://osc.colorado.gov/spco) |
| GOV-0179 | **Connecticut Procurement Office**<br>State of Connecticut | State solicitations, contracts, vendor registration, procurement rules and awards | Connecticut | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Connecticut government contracts | [Open](https://portal.ct.gov/das/procurement) |
| GOV-0180 | **Delaware Procurement Office**<br>State of Delaware | State solicitations, contracts, vendor registration, procurement rules and awards | Delaware | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Delaware government contracts | [Open](https://mymarketplace.delaware.gov/) |
| GOV-0181 | **Florida Procurement Office**<br>State of Florida | State solicitations, contracts, vendor registration, procurement rules and awards | Florida | Portal; API/export varies | Semi-auto | P2 | Very High | Discover and monitor Florida government contracts | [Open](https://www.dms.myflorida.com/business_operations/state_purchasing) |
| GOV-0182 | **Georgia Procurement Office**<br>State of Georgia | State solicitations, contracts, vendor registration, procurement rules and awards | Georgia | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Georgia government contracts | [Open](https://doas.ga.gov/state-purchasing) |
| GOV-0183 | **Hawaii Procurement Office**<br>State of Hawaii | State solicitations, contracts, vendor registration, procurement rules and awards | Hawaii | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Hawaii government contracts | [Open](https://spo.hawaii.gov/) |
| GOV-0184 | **Idaho Procurement Office**<br>State of Idaho | State solicitations, contracts, vendor registration, procurement rules and awards | Idaho | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Idaho government contracts | [Open](https://purchasing.idaho.gov/) |
| GOV-0185 | **Illinois Procurement Office**<br>State of Illinois | State solicitations, contracts, vendor registration, procurement rules and awards | Illinois | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Illinois government contracts | [Open](https://cms.illinois.gov/business/procurement.html) |
| GOV-0186 | **Indiana Procurement Office**<br>State of Indiana | State solicitations, contracts, vendor registration, procurement rules and awards | Indiana | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Indiana government contracts | [Open](https://www.in.gov/idoa/procurement/) |
| GOV-0187 | **Iowa Procurement Office**<br>State of Iowa | State solicitations, contracts, vendor registration, procurement rules and awards | Iowa | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Iowa government contracts | [Open](https://das.iowa.gov/procurement) |
| GOV-0188 | **Kansas Procurement Office**<br>State of Kansas | State solicitations, contracts, vendor registration, procurement rules and awards | Kansas | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Kansas government contracts | [Open](https://admin.ks.gov/offices/procurement-and-contracts) |
| GOV-0189 | **Kentucky Procurement Office**<br>State of Kentucky | State solicitations, contracts, vendor registration, procurement rules and awards | Kentucky | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Kentucky government contracts | [Open](https://finance.ky.gov/office-of-the-controller/office-of-procurement-services/) |
| GOV-0190 | **Louisiana Procurement Office**<br>State of Louisiana | State solicitations, contracts, vendor registration, procurement rules and awards | Louisiana | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Louisiana government contracts | [Open](https://www.doa.la.gov/doa/osp/) |
| GOV-0191 | **Maine Procurement Office**<br>State of Maine | State solicitations, contracts, vendor registration, procurement rules and awards | Maine | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Maine government contracts | [Open](https://www.maine.gov/dafs/bbm/procurementservices/home) |
| GOV-0192 | **Maryland Procurement Office**<br>State of Maryland | State solicitations, contracts, vendor registration, procurement rules and awards | Maryland | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Maryland government contracts | [Open](https://procurement.maryland.gov/) |
| GOV-0193 | **Massachusetts Procurement Office**<br>State of Massachusetts | State solicitations, contracts, vendor registration, procurement rules and awards | Massachusetts | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Massachusetts government contracts | [Open](https://www.mass.gov/orgs/operational-services-division) |
| GOV-0194 | **Michigan Procurement Office**<br>State of Michigan | State solicitations, contracts, vendor registration, procurement rules and awards | Michigan | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Michigan government contracts | [Open](https://www.michigan.gov/dtmb/procurement) |
| GOV-0195 | **Minnesota Procurement Office**<br>State of Minnesota | State solicitations, contracts, vendor registration, procurement rules and awards | Minnesota | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Minnesota government contracts | [Open](https://mn.gov/admin/government/purchasing-contracting/) |
| GOV-0196 | **Mississippi Procurement Office**<br>State of Mississippi | State solicitations, contracts, vendor registration, procurement rules and awards | Mississippi | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Mississippi government contracts | [Open](https://www.dfa.ms.gov/procurement-contracts) |
| GOV-0197 | **Missouri Procurement Office**<br>State of Missouri | State solicitations, contracts, vendor registration, procurement rules and awards | Missouri | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Missouri government contracts | [Open](https://oa.mo.gov/purchasing) |
| GOV-0198 | **Montana Procurement Office**<br>State of Montana | State solicitations, contracts, vendor registration, procurement rules and awards | Montana | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Montana government contracts | [Open](https://spb.mt.gov/) |
| GOV-0199 | **Nebraska Procurement Office**<br>State of Nebraska | State solicitations, contracts, vendor registration, procurement rules and awards | Nebraska | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Nebraska government contracts | [Open](https://das.nebraska.gov/materiel/purchasing.html) |
| GOV-0200 | **Nevada Procurement Office**<br>State of Nevada | State solicitations, contracts, vendor registration, procurement rules and awards | Nevada | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Nevada government contracts | [Open](https://purchasing.nv.gov/) |
| GOV-0201 | **New Hampshire Procurement Office**<br>State of New Hampshire | State solicitations, contracts, vendor registration, procurement rules and awards | New Hampshire | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor New Hampshire government contracts | [Open](https://das.nh.gov/purchasing/) |
| GOV-0202 | **New Jersey Procurement Office**<br>State of New Jersey | State solicitations, contracts, vendor registration, procurement rules and awards | New Jersey | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor New Jersey government contracts | [Open](https://www.nj.gov/treasury/purchase/) |
| GOV-0203 | **New Mexico Procurement Office**<br>State of New Mexico | State solicitations, contracts, vendor registration, procurement rules and awards | New Mexico | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor New Mexico government contracts | [Open](https://www.generalservices.state.nm.us/statepurchasing/) |
| GOV-0204 | **New York Procurement Office**<br>State of New York | State solicitations, contracts, vendor registration, procurement rules and awards | New York | Portal; API/export varies | Semi-auto | P2 | Very High | Discover and monitor New York government contracts | [Open](https://ogs.ny.gov/procurement) |
| GOV-0205 | **North Carolina Procurement Office**<br>State of North Carolina | State solicitations, contracts, vendor registration, procurement rules and awards | North Carolina | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor North Carolina government contracts | [Open](https://ncadmin.nc.gov/government-agencies/procurement) |
| GOV-0206 | **North Dakota Procurement Office**<br>State of North Dakota | State solicitations, contracts, vendor registration, procurement rules and awards | North Dakota | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor North Dakota government contracts | [Open](https://www.omb.nd.gov/doing-business-state/procurement) |
| GOV-0207 | **Ohio Procurement Office**<br>State of Ohio | State solicitations, contracts, vendor registration, procurement rules and awards | Ohio | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Ohio government contracts | [Open](https://procure.ohio.gov/) |
| GOV-0208 | **Oklahoma Procurement Office**<br>State of Oklahoma | State solicitations, contracts, vendor registration, procurement rules and awards | Oklahoma | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Oklahoma government contracts | [Open](https://oklahoma.gov/omes/services/purchasing.html) |
| GOV-0209 | **Oregon Procurement Office**<br>State of Oregon | State solicitations, contracts, vendor registration, procurement rules and awards | Oregon | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Oregon government contracts | [Open](https://www.oregon.gov/DAS/Procurement/Pages/Index.aspx) |
| GOV-0210 | **Pennsylvania Procurement Office**<br>State of Pennsylvania | State solicitations, contracts, vendor registration, procurement rules and awards | Pennsylvania | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Pennsylvania government contracts | [Open](https://www.dgs.pa.gov/Materials-Services-Procurement/Pages/default.aspx) |
| GOV-0211 | **Rhode Island Procurement Office**<br>State of Rhode Island | State solicitations, contracts, vendor registration, procurement rules and awards | Rhode Island | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Rhode Island government contracts | [Open](https://www.ridop.ri.gov/) |
| GOV-0212 | **South Carolina Procurement Office**<br>State of South Carolina | State solicitations, contracts, vendor registration, procurement rules and awards | South Carolina | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor South Carolina government contracts | [Open](https://procurement.sc.gov/) |
| GOV-0213 | **South Dakota Procurement Office**<br>State of South Dakota | State solicitations, contracts, vendor registration, procurement rules and awards | South Dakota | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor South Dakota government contracts | [Open](https://boa.sd.gov/central-services/procurement-management/) |
| GOV-0214 | **Tennessee Procurement Office**<br>State of Tennessee | State solicitations, contracts, vendor registration, procurement rules and awards | Tennessee | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Tennessee government contracts | [Open](https://www.tn.gov/generalservices/procurement.html) |
| GOV-0215 | **Texas Procurement Office**<br>State of Texas | State solicitations, contracts, vendor registration, procurement rules and awards | Texas | Portal; API/export varies | Semi-auto | P2 | Very High | Discover and monitor Texas government contracts | [Open](https://comptroller.texas.gov/purchasing/) |
| GOV-0216 | **Utah Procurement Office**<br>State of Utah | State solicitations, contracts, vendor registration, procurement rules and awards | Utah | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Utah government contracts | [Open](https://purchasing.utah.gov/) |
| GOV-0217 | **Vermont Procurement Office**<br>State of Vermont | State solicitations, contracts, vendor registration, procurement rules and awards | Vermont | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Vermont government contracts | [Open](https://bgs.vermont.gov/purchasing) |
| GOV-0218 | **Virginia Procurement Office**<br>State of Virginia | State solicitations, contracts, vendor registration, procurement rules and awards | Virginia | Portal; API/export varies | Semi-auto | P2 | High | Discover and monitor Virginia government contracts | [Open](https://dgs.virginia.gov/procurement) |
| GOV-0219 | **Washington Procurement Office**<br>State of Washington | State solicitations, contracts, vendor registration, procurement rules and awards | Washington | Portal; API/export varies | Semi-auto | P2 | High | Discover and monitor Washington government contracts | [Open](https://des.wa.gov/services/contracting-purchasing) |
| GOV-0220 | **West Virginia Procurement Office**<br>State of West Virginia | State solicitations, contracts, vendor registration, procurement rules and awards | West Virginia | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor West Virginia government contracts | [Open](https://www.state.wv.us/admin/purchase/) |
| GOV-0221 | **Wisconsin Procurement Office**<br>State of Wisconsin | State solicitations, contracts, vendor registration, procurement rules and awards | Wisconsin | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Wisconsin government contracts | [Open](https://doa.wi.gov/Pages/StateEmployees/Procurement.aspx) |
| GOV-0222 | **Wyoming Procurement Office**<br>State of Wyoming | State solicitations, contracts, vendor registration, procurement rules and awards | Wyoming | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor Wyoming government contracts | [Open](https://ai.wyo.gov/divisions/general-services/purchasing) |
| GOV-0223 | **District of Columbia Procurement Office**<br>State of District of Columbia | State solicitations, contracts, vendor registration, procurement rules and awards | District of Columbia | Portal; API/export varies | Semi-auto | P3 | High | Discover and monitor District of Columbia government contracts | [Open](https://ocp.dc.gov/) |

## Labor Statistics

**Sources:** 4

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0084 | **BLS API**<br>BLS | Employment, wages, prices and productivity | US federal | REST API | Auto | P1 | High | Detect labor shifts | [Open](https://www.bls.gov/developers/) |
| GOV-0085 | **BLS QCEW**<br>BLS | County industry employment and wages | US federal | Bulk CSV | Auto | P1 | High | Find local industry growth | [Open](https://www.bls.gov/cew/downloadable-data-files.htm) |
| GOV-0086 | **BLS OEWS**<br>BLS | Occupational employment and wages | US federal | Bulk XLSX | Auto | P1 | High | Price workforce | [Open](https://www.bls.gov/oes/tables.htm) |
| GOV-0087 | **BLS JOLTS**<br>BLS | Openings, hires and separations | US federal | CSV / API | Auto | P1 | High | Detect hiring pressure | [Open](https://www.bls.gov/jlt/data.htm) |

## Banking

**Sources:** 3

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0075 | **FDIC BankFind API**<br>FDIC | Banks, branches, financials and failures | US federal | REST API | Auto | P1 | High | Detect bank growth and distress | [Open](https://banks.data.fdic.gov/docs/) |
| GOV-0076 | **FDIC Failed Bank List**<br>FDIC | Failed banks and acquirers | US federal | HTML / CSV | Auto | P2 | High | Find disruption and asset transfers | [Open](https://www.fdic.gov/bank-failures/failed-bank-list) |
| GOV-0077 | **FFIEC Call Reports**<br>FFIEC | Bank regulatory financial filings | US federal | Bulk / portal | Auto | P1 | High | Score bank health | [Open](https://cdr.ffiec.gov/public/) |

## Courts

**Sources:** 3

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0056 | **CourtListener API**<br>Free Law Project | Opinions, dockets, judges and citations | US federal | REST API | Auto | P1 | High | Track government litigation | [Open](https://www.courtlistener.com/help/api/) |
| GOV-0057 | **PACER Case Locator**<br>U.S. Courts | Federal dockets and filings | US federal | Portal | Semi-auto | P2 | High | Find disputes and bankruptcies | [Open](https://pcl.uscourts.gov/) |
| GOV-0058 | **Supreme Court Opinions**<br>U.S. Supreme Court | Opinions and orders | US federal | HTML / PDF | Semi-auto | P2 | High | Detect high-impact legal changes | [Open](https://www.supremecourt.gov/opinions/opinions.aspx) |

## Cybersecurity

**Sources:** 3

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0158 | **CISA KEV Catalog**<br>CISA | Actively exploited vulnerabilities | US federal | JSON / CSV | Auto | P2 | High | Find remediation opportunities | [Open](https://www.cisa.gov/known-exploited-vulnerabilities-catalog) |
| GOV-0159 | **CISA Advisories**<br>CISA | Cyber advisories and alerts | US federal | RSS / HTML | Auto | P2 | High | Monitor threats | [Open](https://www.cisa.gov/news-events/cybersecurity-advisories) |
| GOV-0160 | **NVD API**<br>NIST | CVE vulnerabilities and severity | US federal | REST API | Auto | P1 | High | Find security demand | [Open](https://nvd.nist.gov/developers/vulnerabilities) |

## Defense Procurement

**Sources:** 3

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0032 | **Defense Pricing and Contracting**<br>DoD | DoD contracting policy and guidance | US federal | HTML / documents | Semi-auto | P2 | High | Detect defense procurement changes | [Open](https://www.acq.osd.mil/asda/dpc/) |
| GOV-0033 | **DLA DIBBS**<br>DLA | DLA bids and awards | US federal | Portal | Semi-auto | P2 | High | Find supply and manufacturing bids | [Open](https://www.dibbs.bsm.dla.mil/) |
| GOV-0034 | **PIEE Solicitation Module**<br>DoD | DoD solicitations and procurement workflows | US federal | Authenticated portal | Semi-auto | P2 | High | Find and respond to defense opportunities | [Open](https://piee.eb.mil/) |

## Fiscal Data

**Sources:** 3

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0069 | **Treasury Fiscal Data API**<br>U.S. Treasury | Debt, revenue, spending, interest and financial accounts | US federal | REST API | Auto | P1 | High | Track fiscal flows | [Open](https://fiscaldata.treasury.gov/api/fiscal_service/) |
| GOV-0070 | **Daily Treasury Statement**<br>U.S. Treasury | Daily operating cash and debt transactions | US federal | API / CSV | Auto | P1 | High | Monitor federal cash flow | [Open](https://fiscaldata.treasury.gov/datasets/daily-treasury-statement/) |
| GOV-0071 | **Monthly Treasury Statement**<br>U.S. Treasury | Monthly receipts, outlays and deficit | US federal | API / CSV | Auto | P1 | High | Find spending growth | [Open](https://fiscaldata.treasury.gov/datasets/monthly-treasury-statement/) |

## Grants

**Sources:** 3

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0023 | **Grants.gov Search**<br>HHS / Grants.gov | Grant notices, eligibility, deadlines and funding | US federal | Search API / portal | Auto | P2 | Very High | Discover federal grants | [Open](https://www.grants.gov/search-grants) |
| GOV-0024 | **Grants.gov S2S**<br>HHS / Grants.gov | Grant opportunity and application services | US federal | REST / SOAP | Semi-auto | P2 | Very High | Automate grant workflows | [Open](https://www.grants.gov/web/grants/s2s/grantor_system_to_system.html) |
| GOV-0025 | **Simpler.Grants.gov API**<br>GSA | Modern federal grant search and details | US federal | REST API | Auto | P1 | Very High | Build grant scout feeds | [Open](https://wiki.simpler.grants.gov/product/api) |

## Healthcare

**Sources:** 3

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0100 | **CMS Data API**<br>CMS | Provider, facility, utilization and payment data | US federal | REST API / bulk | Auto | P1 | Very High | Find care and reimbursement opportunities | [Open](https://data.cms.gov/api-docs) |
| GOV-0101 | **Care Compare Data**<br>CMS | Provider quality and facility data | US federal | API / CSV | Auto | P1 | Very High | Find quality and capacity gaps | [Open](https://data.cms.gov/provider-data/) |
| GOV-0103 | **Medicaid Data**<br>CMS | Enrollment, expenditure and quality data | US federal | API / CSV | Auto | P1 | Very High | Track state health markets | [Open](https://data.medicaid.gov/) |

## R&D Funding

**Sources:** 3

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0026 | **SBIR.gov Solicitations**<br>SBA | SBIR and STTR solicitations | US federal | Portal / feed | Semi-auto | P2 | High | Find research commercialization topics | [Open](https://www.sbir.gov/solicitations) |
| GOV-0028 | **NSF Seed Fund**<br>NSF | Commercialization funding programs | US federal | Portal | Semi-auto | P2 | High | Find startup funding | [Open](https://seedfund.nsf.gov/) |
| GOV-0029 | **NIH SEED**<br>NIH | Biomedical small-business funding | US federal | Portal | Semi-auto | P2 | High | Find health commercialization opportunities | [Open](https://seed.nih.gov/) |

## Regulations

**Sources:** 3

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0041 | **Federal Register API**<br>Office of the Federal Register | Proposed rules, final rules, notices and presidential documents | US federal | REST API | Auto | P1 | Very High | Detect regulatory change | [Open](https://www.federalregister.gov/developers/documentation/api/v1) |
| GOV-0042 | **Federal Register Bulk Data**<br>GPO / OFR | Daily Federal Register editions | US federal | Bulk XML | Auto | P1 | Very High | Build regulatory archive | [Open](https://www.govinfo.gov/bulkdata/FR) |
| GOV-0044 | **eCFR API**<br>OFR / GPO | Current CFR structure and text | US federal | REST API | Auto | P1 | Very High | Monitor binding regulation changes | [Open](https://www.ecfr.gov/developers/documentation/api/v1) |

## Research Funding

**Sources:** 3

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0116 | **NIH RePORTER API**<br>NIH | Projects, awards, investigators and organizations | US federal | REST API | Auto | P1 | Very High | Find funded research | [Open](https://api.reporter.nih.gov/) |
| GOV-0117 | **NIH ExPORTER**<br>NIH | NIH projects and publications | US federal | Bulk CSV | Auto | P1 | Very High | Build funding history | [Open](https://reporter.nih.gov/exporter) |
| GOV-0164 | **NSF Award Search API**<br>NSF | Awards, investigators and organizations | US federal | REST API | Auto | P1 | Very High | Find funded research | [Open](https://www.research.gov/common/webapi/awardapisearch-v1.htm) |

## Awards

**Sources:** 2

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0008 | **SAM.gov Contract Data**<br>GSA | Contract awards and modifications | US federal | Portal / export | Semi-auto | P2 | Very High | Find incumbents and recompetes | [Open](https://sam.gov/content/contract-data) |
| GOV-0011 | **FPDS Legacy**<br>GSA | Historical federal procurement data | US federal | Portal / bulk | Semi-auto | P2 | Very High | Research older award actions | [Open](https://www.fpds.gov/) |

## Business Activity

**Sources:** 2

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0093 | **Business Formation Statistics**<br>Census Bureau | Business applications and formations | US federal | API / CSV | Auto | P1 | High | Detect startup activity | [Open](https://www.census.gov/econ/bfs/data.html) |
| GOV-0094 | **County Business Patterns**<br>Census Bureau | Establishments, employment and payroll | US federal | API / CSV | Auto | P1 | High | Identify industry gaps | [Open](https://www.census.gov/programs-surveys/cbp/data.html) |

## Committees

**Sources:** 2

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0051 | **House Committee Repository**<br>U.S. House | Hearings, testimony and meeting documents | US federal | HTML / XML | Auto | P2 | High | Detect policy development | [Open](https://docs.house.gov/) |
| GOV-0052 | **Senate Hearings**<br>U.S. Senate | Hearings and schedules | US federal | HTML / RSS | Auto | P2 | High | Monitor oversight activity | [Open](https://www.senate.gov/committees/hearings_meetings.htm) |

## Compliance

**Sources:** 2

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0005 | **SAM.gov Exclusions API**<br>GSA | Federal exclusions, suspensions and debarments | US federal | REST API | Auto | P1 | High | Screen counterparties | [Open](https://open.gsa.gov/api/exclusions-api/) |
| GOV-0006 | **SAM.gov Exclusions Extracts**<br>GSA | Bulk exclusions records | US federal | Bulk download | Auto | P1 | High | Maintain exclusion history | [Open](https://sam.gov/data-services/Exclusions) |

## Defense Research

**Sources:** 2

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0035 | **DARPA Opportunities**<br>DARPA | BAAs, solicitations and research opportunities | US federal | HTML / RSS | Auto | P2 | High | Find frontier-technology funding | [Open](https://www.darpa.mil/work-with-us/opportunities) |
| GOV-0036 | **SAM.gov DoD Opportunities**<br>DoD / GSA | DoD solicitations published through SAM | US federal | REST API / portal | Auto | P1 | High | Create defense-specific scouts | [Open](https://sam.gov/content/opportunities) |

## Demographics

**Sources:** 2

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0090 | **Census Data API**<br>Census Bureau | Population, housing and economic data | US federal | REST API | Auto | P1 | High | Analyze markets | [Open](https://www.census.gov/data/developers/data-sets.html) |
| GOV-0091 | **ACS API**<br>Census Bureau | Income, housing, commuting and demographics | US federal | REST API | Auto | P1 | High | Rank local markets | [Open](https://www.census.gov/data/developers/data-sets/acs-5year.html) |

## Education

**Sources:** 2

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0161 | **College Scorecard API**<br>Education Department | College cost, outcomes and debt | US federal | REST API | Auto | P1 | High | Analyze education markets | [Open](https://collegescorecard.ed.gov/data/api-documentation/) |
| GOV-0162 | **NCES Data Tools**<br>NCES | Schools, districts and colleges | US federal | APIs / downloads | Auto | P1 | High | Map education demand | [Open](https://nces.ed.gov/datatools/) |

## Energy

**Sources:** 2

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0143 | **EIA Open Data API**<br>EIA | Electricity, petroleum and gas data | US federal | REST API | Auto | P1 | Very High | Track energy markets | [Open](https://www.eia.gov/opendata/) |
| GOV-0144 | **NREL Developer APIs**<br>NREL | Solar, wind, rates and fuels | US federal | REST APIs | Auto | P1 | Very High | Find renewable projects | [Open](https://developer.nrel.gov/) |

## Entities

**Sources:** 2

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0003 | **SAM.gov Entity API**<br>GSA | UEI, CAGE, registration, business types and assertions | US federal | REST API | Auto | P1 | High | Find contractors and registration changes | [Open](https://open.gsa.gov/api/entity-api/) |
| GOV-0004 | **SAM.gov Entity Public Extracts**<br>GSA | Public entity registration data | US federal | Bulk download | Auto | P1 | High | Build contractor master records | [Open](https://sam.gov/data-services/Entity%20Registration) |

## Financial Filings

**Sources:** 2

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0078 | **SEC EDGAR APIs**<br>SEC | Company submissions and XBRL facts | US federal | REST JSON | Semi-auto | P2 | High | Detect filings and capital shifts | [Open](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) |
| GOV-0079 | **SEC EDGAR Full-Text Search**<br>SEC | Full-text filings | US federal | Search / JSON | Semi-auto | P2 | High | Find strategic disclosures | [Open](https://www.sec.gov/edgar/search/) |

## Legislation

**Sources:** 2

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0047 | **Congress.gov API**<br>Library of Congress | Bills, amendments, members, committees and actions | US federal | REST API | Auto | P1 | Very High | Detect legislative movement | [Open](https://api.congress.gov/) |
| GOV-0048 | **Congress.gov Data Offsite**<br>Library of Congress | Legislative data access | US federal | API / bulk guidance | Auto | P2 | Very High | Backfill legislative history | [Open](https://www.congress.gov/help/using-data-offsite) |

## Prices

**Sources:** 2

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0088 | **BLS CPI**<br>BLS | Consumer prices | US federal | API / downloads | Auto | P1 | High | Track inflation | [Open](https://www.bls.gov/cpi/data.htm) |
| GOV-0089 | **BLS PPI**<br>BLS | Producer prices | US federal | API / downloads | Auto | P1 | High | Track supplier costs | [Open](https://www.bls.gov/ppi/data.htm) |

## Procurement

**Sources:** 2

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0001 | **SAM.gov Contract Opportunities**<br>GSA | Federal solicitations, notices, amendments, deadlines, set-asides and attachments | US federal | REST API | Auto | P1 | Very High | Find and monitor federal bid opportunities | [Open](https://open.gsa.gov/api/get-opportunities-public-api/) |
| GOV-0002 | **SAM.gov Opportunities Data Services**<br>GSA | Active, archived and versioned opportunity records | US federal | Bulk download | Auto | P1 | Very High | Backfill opportunity history | [Open](https://sam.gov/data-services/Contract%20Opportunities) |

## Public Health

**Sources:** 2

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0107 | **CDC Data API**<br>CDC | Disease and public-health datasets | US federal | Socrata API | Auto | P1 | High | Detect health demand | [Open](https://data.cdc.gov/) |
| GOV-0108 | **CDC WONDER**<br>CDC | Mortality, births and disease statistics | US federal | Query / export | Semi-auto | P2 | High | Find disparities | [Open](https://wonder.cdc.gov/) |

## Publications

**Sources:** 2

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0045 | **GovInfo API**<br>GPO | Official legislative, regulatory and judicial publications | US federal | REST API | Auto | P1 | High | Search government documents | [Open](https://api.govinfo.gov/docs/) |
| GOV-0046 | **GovInfo Bulk Data**<br>GPO | Bills, CFR, FR, Congressional Record and more | US federal | Bulk download | Auto | P1 | High | Build official publication archive | [Open](https://www.govinfo.gov/bulkdata) |

## Spending

**Sources:** 2

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0009 | **USAspending API**<br>U.S. Treasury | Contracts, grants, loans, transactions, recipients and agencies | US federal | REST API | Auto | P1 | Very High | Analyze award history and agency spend | [Open](https://api.usaspending.gov/) |
| GOV-0010 | **USAspending Download Center**<br>U.S. Treasury | Award, transaction and subaward files | US federal | Bulk download | Auto | P1 | Very High | Build historical spending warehouse | [Open](https://www.usaspending.gov/download_center/custom_award_data) |

## Statutes

**Sources:** 2

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0067 | **U.S. Code Downloads**<br>House Law Revision Counsel | Current codified statutes | US federal | Bulk XML / text | Auto | P1 | High | Link opportunities to law | [Open](https://uscode.house.gov/download/download.shtml) |
| GOV-0068 | **Statutes at Large**<br>GovInfo | Enacted public and private laws | US federal | API / bulk | Auto | P2 | High | Track enacted law | [Open](https://www.govinfo.gov/app/collection/STATUTE) |

## Surplus Assets

**Sources:** 2

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0171 | **GSA Auctions**<br>GSA | Federal surplus property and equipment | US federal | Portal | Semi-auto | P2 | High | Find discounted assets | [Open](https://gsaauctions.gov/) |
| GOV-0172 | **USA.gov Auctions Directory**<br>USA.gov | Government auctions and sales | US federal | Directory | Semi-auto | P2 | High | Discover asset sales | [Open](https://www.usa.gov/auctions-and-sales) |

## Trade

**Sources:** 2

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0096 | **Census International Trade API**<br>Census Bureau | Imports and exports by product and country | US federal | REST API | Auto | P1 | High | Find trade opportunities | [Open](https://www.census.gov/data/developers/data-sets/international-trade.html) |
| GOV-0156 | **International Trade Administration APIs**<br>Commerce | Trade leads, tariffs and market data | US federal | REST APIs | Auto | P1 | High | Find export opportunities | [Open](https://developer.trade.gov/) |

## Votes

**Sources:** 2

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0049 | **House Roll Call Votes**<br>U.S. House | House roll-call votes | US federal | XML / HTML | Auto | P2 | High | Analyze coalitions | [Open](https://clerk.house.gov/Votes) |
| GOV-0050 | **Senate Roll Call Votes**<br>U.S. Senate | Senate roll-call votes | US federal | XML / HTML | Auto | P2 | High | Analyze vote likelihood | [Open](https://www.senate.gov/legislative/votes_new.htm) |

## Acquisition

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0020 | **Acquisition Gateway API**<br>GSA | Acquisition guidance and public listings | US federal | REST API | Auto | P1 | High | Research acquisition practices | [Open](https://open.gsa.gov/api/ag-api/) |

## Acquisition Rules

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0031 | **Acquisition.gov**<br>FAR Council / GSA | FAR and agency supplements | US federal | HTML / XML | Auto | P2 | High | Track acquisition rule changes | [Open](https://www.acquisition.gov/) |

## Agency Directory

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0038 | **Federal Agency Directory API**<br>GSA | Federal agency contacts and directory data | US federal | REST API | Auto | P1 | High | Normalize agencies and offices | [Open](https://open.gsa.gov/api/federal-agency-directory-api/) |

## Agriculture

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0140 | **USDA NASS Quick Stats API**<br>USDA | Crop, livestock and price data | US federal | REST API | Auto | P1 | High | Detect agricultural shifts | [Open](https://quickstats.nass.usda.gov/api) |

## Air Quality

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0126 | **EPA AQS API**<br>EPA | Air monitoring data | US federal | REST API | Auto | P1 | High | Monitor pollution | [Open](https://aqs.epa.gov/aqsweb/documents/data_api.html) |

## Archives

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0168 | **National Archives API**<br>NARA | Archival records and digital objects | US federal | REST API | Auto | P1 | High | Research historical records | [Open](https://www.archives.gov/developer) |

## Assistance

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0007 | **SAM.gov Assistance Listings API**<br>GSA | Federal assistance programs and eligibility | US federal | REST API | Auto | P1 | High | Match organizations to programs | [Open](https://open.gsa.gov/api/assistance-listings-api/) |

## Aviation

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0150 | **FAA Data and Research**<br>FAA | Airports, traffic and safety data | US federal | Downloads / APIs | Auto | P1 | High | Find aviation opportunities | [Open](https://www.faa.gov/data_research) |

## Behavioral Health

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0120 | **SAMHSA Data**<br>SAMHSA | Mental health and substance-use data | US federal | Downloads | Semi-auto | P2 | High | Find behavioral health demand | [Open](https://www.samhsa.gov/data/data-we-collect) |

## Biologics

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0113 | **FDA Purple Book**<br>FDA | Biologics and biosimilars | US federal | Portal / downloads | Semi-auto | P2 | High | Track biosimilar opportunities | [Open](https://purplebooksearch.fda.gov/) |

## Biomedical Literature

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0118 | **PubMed E-utilities**<br>NLM | Biomedical publications | US federal | REST API | Auto | P1 | High | Track emerging science | [Open](https://www.ncbi.nlm.nih.gov/books/NBK25501/) |

## Broadband

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0152 | **FCC Broadband Data**<br>FCC | Broadband availability and providers | US federal | Bulk GIS / CSV | Auto | P1 | High | Find underserved markets | [Open](https://broadbandmap.fcc.gov/data-download) |

## Budget

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0053 | **CBO Data**<br>Congressional Budget Office | Budget projections and cost estimates | US federal | CSV / XLSX / RSS | Auto | P2 | High | Find funded policy areas | [Open](https://www.cbo.gov/data) |

## Certifications

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0016 | **SBA Certifications**<br>SBA | 8(a), WOSB, HUBZone and other certifications | US federal | Portal | Semi-auto | P2 | High | Track set-aside eligibility | [Open](https://certifications.sba.gov/) |

## Climate

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0132 | **NOAA Climate Data API**<br>NOAA | Historical climate observations | US federal | REST API | Auto | P1 | High | Model climate demand | [Open](https://www.ncdc.noaa.gov/cdo-web/webservices/v2) |

## Clinical Research

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0115 | **ClinicalTrials.gov API**<br>NLM | Trials, sponsors, interventions and sites | US federal | REST API | Auto | P1 | High | Track emerging treatments | [Open](https://clinicaltrials.gov/data-api/about-api) |

## Commodity Markets

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0082 | **CFTC Commitments of Traders**<br>CFTC | Futures and options positions | US federal | CSV downloads | Auto | P2 | High | Detect commodity positioning | [Open](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm) |

## Communications

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0151 | **FCC Developer APIs**<br>FCC | Licenses, broadband and filings | US federal | REST APIs / downloads | Auto | P1 | High | Track telecom opportunities | [Open](https://www.fcc.gov/reports-research/developers) |

## Community Risk

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0110 | **CDC Social Vulnerability Index**<br>CDC / ATSDR | Community vulnerability indicators | US federal | GIS / CSV | Auto | P2 | High | Prioritize vulnerable markets | [Open](https://www.atsdr.cdc.gov/place-health/php/svi/) |

## Construction

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0095 | **Building Permits Survey**<br>Census Bureau | Residential permit activity | US federal | API / CSV | Auto | P1 | High | Detect construction growth | [Open](https://www.census.gov/construction/bps/) |

## Contract Vehicles

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0018 | **GSA eLibrary**<br>GSA | Schedules, SINs, vendors and contracts | US federal | HTML portal | Semi-auto | P2 | High | Find incumbents and vehicle access | [Open](https://www.gsaelibrary.gsa.gov/) |

## Disasters

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0129 | **OpenFEMA API**<br>FEMA | Disasters, claims, grants and assistance | US federal | REST API | Auto | P1 | High | Find recovery demand | [Open](https://www.fema.gov/about/openfema/api) |

## Economic Indicators

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0073 | **FRED API**<br>Federal Reserve Bank of St. Louis | Economic time series | US federal | REST API | Auto | P1 | High | Build macro scouts | [Open](https://fred.stlouisfed.org/docs/api/fred/) |

## Economic Statistics

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0083 | **BEA API**<br>BEA | GDP, industry, trade and regional accounts | US federal | REST API | Auto | P1 | High | Find regional growth | [Open](https://apps.bea.gov/api/) |

## Energy Regulation

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0146 | **FERC eLibrary**<br>FERC | Dockets, filings and orders | US federal | Portal / documents | Semi-auto | P2 | High | Track infrastructure cases | [Open](https://elibrary.ferc.gov/eLibrary/search) |

## Environment

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0123 | **EPA Envirofacts API**<br>EPA | Facilities, emissions, waste and water data | US federal | REST API | Auto | P1 | High | Find liabilities | [Open](https://www.epa.gov/enviro/envirofacts-data-service-api) |

## Environmental Compliance

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0124 | **EPA ECHO Web Services**<br>EPA | Compliance, enforcement and permits | US federal | REST services | Semi-auto | P2 | High | Find remediation demand | [Open](https://echo.epa.gov/tools/web-services) |

## Executive Policy

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0063 | **White House Presidential Actions**<br>White House | Executive orders, memoranda and proclamations | US federal | HTML / RSS | Auto | P2 | High | Detect immediate policy shifts | [Open](https://www.whitehouse.gov/presidential-actions/) |

## Export Controls

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0155 | **Consolidated Screening List**<br>Commerce | Export restriction lists | US federal | REST API / downloads | Auto | P1 | High | Screen trade risk | [Open](https://www.trade.gov/consolidated-screening-list) |

## FOIA

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0169 | **FOIA.gov API**<br>DOJ | Agency FOIA contacts and statistics | US federal | REST API | Auto | P1 | High | Plan targeted records requests | [Open](https://www.foia.gov/developer/) |

## Facilities

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0128 | **EPA Facility Registry Service**<br>EPA | Cross-program facility identities | US federal | REST / bulk | Semi-auto | P2 | High | Resolve regulated facilities | [Open](https://www.epa.gov/frs/frs-data-resources) |

## Federal Holidays

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0040 | **OPM Operating Status**<br>OPM | Federal operating status | US federal | RSS / JSON-like feed | Auto | P2 | High | Trigger operational alerts | [Open](https://www.opm.gov/policy-data-oversight/snow-dismissal-procedures/current-status/) |

## Federal Jobs

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0037 | **USAJOBS API**<br>OPM | Federal job openings and occupations | US federal | REST API | Auto | P1 | High | Detect agency hiring demand | [Open](https://developer.usajobs.gov/) |

## Federal Property

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0170 | **Federal Real Property Profile**<br>GSA | Federal property and utilization | US federal | Downloads / reports | Semi-auto | P2 | High | Find underused assets | [Open](https://www.gsa.gov/policy-regulations/policy/real-property-policy/asset-management/federal-real-property-profile-frpp) |

## Federal Workforce

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0099 | **FedScope**<br>OPM | Federal employment and occupations | US federal | Downloads / cube | Semi-auto | P2 | High | Find agency staffing shifts | [Open](https://www.fedscope.opm.gov/) |

## Finance

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0074 | **Federal Reserve Data Download Program**<br>Federal Reserve Board | Rates, credit, banking and monetary data | US federal | CSV / XML | Auto | P2 | High | Track credit shifts | [Open](https://www.federalreserve.gov/datadownload/) |

## Flood Risk

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0130 | **FEMA NFHL**<br>FEMA | Official flood zones | US federal | GIS / download | Auto | P2 | High | Score location risk | [Open](https://www.fema.gov/flood-maps/national-flood-hazard-layer) |

## Food

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0141 | **FoodData Central API**<br>USDA | Food composition and branded foods | US federal | REST API | Auto | P1 | High | Analyze food markets | [Open](https://fdc.nal.usda.gov/api-guide.html) |

## Foreign Influence

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0062 | **FARA Search**<br>DOJ | Foreign-agent registrations and filings | US federal | Portal / documents | Semi-auto | P2 | High | Map foreign influence | [Open](https://efile.fara.gov/ords/fara/f?p=1381:1) |

## Funds

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0081 | **SEC Investment Company Data**<br>SEC | Fund filings and structured data | US federal | Bulk / XML | Auto | P1 | High | Track fund changes | [Open](https://www.sec.gov/data-research/sec-markets-data/investment-company-data-resources) |

## Geography

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0092 | **TIGER/Line**<br>Census Bureau | Boundaries, roads and geography | US federal | Bulk GIS | Auto | P1 | High | Spatially join records | [Open](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html) |

## Geologic Hazards

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0136 | **USGS Earthquake API**<br>USGS | Earthquake events | US federal | REST API | Auto | P1 | High | Trigger disaster scouts | [Open](https://earthquake.usgs.gov/fdsnws/event/1/) |

## Geospatial

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0137 | **USGS National Map**<br>USGS | Elevation, imagery and structures | US federal | REST API / GIS | Auto | P1 | High | Enrich location analysis | [Open](https://apps.nationalmap.gov/tnmaccess/) |

## Government Finance

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0097 | **Census Government Finance**<br>Census Bureau | State and local revenues, spending and debt | US federal | API / downloads | Auto | P1 | High | Find fiscal stress | [Open](https://www.census.gov/programs-surveys/gov-finances/data.html) |

## Hazard Risk

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0131 | **FEMA National Risk Index**<br>FEMA | Community natural-hazard risk | US federal | GIS / download | Auto | P2 | High | Rank hazard exposure | [Open](https://www.fema.gov/flood-maps/products-tools/national-risk-index) |

## Health Products

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0111 | **openFDA APIs**<br>FDA | Drug, device and food events, recalls and labels | US federal | REST API | Auto | P1 | High | Detect product risk | [Open](https://open.fda.gov/apis/) |

## Healthcare Capacity

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0119 | **HRSA Data Warehouse**<br>HRSA | Workforce, shortage areas, facilities and grants | US federal | API / GIS / CSV | Auto | P1 | High | Find shortage markets | [Open](https://data.hrsa.gov/) |

## Healthcare Finance

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0106 | **HCRIS Cost Reports**<br>CMS | Provider cost reports | US federal | Bulk files | Auto | P1 | High | Find distressed facilities | [Open](https://www.cms.gov/data-research/statistics-trends-and-reports/cost-reports) |

## Healthcare Payments

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0102 | **Medicare Physician Data**<br>CMS | Provider services and payments | US federal | API / CSV | Auto | P1 | High | Find specialty demand | [Open](https://data.cms.gov/provider-summary-by-type-of-service/medicare-physician-other-practitioners) |

## Healthcare Providers

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0105 | **NPPES NPI Files**<br>CMS | Provider identities and taxonomy | US federal | Bulk CSV | Auto | P1 | High | Build provider directory | [Open](https://download.cms.gov/nppes/NPI_Files.html) |

## Healthcare Relationships

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0104 | **Open Payments**<br>CMS | Industry payments to clinicians | US federal | Socrata API | Auto | P1 | High | Map commercial relationships | [Open](https://openpaymentsdata.cms.gov/) |

## Higher Education

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0163 | **IPEDS Data Center**<br>NCES | Enrollment, finance and staffing | US federal | Bulk downloads | Auto | P1 | High | Find institutional trends | [Open](https://nces.ed.gov/ipeds/use-the-data) |

## IT Spending

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0022 | **IT Dashboard**<br>OMB / GSA | Agency IT portfolios and performance | US federal | Portal / downloads | Semi-auto | P2 | High | Find large or troubled IT programs | [Open](https://itdashboard.gov/) |

## Immigration

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0157 | **USCIS Data**<br>USCIS | Applications, approvals and processing times | US federal | Downloads | Semi-auto | P2 | High | Track workforce migration | [Open](https://www.uscis.gov/tools/reports-and-studies/immigration-and-citizenship-data) |

## Integrity

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0012 | **FAPIIS**<br>GSA | Contractor integrity and performance information | US federal | Portal | Semi-auto | P2 | High | Assess contractor risk | [Open](https://sam.gov/content/fapiis) |

## Investment Advisers

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0080 | **Investment Adviser Public Disclosure**<br>SEC | Registered advisers and filings | US federal | Portal / downloads | Semi-auto | P2 | High | Map advisers | [Open](https://adviserinfo.sec.gov/) |

## Judicial Statistics

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0059 | **U.S. Courts Data Tables**<br>U.S. Courts | Court and bankruptcy statistics | US federal | CSV / XLSX | Auto | P2 | High | Find litigation trends | [Open](https://www.uscourts.gov/statistics-reports/data-tables) |

## Justice

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0153 | **FBI Crime Data API**<br>FBI | Crime and arrest data | US federal | REST API | Auto | P1 | High | Find public-safety demand | [Open](https://cde.ucr.cjis.gov/LATEST/webapp/#/pages/docApi) |

## Lobbying

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0061 | **Lobbying Disclosure Database**<br>Senate / House | Lobbying registrations and reports | US federal | Portal / downloads | Semi-auto | P2 | High | Track influence and policy priorities | [Open](https://lda.senate.gov/system/public/) |

## Local Health

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0109 | **CDC PLACES**<br>CDC | Small-area chronic disease measures | US federal | API / GIS | Auto | P1 | High | Find care gaps | [Open](https://www.cdc.gov/places/) |

## Management Policy

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0064 | **OMB Circulars**<br>OMB | Budget, grants and management directives | US federal | HTML / PDF | Semi-auto | P2 | High | Track federal management rules | [Open](https://www.whitehouse.gov/omb/information-for-agencies/circulars/) |

## Marketplace

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0019 | **GSA Advantage**<br>GSA | Government products, vendors and pricing | US federal | HTML portal | Semi-auto | P2 | High | Benchmark catalog pricing | [Open](https://www.gsaadvantage.gov/) |

## Medical Devices

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0114 | **FDA Device Databases**<br>FDA | 510(k), PMA, recalls and adverse events | US federal | Downloads / APIs | Auto | P1 | High | Find device opportunities | [Open](https://www.fda.gov/medical-devices/device-advice-comprehensive-regulatory-assistance/medical-device-databases) |

## Minerals

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0138 | **USGS Mineral Resources**<br>USGS | Mines and mineral deposits | US federal | GIS / downloads | Auto | P2 | High | Find resource opportunities | [Open](https://mrdata.usgs.gov/) |

## Oversight

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0054 | **GAO Reports**<br>GAO | Audits, recommendations and testimonies | US federal | HTML / RSS | Auto | P2 | High | Find failed programs and reform demand | [Open](https://www.gao.gov/reports-testimonies) |

## Per Diem

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0039 | **GSA Per Diem API**<br>GSA | Federal travel lodging and meal rates | US federal | REST API | Auto | P1 | High | Price travel-heavy contracts | [Open](https://open.gsa.gov/api/perdiem/) |

## Pharmaceuticals

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0112 | **FDA Orange Book**<br>FDA | Approved drugs, patents and exclusivity | US federal | Bulk downloads | Auto | P1 | High | Find generic-entry opportunities | [Open](https://www.fda.gov/drugs/drug-approvals-and-databases/orange-book-data-files) |

## Political Finance

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0060 | **FEC API**<br>FEC | Candidates, committees and campaign finance | US federal | REST API | Auto | P1 | High | Map political money | [Open](https://api.open.fec.gov/developers/) |

## Pricing

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0021 | **GSA CALC+**<br>GSA | Professional-services labor rates | US federal | Web app / export | Semi-auto | P2 | High | Price bids | [Open](https://buy.gsa.gov/pricing/qr/mas?page=1&page_size=20) |

## Prize Challenges

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0030 | **Challenge.gov**<br>GSA | Federal prize competitions and deadlines | US federal | Portal / RSS | Auto | P2 | High | Find prize-funded opportunities | [Open](https://www.challenge.gov/) |

## Procurement Law

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0055 | **GAO Bid Protest Decisions**<br>GAO | Bid protest decisions | US federal | Search / PDF | Semi-auto | P2 | High | Assess protest risk | [Open](https://www.gao.gov/legal/bid-protests/search) |

## Product Safety

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0121 | **SaferProducts API**<br>CPSC | Product incidents and recalls | US federal | REST API | Auto | P1 | High | Detect product risk | [Open](https://www.saferproducts.gov/RestWebServices/) |

## Public Lands

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0139 | **BLM GIS Data**<br>BLM | Federal land, leases and rights-of-way | US federal | GIS downloads | Auto | P2 | High | Find land-use opportunities | [Open](https://www.blm.gov/services/geospatial/GISData) |

## R&D Awards

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0027 | **SBIR.gov Awards**<br>SBA | Historical SBIR/STTR awards | US federal | Search / download | Semi-auto | P2 | High | Find funded companies and technologies | [Open](https://www.sbir.gov/awards) |

## Regulatory Burden

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0066 | **Information Collection Review**<br>OIRA / OMB | Information collection requests | US federal | Portal / XML | Auto | P2 | High | Detect reporting burdens | [Open](https://www.reginfo.gov/public/do/PRAMain) |

## Regulatory Planning

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0065 | **Unified Agenda**<br>OIRA / OMB | Planned and pending rulemakings | US federal | Portal / XML | Auto | P2 | High | Anticipate regulation | [Open](https://www.reginfo.gov/public/do/eAgendaMain) |

## Research

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0145 | **OSTI API**<br>DOE | DOE-funded publications and software | US federal | REST API | Auto | P1 | High | Find funded technologies | [Open](https://www.osti.gov/api) |

## Road Infrastructure

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0149 | **FHWA HPMS**<br>FHWA | Road condition and performance | US federal | GIS / bulk | Auto | P2 | High | Find corridor investment | [Open](https://www.fhwa.dot.gov/policyinformation/hpms/shapefiles.cfm) |

## Rulemaking

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0043 | **Regulations.gov API**<br>GSA | Dockets, documents and comments | US federal | REST API | Auto | P1 | High | Track active rulemakings | [Open](https://open.gsa.gov/api/regulationsgov/) |

## Sanctions

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0154 | **OFAC Sanctions Lists**<br>U.S. Treasury | Sanctioned entities and programs | US federal | Downloads / service | Semi-auto | P2 | High | Screen counterparties | [Open](https://ofac.treasury.gov/sanctions-list-service) |

## Securities

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0072 | **Treasury Auctions Data**<br>U.S. Treasury | Treasury auction schedules and results | US federal | API / CSV | Auto | P1 | High | Monitor government financing | [Open](https://fiscaldata.treasury.gov/datasets/treasury-securities-auctions-data/) |

## Set-Asides

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0017 | **SBA HUBZone Map**<br>SBA | HUBZone eligibility geography | US federal | GIS portal | Semi-auto | P2 | High | Identify HUBZone advantages | [Open](https://maps.certify.sba.gov/hubzone/map) |

## Software

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0167 | **NASA Software Catalog**<br>NASA | Government-developed software | US federal | Portal | Semi-auto | P2 | High | Find reusable software | [Open](https://software.nasa.gov/) |

## Soils

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0142 | **USDA Soil Data Access**<br>USDA NRCS | Soil attributes and spatial data | US federal | SOAP / query | Semi-auto | P2 | High | Evaluate land suitability | [Open](https://sdmdataaccess.sc.egov.usda.gov/) |

## Space

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0165 | **NASA Open APIs**<br>NASA | Earth, imagery, astronomy and missions | US federal | REST APIs | Auto | P1 | High | Find space and geospatial signals | [Open](https://api.nasa.gov/) |

## Subawards

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0013 | **FSRS**<br>GSA | Prime contractor and grantee subawards | US federal | Portal / export | Semi-auto | P2 | High | Map subcontracting chains | [Open](https://www.fsrs.gov/) |

## Subcontracting

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0014 | **SBA SUBNet**<br>SBA | Prime contractor subcontracting opportunities | US federal | HTML portal | Semi-auto | P2 | High | Find subcontracting openings | [Open](https://subnet.sba.gov/client/dsp_Landing.cfm) |

## Supplier Discovery

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0015 | **SBA Dynamic Small Business Search**<br>SBA | Small-business capabilities and certifications | US federal | HTML portal | Semi-auto | P2 | High | Find partners and competitors | [Open](https://dsbs.sba.gov/search/dsp_dsbs.cfm) |

## Tax Statistics

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0098 | **IRS Statistics**<br>IRS | Individual, business and nonprofit tax statistics | US federal | CSV / XLSX | Auto | P2 | High | Find tax-base trends | [Open](https://www.irs.gov/statistics) |

## Technology

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0166 | **NASA TechPort API**<br>NASA | NASA technology investments | US federal | REST API | Auto | P1 | High | Find funded technologies | [Open](https://techport.nasa.gov/help/api) |

## Toxic Releases

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0125 | **EPA TRI**<br>EPA | Facility toxic releases | US federal | Downloads / API | Auto | P1 | High | Find emission reduction targets | [Open](https://www.epa.gov/toxics-release-inventory-tri-program/tri-data-and-tools) |

## Transit

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0148 | **National Transit Database**<br>FTA | Transit agencies, assets and ridership | US federal | Bulk downloads | Auto | P1 | High | Find capital needs | [Open](https://www.transit.dot.gov/ntd/ntd-data) |

## Transportation

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0147 | **BTS APIs**<br>DOT | Freight, aviation and transport indicators | US federal | REST APIs | Auto | P1 | High | Find logistics trends | [Open](https://www.bts.gov/browse-statistical-products-and-data/apis) |

## Vehicle Safety

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0122 | **NHTSA Vehicle API**<br>NHTSA | VIN, recalls and vehicle data | US federal | REST API | Auto | P1 | High | Track automotive risk | [Open](https://vpic.nhtsa.dot.gov/api/) |

## Water

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0135 | **USGS Water Services**<br>USGS | Streamflow, groundwater and water quality | US federal | REST API | Auto | P1 | High | Monitor water conditions | [Open](https://waterservices.usgs.gov/) |

## Water Quality

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0127 | **Water Quality Portal**<br>EPA / USGS / NOAA | Water samples and monitoring sites | US federal | REST API | Auto | P1 | High | Find water problems | [Open](https://www.waterqualitydata.us/) |

## Weather

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0133 | **National Weather Service API**<br>NOAA | Forecasts, alerts and observations | US federal | REST API | Auto | P1 | High | Trigger hazard scouts | [Open](https://www.weather.gov/documentation/services-web-api) |

## Weather Disasters

**Sources:** 1

| ID | Source / Owner | Data available | Coverage | Access | Auto | Priority | Value | Example opportunity | Access link |
|---|---|---|---|---|---|---|---|---|---|
| GOV-0134 | **NOAA Storm Events**<br>NOAA | Severe weather events and damage | US federal | Bulk CSV | Auto | P1 | High | Quantify exposure | [Open](https://www.ncdc.noaa.gov/stormevents/) |

---

# 7. Opportunity-to-Source Matrix

| Opportunity | Minimum source combination |
|---|---|
| New federal contract matching a company | SAM.gov Opportunities + SAM Entities + company capability profile |
| Likely contract recompete | USAspending + SAM Contract Data + incumbent/entity records |
| Federal subcontracting lead | USAspending + FSRS + SBA SUBNet + DSBS |
| Small-business set-aside opening | SAM Opportunities + DSBS + SBA certification data + HUBZone map |
| Agency spending growth | USAspending + Treasury Fiscal Data + CBO + agency budget documents |
| Regulation-created market | Unified Agenda + Federal Register + Regulations.gov + eCFR |
| Legislative market change | Congress.gov + committee hearings + votes + CBO cost estimates |
| Grant matched to nonprofit or company | Grants.gov + Assistance Listings + USAspending recipient history |
| Government-funded technology opportunity | SBIR Awards + NIH RePORTER + NSF Awards + NASA TechPort + DOE OSTI |
| Healthcare market opening | CMS + HRSA + CDC + FDA + Grants.gov |
| Infrastructure opportunity | USAspending + FHWA + FTA + FAA + FCC + state procurement portals |
| Environmental remediation opportunity | EPA ECHO + Envirofacts + Brownfields/Superfund + state procurement |
| Disaster-recovery demand | OpenFEMA + NOAA/NWS + USGS + SAM.gov + state procurement |
| Energy project opportunity | EIA + NREL + FERC + DOE funding + SAM.gov |
| Public asset acquisition | GSA Auctions + federal property data + USA.gov auction directory |
| Contractor risk | SAM Exclusions + FAPIIS + GAO protests + DOJ enforcement + OFAC |

---

# 8. Source Approval Checklist

A source may move from this catalog into technical design only when all items below are confirmed:

- [ ] The official owner and current Access Link are verified.
- [ ] The source still exposes the stated data.
- [ ] Authentication requirements are known.
- [ ] The source supports commercial internal use under its current terms.
- [ ] Automation classification is confirmed by a sample retrieval.
- [ ] Update cadence and historical depth are known.
- [ ] A stable source record identifier exists or can be constructed.
- [ ] The source's opportunity use cases are approved.
- [ ] Duplicate coverage with another source is understood.
- [ ] The source is assigned to an implementation wave.

---

# 9. Government Domain Completion Criteria

The Government domain source-research phase is considered complete for Version 1.0 when:

1. All P1 federal sources have passed sample-access validation.
2. All P2 federal portals have been reviewed for export or automation options.
3. Every state procurement office has been mapped to its actual solicitation and award platform.
4. Contract, grant, award, regulation, legislation, entity and agency-spending opportunity types have complete source coverage.
5. Gaps are explicitly documented rather than silently omitted.
6. The approved implementation queue is frozen for the first coding cycle.

---

# 10. Maintenance

This is a living reference manual. Government systems migrate, APIs are replaced, procurement platforms change and access policies evolve. Permanent source IDs must remain stable even when names or links change.

Recommended releases:

- **v1.0:** Federal core plus all state procurement entry points.
- **v1.1:** Validated state bid platforms and award repositories.
- **v1.2:** Top 100 county and municipal procurement systems.
- **v2.0:** Full state/local public-spending, grants, licensing and public-record expansion.
