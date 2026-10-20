import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

RSS_URL = 'https://note.com/masakazu_tanaka/rss'
OUT = Path(__file__).with_name('note_articles.json')
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; NoteArticleUpdater/1.0)', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
MEDIA = '{http://search.yahoo.com/mrss/}'
CONTENT = '{http://purl.org/rss/1.0/modules/content/}'

class ImageMetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.image = ''

    def handle_starttag(self, tag, attrs):
        if tag.lower() != 'meta':
            return
        data = dict(attrs)
        key = (data.get('property') or data.get('name') or '').lower()
        if key in ('og:image', 'og:image:url', 'twitter:image'):
            candidate = unescape(data.get('content', '')).strip()
            if candidate.startswith('https://') and (not self.image or key.startswith('og:')):
                self.image = candidate

def fetch(url):
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode('utf-8', errors='replace')

def rss_image(item):
    for tag in (MEDIA + 'thumbnail', MEDIA + 'content'):
        for node in item.findall(tag):
            url = node.get('url', '')
            if url.startswith('https://') and (tag.endswith('thumbnail') or node.get('medium') == 'image' or node.get('type', '').startswith('image/')):
                return url
    enclosure = item.find('enclosure')
    if enclosure is not None and enclosure.get('type', '').startswith('image/'):
        url = enclosure.get('url', '')
        if url.startswith('https://'):
            return url
    for tag in ('description', CONTENT + 'encoded'):
        node = item.find(tag)
        html = unescape(node.text or '') if node is not None else ''
        match = re.search(r'<img\b[^>]*\bsrc=[\"\'](https://[^\"\']+)', html, re.I)
        if match:
            return unescape(match.group(1))
    return ''

def page_image(url):
    try:
        parser = ImageMetaParser()
        parser.feed(fetch(url))
        return parser.image
    except Exception as exc:
        print(f'Could not read article image from {url}: {exc}')
        return ''

root = ET.fromstring(fetch(RSS_URL))
items = []
for item in root.findall('./channel/item')[:3]:
    def val(tag):
        node = item.find(tag)
        return (node.text or '').strip() if node is not None else ''

    title, link, date = val('title'), val('link'), val('pubDate')
    if not title or not link.startswith('https://note.com/'):
        continue
    try:
        date = parsedate_to_datetime(date).date().isoformat()
    except (ValueError, TypeError, IndexError):
        date = ''
    image = rss_image(item) or page_image(link)
    items.append({'title': title, 'url': link, 'date': date, 'image': image})

if not items:
    raise RuntimeError('RSSに記事が見つかりません。既存のデータを維持します。')
OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'{len(items)} articles updated; {sum(bool(x["image"]) for x in items)} images found')
