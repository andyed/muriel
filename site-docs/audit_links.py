"""Audit links in built docs articles and standalone demo pages; distinguish HTTP failures from blocked checks.

Run after mkdocs build: python site-docs/audit_links.py --site site-build --out /tmp/muriel-links.json
External requests are bounded and deduplicated. Fragments on remote pages and
JavaScript-rendered/soft error pages still need browser review. Never executes JS.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen


class Page(HTMLParser):
    def __init__(self, whole_page=False):
        super().__init__()
        self.article = False
        self.whole_page = whole_page
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        if tag == 'article' and 'md-content__inner' in attrs.get('class', ''):
            self.article = True
        if self.article or self.whole_page:
            key = 'href' if tag == 'a' else 'src' if tag in ('img', 'video', 'audio', 'source', 'track') else None
            if key and attrs.get(key):
                self.links.append(attrs[key])
            if tag == 'video' and attrs.get('poster'):
                self.links.append(attrs['poster'])
            if tag in ('img', 'source') and attrs.get('srcset'):
                self.links.extend(item.strip().split()[0] for item in attrs['srcset'].split(',') if item.strip())

    def handle_endtag(self, tag):
        if tag == 'article':
            self.article = False


def check_remote(url):
    result = {'url': url}
    try:
        request = Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; MurielDocsLinkAudit/1.0)'})
        with urlopen(request, timeout=12) as response:
            result.update(status=response.status, final_url=response.url)
            body = response.read(131072).decode('utf-8', errors='replace') if 'html' in response.headers.get('Content-Type', '') else ''
            title = re.search(r'<title[^>]*>(.*?)</title>', body, re.I | re.S)
            result['title'] = re.sub(r'\s+', ' ', title.group(1)).strip() if title else ''
            result['category'] = 'review' if re.search(r'\b404\b|page not found|access denied|just a moment', result['title'], re.I) else 'ok'
            if response.status != 200:
                result['category'] = 'review'
    except HTTPError as error:
        result.update(status=error.code, category='broken' if error.code in (404, 410) else 'blocked' if error.code in (401, 403, 429) else 'review')
    except (URLError, TimeoutError, OSError) as error:
        result.update(category='unverified', error=str(error))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', type=Path, default=Path('site-build'))
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--external', action='store_true', help='Also check public HTTP(S) URLs')
    args = parser.parse_args()
    root = args.site.resolve()
    if not (root / 'index.html').is_file():
        parser.error(f'No built site at {root}; run mkdocs build first')
    pages = {}
    for path in sorted(root.rglob('*.html')):
        html = path.read_text(errors='replace')
        page = Page(whole_page='md-content__inner' not in html)
        page.feed(html); pages[path] = page
    external = {}; internal = []; checked = 0; skipped = []
    for path, page in pages.items():
        route = '/' + path.relative_to(root).as_posix()
        for href in page.links:
            url = urlsplit(urljoin('https://local.invalid' + route, href))
            if url.scheme not in ('http', 'https'):
                continue
            if url.netloc not in ('local.invalid', 'muriel.mindbendingpixels.com'):
                if url.hostname in ('localhost', '127.0.0.1', 'example.com', 'example.org'):
                    skipped.append(href); continue
                key = urlunsplit((url.scheme, url.netloc, url.path, url.query, ''))
                external.setdefault(key, []).append(route)
                continue
            target = root / unquote(url.path).lstrip('/')
            if target.is_dir(): target /= 'index.html'
            checked += 1
            issue = None
            if not target.is_file(): issue = 'missing file'
            elif url.fragment and target.suffix == '.html':
                dest = pages.get(target)
                if dest and unquote(url.fragment) not in dest.ids: issue = 'missing anchor'
            if issue: internal.append({'page': route, 'href': href, 'issue': issue})
    print(f'{len(pages)} HTML files; {checked} internal links; {len(external)} unique external URLs', flush=True)
    results = []
    if args.external:
        with ThreadPoolExecutor(max_workers=6) as pool:
            for i, result in enumerate(pool.map(check_remote, sorted(external)), 1):
                result['pages'] = sorted(set(external[result['url']]))
                results.append(result)
                if i % 50 == 0: print(f'Checked {i}/{len(external)} external URLs', flush=True)
    report = {'internal_checked': checked, 'internal_issues': internal,
              'external_unique': len(external), 'external_results': results,
              'external_counts': dict(Counter(r['category'] for r in results)),
              'skipped_examples': sorted(set(skipped)),
              'limits': 'HTTP checks do not verify remote fragments, JavaScript routes, source claims, or link relevance. Blocked and unverified URLs are not confirmed dead.'}
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'internal_issues':len(internal),'external_counts':report['external_counts'],'report':str(args.out)},indent=2))

    return 1 if internal or any(r['category'] == 'broken' for r in results) else 0


if __name__ == '__main__':
    raise SystemExit(main())
