"""muriel.tools.impeccable_bridge — wire pbakaus/impeccable into muriel-critique.

Shells out to ``npx impeccable detect <target> --json`` (the
deterministic 27-rule scanner from pbakaus/impeccable, regex + headless
Chrome, no LLM in the loop) and returns the findings in a form the
``muriel-critique`` agent can fold into its report. Runs as a first
pass on web artifacts (HTML, URLs, static dirs); the vision-model
critique layers on top, focusing on what a static analyser cannot see
(hierarchy, composition, brand voice, perceptual issues).

Degrades silently when Node / npx / impeccable / network are missing —
returns ``BridgeResult(available=False, …)`` so callers can fall back
to vision-only without raising.

Attribution: the detector and its rules are pbakaus/impeccable's
(Apache-2.0). This module is a thin Python wrapper for invocation +
JSON parsing + Markdown formatting. Cite the upstream at use-site.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any, Optional, Union

IMPECCABLE_REPO = "https://github.com/pbakaus/impeccable"

__all__ = [
    "BridgeResult",
    "detect",
    "format_markdown",
]


@dataclass
class BridgeResult:
    """Outcome of one ``npx impeccable detect`` invocation."""

    available: bool
    findings: list[dict[str, Any]] = field(default_factory=list)
    error: str = ""
    raw: Union[dict[str, Any], list[Any], str, None] = None
    target: str = ""

    def __bool__(self) -> bool:
        return self.available


def detect(
    target: str,
    *,
    fast: bool = False,
    timeout: float = 120.0,
    npx_path: Optional[str] = None,
) -> BridgeResult:
    """Run ``npx impeccable detect <target> --json`` and parse the output.

    Parameters
    ----------
    target
        URL, HTML file, or directory to scan. Passed verbatim to the
        detector — no path resolution here.
    fast
        If True, add ``--fast`` (regex-only; skips Puppeteer rendering).
        Faster, but loses the rules that require computed styles.
    timeout
        Seconds before the subprocess is killed.
    npx_path
        Override the discovered npx binary. Useful for tests.

    Returns
    -------
    BridgeResult
        ``.available`` is True iff the detector ran and emitted parseable
        JSON. Errors (missing npx, timeout, malformed JSON) yield
        ``available=False`` with a clean ``.error`` message; nothing is
        raised.
    """
    npx = npx_path if npx_path is not None else shutil.which("npx")
    if not npx:
        return BridgeResult(
            available=False,
            error="npx not found on PATH — install Node.js to enable the bridge",
            target=target,
        )

    cmd = [npx, "--yes", "impeccable", "detect", target, "--json"]
    if fast:
        cmd.insert(-1, "--fast")

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired:
        return BridgeResult(
            available=False,
            error=f"impeccable timed out after {timeout:.0f}s on {target!r}",
            target=target,
        )
    except OSError as exc:
        return BridgeResult(
            available=False,
            error=f"impeccable invocation failed: {exc}",
            target=target,
        )

    # impeccable may exit nonzero when findings are present; that's not
    # a failure for us. Only treat empty stdout / unparseable JSON as one.
    stdout = proc.stdout.strip()
    if not stdout:
        stderr = proc.stderr.strip() or "no JSON output"
        return BridgeResult(
            available=False,
            error=f"impeccable produced no JSON: {stderr[:200]}",
            target=target,
        )
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError as exc:
        return BridgeResult(
            available=False,
            error=f"impeccable JSON unparseable: {exc}",
            target=target,
            raw=stdout,
        )

    return BridgeResult(
        available=True,
        findings=_extract_findings(parsed),
        raw=parsed,
        target=target,
    )


def _extract_findings(parsed: Any) -> list[dict[str, Any]]:
    """Flatten impeccable's JSON to a list of finding dicts.

    The CLI's output shape is not formally documented; accept either a
    bare list at the top level, or an object with one of several common
    container keys (``findings``, ``issues``, ``results``, ``violations``,
    ``detections``), or a one-level nested object keyed by target.
    """
    if isinstance(parsed, list):
        return [f for f in parsed if isinstance(f, dict)]
    if isinstance(parsed, dict):
        for key in ("findings", "issues", "results", "violations", "detections"):
            v = parsed.get(key)
            if isinstance(v, list):
                return [f for f in v if isinstance(f, dict)]
        for v in parsed.values():
            if isinstance(v, dict):
                inner = _extract_findings(v)
                if inner:
                    return inner
            elif isinstance(v, list):
                inner = [f for f in v if isinstance(f, dict)]
                if inner:
                    return inner
    return []


def format_markdown(
    result: BridgeResult, *, attribution: bool = True
) -> str:
    """Format a bridge result for inclusion in a critique report.

    Three shapes:

    - **unavailable** — one-line italic note explaining why; the caller
      should proceed with vision-only critique.
    - **available, no findings** — one-line italic "clean" note.
    - **available, findings** — a ``### Deterministic pre-scan`` heading
      and a Markdown table of (rule, severity, where, what).
    """
    if not result.available:
        return (
            f"_impeccable bridge unavailable: {result.error}_  \n"
            f"_(deterministic pre-scan skipped; vision-model rules only)_\n"
        )
    if not result.findings:
        head = (
            f"_impeccable detect on `{result.target}`: no anti-patterns "
            f"flagged (27-rule deterministic pass clean)._"
        )
        if attribution:
            head += (
                f"  \n_Detector: [pbakaus/impeccable]({IMPECCABLE_REPO}) "
                f"(Apache-2.0)._"
            )
        return head + "\n"

    n = len(result.findings)
    out: list[str] = [
        f"### Deterministic pre-scan — impeccable "
        f"({n} finding{'' if n == 1 else 's'})",
        "",
        "| Rule | Severity | Where | What |",
        "|---|---|---|---|",
    ]
    for f in result.findings:
        rule = _first(f, ["rule", "id", "name", "code"]) or "?"
        sev = _first(f, ["severity", "level"]) or "—"
        where = (
            _first(f, ["selector", "location", "element", "where", "path"])
            or _first(f, ["file", "url"])
            or "—"
        )
        msg = _first(f, ["message", "description", "what", "detail"]) or "—"
        out.append(
            f"| `{rule}` | {sev} | {_md_escape(_truncate(str(where), 48))} "
            f"| {_md_escape(_truncate(str(msg), 96))} |"
        )
    if attribution:
        out.append("")
        out.append(
            f"_Source: `npx impeccable detect {result.target} --json` · "
            f"detector by [pbakaus/impeccable]({IMPECCABLE_REPO}) "
            f"(Apache-2.0)._"
        )
    return "\n".join(out) + "\n"


def _first(d: dict[str, Any], keys: list[str]) -> Any:
    for k in keys:
        if k in d and d[k]:
            return d[k]
    return None


def _truncate(s: str, n: int) -> str:
    s = s.replace("\n", " ").strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def _md_escape(s: str) -> str:
    return s.replace("|", "\\|").replace("`", "'")


def _selftest() -> int:
    # _extract_findings normalises a handful of shapes
    assert _extract_findings([{"rule": "a"}, {"rule": "b"}]) == [
        {"rule": "a"}, {"rule": "b"},
    ]
    assert _extract_findings({"findings": [{"rule": "x"}]}) == [{"rule": "x"}]
    assert _extract_findings({"issues": [{"rule": "y"}]}) == [{"rule": "y"}]
    assert _extract_findings(
        {"nested": {"findings": [{"r": 1}]}}
    ) == [{"r": 1}]
    assert _extract_findings({}) == []
    assert _extract_findings("not a dict") == []
    # Mixed list: only dicts kept
    assert _extract_findings([{"rule": "a"}, "noise", 7]) == [{"rule": "a"}]

    # helpers
    assert _first({"a": 1, "b": 2}, ["b", "a"]) == 2
    assert _first({"a": ""}, ["a"]) is None
    assert _first({}, ["a", "b"]) is None
    assert _truncate("hello world", 5) == "hell…"
    assert _truncate("ok", 5) == "ok"
    assert _md_escape("a|b`c") == "a\\|b'c"

    # format_markdown handles all three shapes
    md = format_markdown(
        BridgeResult(available=False, error="x", target="t")
    )
    assert "unavailable" in md and "vision-model" in md

    md = format_markdown(
        BridgeResult(available=True, findings=[], target="t.html")
    )
    assert "no anti-patterns" in md

    md = format_markdown(
        BridgeResult(
            available=True,
            findings=[
                {"rule": "low-contrast", "severity": "high",
                 "selector": ".hero h1",
                 "message": "2.1:1 on body bg"},
                {"id": "overused-font", "level": "medium",
                 "where": "body", "description": "Inter detected"},
            ],
            target="page.html",
        )
    )
    assert "low-contrast" in md
    assert "overused-font" in md
    assert "2.1:1" in md and "Inter" in md
    assert "(2 findings)" in md

    # detect() gracefully handles missing npx without raising
    r = detect("http://example.com", npx_path="/nonexistent/npx-xxx")
    assert not r.available
    assert r.error

    # explicit "no npx" path
    r = detect("http://example.com", npx_path="")
    assert not r.available
    assert "npx" in r.error.lower()

    return 0


def _main(argv: list[str]) -> int:
    import argparse

    p = argparse.ArgumentParser(
        prog="python -m muriel.tools.impeccable_bridge",
        description=(
            "Run pbakaus/impeccable's deterministic anti-pattern "
            "detector and emit Markdown for inclusion in a "
            "muriel-critique report."
        ),
    )
    p.add_argument("target", nargs="?",
                   help="URL, HTML file, or directory")
    p.add_argument("--fast", action="store_true",
                   help="regex-only scan; skip Puppeteer rendering")
    p.add_argument("--json", action="store_true",
                   help="emit raw parsed JSON instead of Markdown")
    p.add_argument("--no-attribution", action="store_true",
                   help="omit the impeccable attribution line")
    p.add_argument("--timeout", type=float, default=120.0,
                   help="seconds before giving up (default 120)")
    p.add_argument("--selftest", action="store_true",
                   help="run the assertion suite")
    args = p.parse_args(argv)

    if args.selftest:
        _selftest()
        print(
            "muriel.tools.impeccable_bridge: selftest passed",
            file=sys.stderr,
        )
        return 0

    if not args.target:
        p.print_help()
        return 2

    result = detect(args.target, fast=args.fast, timeout=args.timeout)
    if args.json:
        out = {
            "available": result.available,
            "error": result.error,
            "target": result.target,
            "findings": result.findings,
        }
        print(json.dumps(out, indent=2))
    else:
        sys.stdout.write(
            format_markdown(result, attribution=not args.no_attribution)
        )
    return 0 if result.available else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
