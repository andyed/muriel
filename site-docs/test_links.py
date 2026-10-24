"""Regression checks for the repository-to-site boundary and link-audit gate."""
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import link_paths


class LinkPathsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.files = []
        self.source = self.file('plugin/channels/web.md', 'channels/web.md', 'channels/web/')
        self.file('plugin/agents/reviewer.md', 'agents/reviewer.md', 'agents/reviewer/')
        self.file('assets/logo.gif', 'brand-assets/logo.gif', 'brand-assets/logo.gif')
        self.file('plugin/demo/index.html', 'examples/demo/index.html', 'examples/demo/index.html')
        (self.root / 'tool.py').write_text('')
        self.native = self.file('site-docs/src/index.md', 'index.md', '')

    def file(self, canonical, src_uri, url):
        path = self.root / canonical
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('')
        file = SimpleNamespace(abs_src_path=str(path), src_uri=src_uri, url=url)
        self.files.append(file)
        return file

    def render(self, text, file=None):
        with patch.object(link_paths, 'REPO', self.root):
            return link_paths.on_page_markdown(text, page=SimpleNamespace(file=file or self.source), config={}, files=self.files)

    def test_site_link_preserves_fragment(self):
        self.assertEqual(self.render('[review](../agents/reviewer.md#checks)'), '[review](../agents/reviewer.md#checks)')

    def test_repository_file_uses_github(self):
        self.assertEqual(self.render('[tool](../../tool.py)'), '[tool](https://github.com/andyed/muriel/blob/main/tool.py)')

    def test_demo_directory_uses_published_index(self):
        self.assertEqual(self.render('[demo](../demo/)'), '[demo](../examples/demo/index.html)')

    def test_html_assets_use_output_layout(self):
        self.assertEqual(self.render('<img src="../../assets/logo.gif"><source srcset="../../assets/logo.gif">'), '<img src="../../brand-assets/logo.gif"><source srcset="../../brand-assets/logo.gif">')

    def test_fenced_examples_and_native_pages_unchanged(self):
        fenced = '```md\n[tool](../../tool.py)\n```\n'
        self.assertEqual(self.render(fenced), fenced)
        self.assertEqual(self.render('[gallery](gallery/)', self.native), '[gallery](gallery/)')

    def test_missing_targets_are_left_for_audit(self):
        text = '[missing](no-such.md) [web](https://example.org/) [section](#section)'
        self.assertEqual(self.render(text), text)

    def test_audit_fails_on_missing_anchor_and_image(self):
        site = self.root / 'built'
        site.mkdir()
        page = site / 'index.html'
        page.write_text('<article class="md-content__inner"><a href="#gone">Bad</a><source srcset="missing.gif"></article>')
        report = self.root / 'audit.json'
        command = [sys.executable, str(Path(__file__).with_name('audit_links.py')), '--site', str(site), '--out', str(report)]
        failed = subprocess.run(command, capture_output=True)
        self.assertEqual(failed.returncode, 1)
        self.assertEqual(len(json.loads(report.read_text())['internal_issues']), 2)
        page.write_text('<article class="md-content__inner"><h1 id="here">Good</h1><a href="#here">OK</a></article>')
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)


if __name__ == '__main__':
    unittest.main()
