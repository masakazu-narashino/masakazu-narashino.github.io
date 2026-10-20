import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

RSS_URL = 'https://note.com/masakazu_tanaka/rss'
OUT = Path(__file__).with_name('note_articles.json')
req = urllib.request.Request(RSS_URL, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=30) as response:
    root = ET.fromstring(response.read())

MEDIA = '{http://search.yahoo.com/mrss/}'
CONTENT = '{http://purl.org/rss/1.0/modules/content/}'

def get_image(item):
    # RSS may provide the article cover through Media RSS.
    for tag in (MEDIA + 'thumbnail', MEDIA + 'content'):
        node = item.find(tag)
        if node is not None:
            url = node.get('url', '')
            if url.startswith('https://') and (tag.endswith('thumbnail') or node.get('medium') == 'image' or node.get('type', '').startswith('image/')):
                return url
    enclosure = item.find('enclosure')
    if enclosure is not None and enclosure.get('type', '').startswith('image/'):
        url = enclosure.get('url', '')
        if url.startswith('https://'):
            return url
    # Some feeds include the cover as an img element inside HTML content.
    for tag in ('description', CONTENT + 'encoded'):
        node = item.find(tag)
        html = unescape(node.text or '') if node is not None else ''
        match = re.search(r'<img\b[^>]*\bsrc=[\"\'](https://[^\"\']+)', html, re.I)
        if match:
            return match.group(1)
    return ''

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
    items.append({'title': title, 'url': link, 'date': date, 'image': get_image(item)})
if not items:
    raise RuntimeError('RSSに記事が見つかりません。既存のデータを維持します。')
OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'{len(items)} articles updated; {sum(bool(x["image"]) for x in items)} images found')
