$env:PYTHONPATH="C:\AIProjects\intelligence\v2\api"
..\.venv\Scripts\python -c @"
import cloudscraper
scraper = cloudscraper.create_scraper()
response = scraper.get('https://drata.com/learn/soc-2', timeout=30)
html = response.text
print(f'HTML length: {len(html)}')
print('First 2000 chars:')
print(html[:2000])
# Save for inspection
with open('drata_page_cf.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f'\nSaved to drata_page_cf.html')
"@
