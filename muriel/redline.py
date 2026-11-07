"""Build a portable critique presentation from captured PNGs and authored findings.

``muriel redline review.json --output review.html`` embeds the captures without
resampling them. This is a presentation of supplied evidence, not a critic or
an acceptance gate. Coordinates are in capture pixels; no DOM is reconstructed.
Core uses only the standard library. See references/redline-review.md for the
manifest contract and the distinction between a revision and a verified fix.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import math
from pathlib import Path
import re
import struct
import sys
import zlib


class ReviewError(ValueError):
    """An input cannot be presented faithfully."""


def _text(obj, key, where):
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ReviewError(f"{where}.{key}: expected non-empty text")
    return value


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _png(path):
    data = path.read_bytes()
    if len(data) > 20 * 1024 * 1024:
        raise ReviewError(f"{path.name}: PNG exceeds 20 MiB")
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ReviewError(f"{path.name}: expected a PNG capture")
    pos, size, has_data, ended = 8, None, False, False
    while pos + 12 <= len(data):
        length = struct.unpack('>I', data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        end = pos + 8 + length
        if end + 4 > len(data):
            raise ReviewError(f"{path.name}: truncated PNG")
        chunk = data[pos + 8:end]
        if zlib.crc32(kind + chunk) & 0xffffffff != struct.unpack('>I', data[end:end + 4])[0]:
            raise ReviewError(f"{path.name}: PNG checksum mismatch")
        if size is None:
            if kind != b'IHDR' or length != 13:
                raise ReviewError(f"{path.name}: missing PNG header")
            size = struct.unpack('>II', chunk[:8])
        if kind == b'IDAT':
            has_data = True
        pos = end + 4
        if kind == b'IEND':
            ended = True
            break
    if not ended or not has_data or pos != len(data) or not size or min(size) < 1 or max(size) > 20000:
        raise ReviewError(f"{path.name}: incomplete or oversized PNG capture")
    return data, size


def load_review(path):
    """Validate and resolve captures; return data plus input paths to protect."""
    path = Path(path).resolve()
    try:
        raw = json.loads(path.read_text(encoding='utf-8'))
    except (ValueError, UnicodeError) as exc:
        raise ReviewError(f"Invalid review JSON: {exc}") from exc
    if not isinstance(raw, dict) or type(raw.get('version')) is not int or raw['version'] != 1:
        raise ReviewError('Expected a review object with version: 1')
    review = {key: _text(raw, key, 'review') for key in ('title', 'summary')}
    frames = raw.get('frames')
    if not isinstance(frames, list) or not 1 <= len(frames) <= 30:
        raise ReviewError('frames: expected 1–30 captured revisions')
    review['frames'] = []
    inputs, ids = {path}, set()
    for i, frame in enumerate(frames):
        where = f'frames[{i}]'
        if not isinstance(frame, dict):
            raise ReviewError(f'{where}: expected an object')
        item = {key: _text(frame, key, where) for key in ('id', 'label', 'note', 'source')}
        if item['id'] in ids:
            raise ReviewError(f'{where}: duplicate frame id')
        ids.add(item['id'])
        image = _text(frame, 'image', where)
        if '://' in image or image.startswith('data:'):
            raise ReviewError(f'{where}.image: use a local PNG path')
        image_path = (path.parent / image).resolve()
        inputs.add(image_path)
        data, (width, height) = _png(image_path)
        item.update(width=width, height=height, sha256=hashlib.sha256(data).hexdigest(),
                    image='data:image/png;base64,' + base64.b64encode(data).decode('ascii'))
        findings = frame.get('findings')
        if not isinstance(findings, list):
            raise ReviewError(f'{where}.findings: expected a list (empty is allowed)')
        item['findings'], finding_ids = [], set()
        for j, finding in enumerate(findings):
            at = f'{where}.findings[{j}]'
            if not isinstance(finding, dict):
                raise ReviewError(f'{at}: expected an object')
            f = {key: _text(finding, key, at) for key in ('id', 'title', 'severity', 'status', 'rule', 'evidence', 'fix')}
            if f['id'] in finding_ids:
                raise ReviewError(f'{at}: duplicate finding id in this frame')
            finding_ids.add(f['id'])
            if f['severity'] not in ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW'):
                raise ReviewError(f'{at}.severity: use CRITICAL, HIGH, MEDIUM, or LOW')
            if f['status'] not in ('open', 'addressed', 'unverified'):
                raise ReviewError(f'{at}.status: use open, addressed, or unverified')
            rect = finding.get('rect')
            if rect is not None:
                if (not isinstance(rect, list) or len(rect) != 4 or not all(_number(v) for v in rect)
                        or min(rect[:2]) < 0 or min(rect[2:]) <= 0
                        or rect[0] + rect[2] > width or rect[1] + rect[3] > height):
                    raise ReviewError(f'{at}.rect: [x, y, width, height] must fit the capture')
                f['rect'] = rect
            measure = finding.get('measure')
            if measure is not None:
                if not isinstance(measure, dict):
                    raise ReviewError(f'{at}.measure: expected an object')
                axis, start, end = measure.get('axis'), measure.get('from'), measure.get('to')
                points = [start, end]
                if axis not in ('x', 'y') or any(not isinstance(p, list) or len(p) != 2 or
                        not all(_number(v) for v in p) or not (0 <= p[0] <= width and 0 <= p[1] <= height) for p in points):
                    raise ReviewError(f'{at}.measure: axis x/y and two points within the capture are required')
                a = 0 if axis == 'x' else 1
                if start[1-a] != end[1-a] or start[a] == end[a]:
                    raise ReviewError(f'{at}.measure: endpoints must form a nonzero axis-aligned distance')
                f['measure'] = {'axis': axis, 'from': start, 'to': end,
                                'label': _text(measure, 'label', at + '.measure'),
                                'pixels': abs(end[a] - start[a])}
            item['findings'].append(f)
        review['frames'].append(item)
    return review, inputs


def build(manifest, output):
    """Write one offline HTML artifact, with exact captures and a no-JS report."""
    review, inputs = load_review(manifest)
    output = Path(output).resolve()
    template_path = Path(__file__).with_name('redline.html')
    if output in inputs or output == template_path.resolve():
        raise ReviewError('Output must not overwrite a manifest, capture, or template')
    esc = html.escape
    fallback = []
    for frame in review['frames']:
        fallback.append(f'<section><h2>{esc(frame["label"])}</h2><p>{esc(frame["note"])}</p>'
                        f'<img src="{frame["image"]}" alt="{esc(frame["label"], quote=True)}">'
                        f'<p>{esc(frame["source"])}</p><ol>')
        for f in frame['findings']:
            measurement = f.get('measure')
            distance = f' · {measurement["label"]}: {measurement["pixels"]:g} capture px' if measurement else ''
            fallback.append(f'<li><h3>{esc(f["title"])}</h3><p>{esc(f["severity"] + " · " + f["status"] + distance)}</p>'
                            f'<p>{esc(f["rule"])}</p><p>{esc(f["evidence"])}</p><p>{esc(f["fix"])}</p></li>')
        fallback.append('</ol></section>')
    payload = json.dumps(review, ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    substitutions = {'TITLE': esc(review['title']), 'SUMMARY': esc(review['summary']),
                     'DATA': payload, 'FALLBACK': '\n'.join(fallback)}
    result = re.sub(r'@@(TITLE|SUMMARY|DATA|FALLBACK)@@', lambda m: substitutions[m[1]],
                    template_path.read_text(encoding='utf-8'))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result, encoding='utf-8')
    return output


def _main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('manifest', type=Path, help='Review JSON; capture paths are relative to it')
    parser.add_argument('--output', required=True, type=Path, help='Portable HTML output')
    args = parser.parse_args(argv)
    try:
        print(build(args.manifest, args.output))
    except (OSError, ReviewError) as exc:
        print(f'muriel redline: {exc}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(_main())
