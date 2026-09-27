#!/usr/bin/env python3
"""Build wordpress.html: same page as index.html, but the data fetches from
jsDelivr CDN instead of relative paths, so it works from any WordPress
Elementor HTML widget with no folder upload.

Output is written to the PRIVATE strategy repo (../places-breakfast/wordpress.html)
to keep the paste-ready file out of the public dev2.090 repo. Falls back to
writing next to index.html if the private repo checkout is not present.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
src = (ROOT / 'index.html').read_text()

# Prefer writing to the private strategy repo if it's checked out as a sibling
PRIVATE_REPO = ROOT.parent / 'places-breakfast'
OUT = (PRIVATE_REPO / 'wordpress.html') if PRIVATE_REPO.exists() else (ROOT / 'wordpress.html')

# Strip doctype/html/head/body wrappers
head_start = src.find('<head>')
head_end = src.find('</head>')
head_content = src[head_start+6:head_end]
body_start = src.find('<body>')
body_end = src.find('</body>')
body_content = src[body_start+6:body_end]

BRANCH = 'claude/confident-carson-feo8dx'
REPO = 'Azeem-tech314/dev2.090'
CDN = f'https://cdn.jsdelivr.net/gh/{REPO}@{BRANCH}/data/compact/'

body_content = body_content.replace(
    "var DATA_BASE='data/compact/';",
    f"var DATA_BASE='{CDN}';"
)

# Keep the leaflet CSS/JS <link> and <script> tags (browsers handle these fine
# inside body). Skip Elementor-conflicting head-only tags.
extras = []
for line in head_content.split('\n'):
    stripped = line.strip()
    if not stripped: continue
    if stripped.startswith('<title>'): continue
    if 'viewport' in stripped: continue
    if 'charset' in stripped: continue
    if stripped.startswith('<meta name="description"'): continue
    if 'apple-mobile-web-app' in stripped or 'mobile-web-app' in stripped: continue
    if stripped.startswith('<meta name="robots"') or 'googlebot' in stripped or 'bingbot' in stripped: continue
    extras.append(stripped)

header_comment = (
    '<!-- ============================================================ \n'
    '     BREAKFAST PLACES v3.2 - WordPress / Elementor single-file version \n'
    '     Paste this entire block into an Elementor HTML widget, a Gutenberg \n'
    '     "Custom HTML" block, or a "Text" widget with HTML enabled. \n'
    '     Data loads live from a public CDN - no FTP, no folder upload. \n'
    '     ============================================================ -->\n\n'
)

out = header_comment + '\n'.join(extras) + '\n\n' + body_content
OUT.write_text(out)
print(f'wordpress.html written: {OUT.stat().st_size // 1024} KB → {OUT}')
print(f'Data URL: {CDN}')
