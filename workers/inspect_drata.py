import re
from playwright.sync_api import sync_playwright
import os

def get_exe():
    paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    raise RuntimeError("No browser")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path=get_exe())
    page = browser.new_page()
    page.goto("https://drata.com/learn/soc-2", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector("body", timeout=5000)
    html = page.content()
    browser.close()

# Save for inspection
with open("drata_page.html", "w", encoding="utf-8") as f:
    f.write(html)

# Look for links
links = re.findall(r'href="(/learn/[^"]+)"[^>]*>([^<]+)<', html)
print(f"Found {len(links)} /learn/ links")
for i, (url, title) in enumerate(links[:20]):
    print(f"{i+1}. {title.strip()[:60]} -> {url}")
