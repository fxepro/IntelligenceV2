import re

with open('drata_page_cf.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Search for the known article titles
titles = [
    "What is SOC 2 Compliance?",
    "SOC 2 Compliance Checklist",
    "Getting Started",
    "Best Practices",
    "SOC 2 Type",
    "Automation",
]

for title in titles:
    if title in html:
        print(f"Found: {title}")
        # Get context
        idx = html.find(title)
        print(f"  Context: {html[max(0, idx-100):idx+150]}\n")

# Try to find all /learn/ URLs
matches = re.findall(r'["\']([^"\']*?/learn/[^"\']*?)["\']', html)
print(f"\nFound {len(set(matches))} /learn/ URLs:")
for url in sorted(set(matches))[:20]:
    print(f"  - {url}")
