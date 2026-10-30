"""Translate repository-relative Markdown links for the symlinked docs tree.

Keep the skill files usable in a checkout. Published pages link to another site
page when its canonical source is included; repository-only files/directories
link to GitHub. Only existing targets inside this repository are rewritten.
"""
from pathlib import Path
import posixpath
import re
from urllib.parse import quote, unquote, urlsplit, urlunsplit

REPO = Path(__file__).resolve().parent.parent
TARGET = re.compile(r'(?<=\]\()([^\s)]+)(?=\s|\))')
HTML_ASSET = re.compile(r'(?P<prefix>\b(?:src|srcset)=["\'])(?P<url>[^"\'\s]+)(?P<suffix>["\'])')
FENCES = re.compile(r'(^[ \t]*(?:`{3,}|~{3,})[^\n]*\n.*?^[ \t]*(?:`{3,}|~{3,})[ \t]*$)', re.M | re.S)


def on_page_markdown(markdown, *, page, config, files):
    source = Path(page.file.abs_src_path).resolve()
    # Native site pages already use the publication layout.
    if source.is_relative_to(REPO / 'site-docs'):
        return markdown
    published = {Path(f.abs_src_path).resolve(): f for f in files if f.abs_src_path}

    def rewrite_url(original, html=False):
        url = urlsplit(original)
        # Keep links to our standalone demos on the current preview/site host.
        if url.hostname == 'muriel.mindbendingpixels.com':
            return urlunsplit(('', '', url.path, url.query, url.fragment))
        if url.scheme or url.netloc or not url.path or url.path.startswith('/'):
            return original
        target = (source.parent / unquote(url.path)).resolve()
        if not target.exists() or not target.is_relative_to(REPO):
            return original
        if target.is_dir():
            for name in ('index.md', 'index.html', 'README.md'):
                if target / name in published:
                    target /= name
                    break
        if target in published:
            destination = published[target].url if html else published[target].src_uri
            current = page.file.url if html else page.file.src_uri
            path = posixpath.relpath(destination, posixpath.dirname(current) or '.')
            return urlunsplit(('', '', quote(path, safe='/.'), url.query, url.fragment))
        kind = 'tree' if target.is_dir() else 'blob'
        path = quote(target.relative_to(REPO).as_posix(), safe='/')
        return urlunsplit(('https', 'github.com', f'/andyed/muriel/{kind}/main/{path}', url.query, url.fragment))

    # Fenced code examples describe source syntax and must not be rewritten.
    parts = FENCES.split(markdown)
    def rewrite_prose(part):
        part = TARGET.sub(lambda m: rewrite_url(m.group(0)), part)
        return HTML_ASSET.sub(lambda m: m['prefix'] + rewrite_url(m['url'], html=True) + m['suffix'], part)

    return ''.join(part if i % 2 else rewrite_prose(part) for i, part in enumerate(parts))
