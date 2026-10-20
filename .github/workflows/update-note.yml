import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

RSS_URL = 'https://note.com/masakazu_tanaka/rss'
OUT = Path(__file__).with_name('note_articles.json')
req = urllib.request.Request(RSS_URL, headers={'User-Agent': 'Mozilla/5.0 (compatible; PersonalSiteFeedUpdater/1.0)'})
with urllib.request.urlopen(req, timeout=30) as response:
    xml = response.read()
root = ET.fromstring(xml)
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
    items.append({'title': title, 'url': link, 'date': date})
if not items:
    raise RuntimeError('RSSに記事が見つかりません。既存のデータを維持します。')
OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'{len(items)} articles updated')
