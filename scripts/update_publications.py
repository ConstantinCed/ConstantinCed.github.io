#!/usr/bin/env python3
"""Add new arXiv papers; preserve existing entries and manual annotations."""
import argparse
from datetime import datetime
from html import escape
from pathlib import Path
import re
import time
import unicodedata
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
AUTHOR = 'Constantin Cedillo Vayson de Pradenne'
NS = {'a': 'http://www.w3.org/2005/Atom', 'o': 'http://a9.com/-/spec/opensearch/1.1/'}
START = '      <!-- publications:start -->\n'
END = '      <!-- publications:end -->'
ID = r'\d{4}\.\d{4,5}'


def normalize(name):
    return ' '.join(unicodedata.normalize('NFKC', name).casefold().split())


def parse_feed(data):
    root = ET.fromstring(data)
    if root.tag != '{http://www.w3.org/2005/Atom}feed':
        raise ValueError('Expected an arXiv Atom feed')
    entries = root.findall('a:entry', NS)
    total = int(root.findtext('o:totalResults', default=str(len(entries)), namespaces=NS))
    if total > len(entries):
        raise ValueError('arXiv results are truncated; increase max_results or narrow the query')
    papers = {}
    for entry in entries:
        url = entry.findtext('a:id', default='', namespaces=NS)
        match = re.fullmatch(r'https?://arxiv.org/abs/(' + ID + r')(?:v\d+)?', url)
        if '/api/errors' in url:
            raise ValueError('arXiv API error: ' + url)
        authors = [' '.join(x.text.split()) for x in entry.findall('a:author/a:name', NS) if x.text]
        if not any(normalize(a) == normalize(AUTHOR) for a in authors):
            continue
        if not match:
            raise ValueError('Unsupported arXiv ID for matching author: ' + url)
        title = ' '.join(entry.findtext('a:title', default='', namespaces=NS).split())
        published = entry.findtext('a:published', default='', namespaces=NS)
        if not title:
            raise ValueError('Missing title for ' + url)
        date = datetime.fromisoformat(published.replace('Z', '+00:00')).strftime('%B %Y')
        papers[match[1]] = {'title': title, 'authors': authors, 'date': date}
    if not papers:
        raise ValueError('No matching author found; leaving the website unchanged')
    return papers


def render(arxiv_id, paper):
    authors = ', '.join('<strong>' + escape(a) + '</strong>' if normalize(a) == normalize(AUTHOR) else escape(a) for a in paper['authors'])
    return (f'      <article class="paper">\n'
            f'        <a href="https://arxiv.org/abs/{arxiv_id}" target="_blank" rel="noopener noreferrer">{escape(paper["title"])}</a>\n'
            f'        <p class="authors">{authors}</p>\n'
            f'        <p class="date">{escape(paper["date"])} · arXiv:{arxiv_id}</p>\n'
            f'      </article>\n')


def update_html(html, papers):
    if html.count(START) != 1 or html.count(END) != 1:
        raise ValueError('Expected exactly one publications marker pair')
    before, rest = html.split(START)
    section, after = rest.split(END)
    blocks = re.findall(r'      <article class="paper">.*?</article>\n', section, re.S)
    if ''.join(blocks) != section:
        raise ValueError('Unexpected publication markup; leaving it unchanged')
    existing = {}
    for block in blocks:
        match = re.search(r'https://arxiv.org/abs/(' + ID + r')(?:v\d+)?"', block)
        if not match or match[1] in existing:
            raise ValueError('Missing or duplicate arXiv ID in existing publications')
        existing[match[1]] = block
    added = sorted(set(papers) - set(existing), reverse=True)
    if not added:
        return html, added
    for arxiv_id in added:
        existing[arxiv_id] = render(arxiv_id, papers[arxiv_id])
    # Modern arXiv IDs encode submission month and sequence, independent of revisions.
    section = ''.join(existing[k] for k in sorted(existing, reverse=True))
    return before + START + section + END + after, added


def fetch_feed():
    query = urlencode({'search_query': 'au:Cedillo', 'start': 0, 'max_results': 1000,
                       'sortBy': 'submittedDate', 'sortOrder': 'descending'})
    request = Request('https://export.arxiv.org/api/query?' + query,
                      headers={'User-Agent': 'ConstantinCed-publications/1.0 (https://constantinced.github.io/)'})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=60) as response:
                return response.read()
        except (OSError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(5 * (attempt + 1))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--feed', type=Path, help='Use a saved Atom response (offline testing)')
    args = parser.parse_args()
    papers = parse_feed(args.feed.read_bytes() if args.feed else fetch_feed())
    path = ROOT / 'index.html'
    html, added = update_html(path.read_text(encoding='utf-8'), papers)
    if added:
        temporary = path.with_suffix('.html.tmp')
        temporary.write_text(html, encoding='utf-8')
        temporary.replace(path)
    print('Added: ' + ', '.join(added) if added else 'No new papers. Existing entries preserved.')


if __name__ == '__main__':
    main()
