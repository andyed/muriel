"""Evidence preservation and failure boundaries for portable redline reviews."""
import base64
import copy
import hashlib
import json
import re
import struct
import zlib

import pytest

from muriel.redline import ReviewError, build, load_review, _main
from muriel.__main__ import main


def png(width=100, height=80):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress((b'\0' + b'\xff\xff\xff' * width) * height)) + chunk(b'IEND', b''))


@pytest.fixture
def case(tmp_path):
    (tmp_path / 'capture.png').write_bytes(png())
    data = {'version': 1, 'title': 'Review', 'summary': 'Captured, not accepted.', 'frames': [
        {'id': 'before', 'label': 'Before', 'note': 'One capture.', 'source': 'Fixture; DPR 1',
         'image': 'capture.png', 'findings': [
            {'id': 'gap', 'title': 'Gap', 'severity': 'HIGH', 'status': 'open',
             'rule': 'Grouping', 'evidence': 'Two edges.', 'fix': 'Separate groups.',
             'rect': [10, 20, 50, 40], 'measure': {'axis': 'x', 'from': [10, 20], 'to': [26, 20], 'label': 'Gap'}}]}]}
    path = tmp_path / 'review.json'
    path.write_text(json.dumps(data))
    return path, data


def save(case, mutate):
    path, data = case
    mutate(data)
    path.write_text(json.dumps(data))
    return path


def test_preserves_capture_bytes_hash_and_computes_distance(case, tmp_path):
    review, _ = load_review(case[0])
    f = review['frames'][0]
    original = (tmp_path / 'capture.png').read_bytes()
    assert base64.b64decode(f['image'].split(',')[1]) == original
    assert (f['width'], f['height']) == (100, 80)
    assert f['sha256'] == hashlib.sha256(original).hexdigest()
    assert f['findings'][0]['measure']['pixels'] == 16


@pytest.mark.parametrize('rect', [[90, 0, 20, 10], [-1, 0, 10, 10], [0, 0, 0, 10],
                                  [0, 0, float('nan'), 10], [True, 0, 10, 10]])
def test_rejects_misregistered_or_nonfinite_regions(case, rect):
    path = save(case, lambda d: d['frames'][0]['findings'][0].update(rect=rect))
    with pytest.raises(ReviewError, match='rect'):
        load_review(path)


@pytest.mark.parametrize('measure', [
    {'axis': 'x', 'from': [10, 20], 'to': [30, 25], 'label': 'Diagonal'},
    {'axis': 'x', 'from': [10, 20], 'to': [10, 20], 'label': 'Zero'},
    {'axis': 'y', 'from': [10, 20], 'to': [10, 90], 'label': 'Outside'},
])
def test_rejects_unmeasurable_distances(case, measure):
    path = save(case, lambda d: d['frames'][0]['findings'][0].update(measure=measure))
    with pytest.raises(ReviewError, match='measure'):
        load_review(path)


def test_same_finding_can_persist_but_not_duplicate_within_frame(case):
    path, data = case
    second = copy.deepcopy(data['frames'][0]); second['id'] = 'after'
    second['findings'][0]['status'] = 'unverified'
    data['frames'].append(second); path.write_text(json.dumps(data))
    assert load_review(path)[0]['frames'][1]['findings'][0]['status'] == 'unverified'
    data['frames'][0]['findings'] *= 2; path.write_text(json.dumps(data))
    with pytest.raises(ReviewError, match='duplicate finding'):
        load_review(path)


def test_empty_findings_do_not_imply_pass(case, tmp_path):
    path = save(case, lambda d: d['frames'][0].update(findings=[]))
    output = build(path, tmp_path / 'result.html').read_text()
    assert 'No findings supplied' in output
    assert 'PASS' not in output


def test_payload_and_static_fallback_escape_untrusted_text(case, tmp_path):
    hostile = '</script><script>window.PWNED=1</script>@@FALLBACK@@'
    path = save(case, lambda d: d.update(title=hostile, summary=hostile))
    result = build(path, tmp_path / 'result.html').read_text()
    assert hostile not in result
    payload = re.search(r'<script type="application/json" id="review-data">(.*?)</script>', result, re.S)[1]
    assert json.loads(payload)['title'] == hostile
    assert '&lt;script&gt;window.PWNED=1&lt;/script&gt;' in result


def test_refuses_to_destroy_inputs(case, tmp_path):
    for output in [case[0], tmp_path / 'capture.png']:
        before = output.read_bytes()
        with pytest.raises(ReviewError, match='overwrite'):
            build(case[0], output)
        assert output.read_bytes() == before


def test_missing_and_corrupt_capture_fail_without_output(case, tmp_path):
    capture = tmp_path / 'capture.png'
    capture.write_bytes(png()[:-2])
    output = tmp_path / 'out.html'
    assert _main([str(case[0]), '--output', str(output)]) == 2
    assert not output.exists()
    capture.unlink()
    assert _main([str(case[0]), '--output', str(output)]) == 2
    assert not output.exists()


def test_network_capture_and_invented_status_rejected(case):
    path = save(case, lambda d: d['frames'][0].update(image='https://example.com/image.png'))
    with pytest.raises(ReviewError, match='local PNG'):
        load_review(path)
    path = save(case, lambda d: (d['frames'][0].update(image='capture.png'),
                                d['frames'][0]['findings'][0].update(status='accepted')))
    with pytest.raises(ReviewError, match='status'):
        load_review(path)


def test_public_dispatcher_and_single_file_offline_report(case, tmp_path):
    output = tmp_path / 'nested' / 'result.html'
    assert main(['redline', str(case[0]), '--output', str(output)]) == 0
    text = output.read_text()
    assert 'class="static"' in text
    assert 'data:image/png;base64,' in text
    assert not re.search(r'<(?:script|link)[^>]+(?:src|href)=', text)
    assert 'Separate groups.' in text
