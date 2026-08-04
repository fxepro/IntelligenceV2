import re
import json

with open('drata_page_cf.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Look for NextJS data or article references
patterns = [
    r'href="(/learn/[^"]+)"[^>]*>([^<]+)</a>',
    r'"href":"(/learn/[^"]+)".{0,100}?"name":"([^"]+)"',
]

all_links = set()
for pattern in patterns:
    matches = re.findall(pattern, html)
    for url, title in matches:
        if url and title and '/learn/' in url:
            all_links.add((url.strip(), title.strip()))

print(f"Found {len(all_links)} unique articles\n")
for i, (url, title) in enumerate(sorted(all_links)[:50]):
    print(f"{i+1}. {title[:70]}")

# Save list
with open('drata_articles.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join([f"{title} -> {url}" for url, title in sorted(all_links)]))
print(f"\nSaved {len(all_links)} articles to drata_articles.txt")
