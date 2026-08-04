import re
import json

with open('drata_page_cf.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Extract all builder.io article blocks which contain the article structure
# Pattern: builder-block with links and titles
articles = {}

# Find all the article links with their titles
# Looking for pattern: href="/learn/soc-2/..." and nearby titles
article_links = re.findall(r'href="(/learn/soc-2/[^"]*)"[^>]*>([^<]*)</a>', html)

# Also search for Builder.io nested structure with article info
blocks = re.findall(r'builder-block"[^>]*>([^<]*)<', html)
titles = re.findall(r'"builderio-block"[^>]*>([^<]*)</div>', html)
links_direct = re.findall(r'href="(/learn/soc-2/[^"]+)"', html)

print(f"Found {len(article_links)} article link pairs")
print(f"Found {len(set(links_direct))} unique /learn/soc-2/ links\n")

# Clean and deduplicate
clean_links = set()
for link in links_direct:
    clean = link.rstrip('\\').strip()
    if '/learn/soc-2/' in clean:
        clean_links.add(clean)

print(f"Cleaned to {len(clean_links)} unique links:\n")

# Map URL slugs to titles by finding adjacent title elements
for i, link in enumerate(sorted(clean_links)[:30]):
    slug = link.replace('/learn/soc-2/', '').replace('-', ' ').title()
    print(f"{i+1}. {slug}")
    print(f"   URL: https://drata.com{link}")

# Save all links
with open('drata_articles_soc2.txt', 'w', encoding='utf-8') as f:
    for link in sorted(clean_links):
        slug = link.replace('/learn/soc-2/', '').replace('-', ' ').title()
        f.write(f"{slug}\thttps://drata.com{link}\n")

print(f"\nSaved {len(clean_links)} articles to drata_articles_soc2.txt")
