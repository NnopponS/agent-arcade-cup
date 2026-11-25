"""Check English defaults, all local resource references and the deployed logo."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import json
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]).resolve()

class Page(HTMLParser):
    locale = ''
    logo_count = 0
    favicon = False

    def __init__(self):
        super().__init__()
        self.references = set()

    def handle_starttag(self, tag, values):
        v = dict(values)
        if tag == 'html':
            self.locale = v.get('lang')
        if tag == 'img' and urlsplit(v.get('src', '')).path.endswith('arcade-mark.svg'):
            self.logo_count += 1
        if tag == 'link' and v.get('rel') == 'icon':
            self.favicon = urlsplit(v.get('href', '')).path.endswith('arcade-mark.svg')
        if tag == 'link' and v.get('rel') in ('icon', 'stylesheet'):
            self.references.add(v['href'])
        if tag in ('img', 'script') and v.get('src'):
            self.references.add(v['src'])

def existing_url(parent, url):
    u = urlsplit(url)
    assert not (u.netloc or u.scheme), url
    p = (parent / u.path).resolve()
    assert p.is_relative_to(root) and p.is_file() and p.stat().st_size, (url, p)
    return p

page = Page()
page.feed((root/'index.html').read_text())
assert page.locale == 'en', 'English must be the default page language'
assert page.logo_count == 2 and page.favicon, 'Both brands and favicon must reference the Cup mark'
assert len(page.references) > 3
for url in page.references:
    existing_url(root, url)
for file in root.glob('*.css'):
    for quote, ref in re.findall(r'''url\(\s*(["']?)([^\s)("']+)\1\s*\)''', file.read_text()):
        existing_url(file.parent, ref)

assert b'<svg' in (root/'assets/arcade-mark.svg').read_bytes(), 'Expected a bundled SVG logo'
for name in ('index.html', 'app.js', 'replay.js', 'report.json', 'report.md'):
    assert not re.search('[\u0e00-\u0e7f]|th-TH', (root/name).read_text()), ('Non-English default copy', name)
for entry in json.loads((root/'report.json').read_text())['links']:
    existing_url(root, entry['href'])
print('English default, English download, logo/favicon, CSS fonts, and local page resources validated.')
