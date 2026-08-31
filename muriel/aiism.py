"""
muriel.aiism — anti-AI-tell prose audit for paper drafts.

What this module actually detects, as of the v0.10.0 licence purge:

- Project-specific phrase tics (12 single-phrase rules) — definitional clefts
  ("the locus of X", "the unit at which Y"), "not just X but Y" parallelism,
  "earn their keep", "in observational register", bare "regime".
- Intensifier repetition (5 repeated-phrase rules) — "load-bearing",
  "structurally", "materially", "meaningfully", "already-Y" compounds, each
  with its own max_count.
- Doubled "What X is Y" clefts within 220 characters (1 proximity rule).
- Hard artifacts of LLM tooling (8 rules) — oaicite tokens, turn tokens,
  sandbox paths, ChatGPT URLs, knowledge-cutoff disclaimers, refusal
  preambles.
- Three structural heuristics — overlong clause-stacked sentences, em-dash
  density per line, mid-paragraph bold density.

What it does NOT detect, despite what earlier versions of this docstring
claimed: copula-avoidance verbs ("serves as", "stands as"),
significance-inflation phrases ("a testament to", "underscores the
importance"), prescriptive narrator framing ("It is important to note"),
padded-vocabulary clusters, throat-clearing temporal openers, and
anthropomorphized research verbs. Those rules were removed in v0.10.0 and
the docstring was not updated with them, so it advertised detectors that had
not existed for several releases. CLUSTER_RULES and PATTERN_RULES are both
empty tables for the same reason.

That coverage now lives downstream: science-agent's aiism-rules.json v6
rebuilt copula-avoidance, significance-inflation, participial significance
tails, actorless-evidence, and citation-aware weasel-attribution from
MIT-licensed sources. If you want those checks, run science-agent's
prose-audit, which loads this module as an optional second source for .md
and .ipynb input.

Sources for phrase lists:
- Local critique of paper-v4 (project-specific tics)
- Hard LLM-tooling artifact detectors (oaicite tokens, sandbox paths,
  knowledge-cutoff disclaimers, etc.) — project-specific.

As of v0.10.0, all phrase tables previously derivative of Wikipedia
"Signs of AI writing" and ammil-industries/vale-signs-of-ai-writing
(CC-BY-SA-4.0) were removed to make muriel commercial-use-clean. The
former list of 25 removed rules (significance-inflation, prescriptive-
narrator framing, throat-clearing temporal openers, anthropomorphized
research verbs, sourceless-authority hedges, four cluster detectors,
two repeated-phrase patterns) is documented in CHANGELOG.

Usage
-----

Programmatic::

    from muriel.aiism import audit_text
    findings = audit_text(open("paper.md").read())
    for f in findings:
        print(f.line, f.severity, f.rule, f.message)

CLI::

    python -m muriel.aiism paper.md
    python -m muriel.aiism paper.md --severity warn   # exit 1 on warn+
    python -m muriel.aiism paper.md --respect-pencil  # skip locked sentences

Exit status: 0 = clean, 1 = findings at or above the configured severity,
2 = usage error.

Why this exists
---------------

The project's prose accumulated AI tells under sustained collaboration: a
critique reader counted "load-bearing" seven times, em-dashes in nearly
every paragraph, and a recurring "the substrate that licenses the
partition" cleft pattern. The fixes are obvious once flagged. The tool
exists so flagging is automatic rather than left to a human reader's
patience on draft N.

Companion to ``pencil`` (sentence-level voice locking): when a
``<file>.pencil.json`` sidecar is present and ``--respect-pencil`` is
set, locked sentences are skipped because they're explicitly the human
author's voice.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

SEVERITIES = ("info", "warn", "error")
_SEV_ORDER = {s: i for i, s in enumerate(SEVERITIES)}


# ---------------------------------------------------------------------------
# Hard artifacts — leaked LLM tooling / refusal residue. Zero false-positive.
# ---------------------------------------------------------------------------

HARD_ARTIFACT_RULES: list[tuple[str, str, str]] = [
    # rule_id, regex, message
    ("artifact-oaicite", r"\boaicite\b|\boai_citation\b|:contentReference\[",
     "Leaked OpenAI tool-citation token. Strip before any external pass."),
    ("artifact-turn-token", r"\bturn\d+(?:search|fetch|view|news)\d+\b",
     "Leaked LLM tool token (turn-N). Always real; strip immediately."),
    ("artifact-sandbox-path", r"\bsandbox:/mnt/data/\S+",
     "Leaked OpenAI sandbox path. Always real."),
    ("artifact-chatgpt-url", r"\b(?:chat\.openai\.com|chatgpt\.com)/[^\s)]+",
     "Live ChatGPT URL embedded in prose. Always a paste artifact."),
    ("artifact-utm-chatgpt", r"utm_source=chatgpt\.com",
     "Citation copied from ChatGPT with tracking parameter intact."),
    ("artifact-knowledge-cutoff", r"\bas\s+of\s+my\s+(?:last\s+update|knowledge\s+cutoff|training)\b",
     "Knowledge-cutoff disclaimer is LLM throat-clearing; cut."),
    ("artifact-realtime-disclaimer", r"\bI\s+don'?t\s+have\s+access\s+to\s+real[-\s]?time\b",
     "LLM real-time-data disclaimer; cut."),
    ("artifact-refusal-preamble", r"^\s*(?:Certainly!|Sure,\s+I'?d\s+be\s+happy|I\s+cannot\s+help\s+with)",
     "Refusal/preamble residue from an LLM session. Strip."),
]


@dataclass
class Finding:
    line: int
    column: int
    severity: str
    rule: str
    message: str
    excerpt: str

    def __lt__(self, other: "Finding") -> bool:
        return (self.line, self.column, self.rule) < (other.line, other.column, other.rule)


# ---------------------------------------------------------------------------
# Rule tables
# ---------------------------------------------------------------------------

# Phrases that, on first occurrence, are themselves the tell. Case-insensitive
# unless marked. (rule_id, pattern, severity, message)
SINGLE_PHRASE_RULES: list[tuple[str, str, str, str]] = [
    ("phrase-earn-their-keep", r"\bearn(?:s|ed|ing)?\s+(?:their|its)\s+keep\b", "warn",
     "Folksy where the rest is technical. Replace with something specific."),
    ("phrase-locus-of", r"\bthe\s+locus\s+of\b", "warn",
     "Definitional cleft tic. Use 'where X happens' or just name X."),
    ("phrase-unit-at-which", r"\bthe\s+unit\s+at\s+which\b", "warn",
     "Definitional cleft tic. Most uses can become 'where X is recorded' or 'X-level'."),
    ("phrase-substrate-licenses", r"\bsubstrate\s+that\s+licenses\b", "warn",
     "Performative depth. Say 'the partition is grounded in' or just state the grounding."),
    ("phrase-doing-its-share", r"\b(?:cursor|gaze|motor\s+system)\s+is\s+doing\s+its\s+share\b", "warn",
     "Anthropomorphism reviewers will quote back at you. Drop or rephrase mechanically."),
    ("phrase-observational-register", r"\bin\s+observational\s+register\b", "warn",
     "Self-conscious framing. Trust the metaphor or unpack it plainly."),
    ("phrase-names-the-same-observation", r"\bnames\s+the\s+same\s+observation\b", "warn",
     "Title-explainer tic. Cut or rewrite as plain English."),
    ("phrase-the-hope-is-that", r"\bthe\s+hope\s+is\s+that\b", "warn",
     "Authorial-voice hedging that weakens the close. State what the work does."),
    ("phrase-looking-into-the-corners", r"\blooking\s+into\s+the\s+corners\b", "info",
     "Italicized motif. Allowed once (e.g., §5 header). Flag every additional occurrence."),
    ("phrase-leaky-cursor-aside", r"\bleaky\s+cursor.{0,40}observational\s+register\b", "warn",
     "Title aside is overwrought. Trust the title or unpack plainly."),

    # --- 19 Vale/Wikipedia-derived phrase rules removed in muriel 0.10.0
    # (significance-inflation, prescriptive-narrator framing, throat-clearing
    # temporal openers, anthropomorphized research verbs, sourceless-authority
    # hedges). These carried CC-BY-SA-4.0 share-alike obligations that
    # constrained commercial use of muriel and downstream consumers. See
    # CHANGELOG entry for full list.

    # --- En-dash escalation tic ---
    ("phrase-not-just-but", r"\bnot\s+just\s+\S+(?:\s+\S+){0,5}?\s+[—–-]\s+\S+", "warn",
     "'This is not just X — it's Y' escalation. Tell of LLM rhetoric. Convert to plain claim."),

    # --- Loaded-vocabulary in current usage ---
    ("phrase-regime", r"\bregime[s]?\b", "warn",
     "'Regime' carries political connotations in current usage; for technical contexts prefer 'phase', 'mode', or 'state'."),

    # --- Analyst-voice tells in decision memos ---
    ("phrase-priced-cost", r"\bpriced\s+cost\b", "warn",
     "Coined analyst-voice label on a cost/gain. Say 'the cost' plainly, or ground it in what was pre-identified."),
    ("phrase-document-part-as-actor",
     r"\bthe\s+\w+(?:\s+\w+)?\s+(?:the\s+)?(?:declared\s+risk|pre-?registration|risk\s+statement|(?:\w+\s+)?(?:email|memo|announcement|brief|write-?up))\s+nam(?:es?|ed)\b",
     "warn",
     "Document-part-as-actor inversion ('the cost the declared risk names'). Name the actor plainly: 'pre-identified as a risk when the work was proposed'."),
]


# ---------------------------------------------------------------------------
# Per-rule suppression — false-positive control
# ---------------------------------------------------------------------------
# A rule may name a regex that, when it also matches the local context around a
# hit, cancels that hit. This is the discipline ported from ``muriel.devibe``
# (whose rounded-corner rule skips avatar-sized boxes): flag a tell only where
# it is actually a tell. Keyed by rule_id; the context window is a few words on
# either side of the match.
RULE_SUPPRESS: dict[str, str] = {
    # "regime" is loaded in political prose but is neutral, standard vocabulary
    # in physics, applied math, and vision science: an asymptotic regime, the
    # linear regime of a psychometric function, the scotopic / low-light regime.
    # Suppress the rule when one of those technical collocations produced the
    # match, so the audit still flags "the regime's crackdown" but leaves
    # "saturation regime" alone.
    "phrase-regime": (
        r"\b(?:asymptotic|linear|non-?linear|saturat\w+|threshold|supra-?threshold|"
        r"sub-?threshold|scotopic|photopic|mesopic|foveal|parafoveal|peripheral|"
        r"ballistic|diffusiv\w+|perturbativ\w+|viscous|inertial|turbulent|laminar|"
        r"hydrodynamic|kinetic|thermodynamic|quantum|classical|relativistic|"
        r"steady-?state|transient|scaling|light|dark|contrast|luminance|noise|"
        r"signal|dose|energy|temperature|density|velocity|frequency|intensity|"
        r"coupling|stimulus|response)[-\s]+regimes?\Z"
    ),
}

_SUPPRESS_COMPILED: dict[str, "re.Pattern[str]"] = {
    rid: re.compile(pat, re.IGNORECASE) for rid, pat in RULE_SUPPRESS.items()
}


# ---------------------------------------------------------------------------
# Cleared candidates — the "do not chase" list
# ---------------------------------------------------------------------------
# Candidate tells considered and deliberately NOT flagged. Documented so they
# are not re-added on a future pass and so the audit stays narrow enough to
# trust — the same discipline as vibecoded-design-tells' "Cleared by the data"
# section (and ``muriel.devibe``'s tell #12). Over-flagging trains the writer to
# ignore the tool. (candidate, why-not)
CLEARED_CANDIDATES: list[tuple[str, str]] = [
    ("the em-dash itself",
     "A few em-dashes per paper is ordinary punctuation. Only the density rule "
     "(3+ on one line) fires; flagging every em-dash is noise."),
    ("single LLM-vocabulary words ('delve', 'leverage', 'tapestry', 'realm')",
     "High false-positive in technical prose — 'leverage' is a real mechanics "
     "term, 'realm' a math one. These lists were also CC-BY-SA-derived and were "
     "removed in 0.10.0. Cluster context, not single words, is the signal."),
    ("passive voice",
     "Standard and often correct in a methods section ('participants were "
     "recruited'). A style preference, not an AI tell."),
    ("first-person 'we' / 'our'",
     "Normal academic voice."),
    ("semicolons and parentheticals",
     "Punctuation choices, not AI signatures."),
    ("sentence-initial 'And' / 'But'",
     "A register choice common in deliberate human prose."),
    ("'regime' in a technical collocation",
     "Suppressed (see RULE_SUPPRESS): 'asymptotic / linear / scotopic regime' is "
     "neutral domain vocabulary. Only the political sense is a tell."),
]

# Phrases that repeat. Allow up to `max_count` occurrences before flagging.
REPEATED_PHRASE_RULES: list[tuple[str, str, int, str, str]] = [
    ("repeat-load-bearing", r"\bload[-\s]bearing\b", 1, "error",
     "Meme phrase. Use one place where the metaphor pulls weight; replace others with 'central', 'primary', 'defended claim'."),
    ("repeat-structurally", r"\bstructurally\b", 2, "warn",
     "Empty intensifier. Either give the number that justifies it or drop the adverb."),
    ("repeat-materially", r"\bmaterially\b", 2, "warn",
     "Empty intensifier. Either give the number or drop the adverb."),
    ("repeat-meaningfully", r"\bmeaningfully\b", 2, "warn",
     "Empty intensifier. Either give the number or drop the adverb."),
    ("repeat-already-compound", r"\balready-\w+", 5, "info",
     "Already-Y compound used many times. Vary phrasing; 'previously', 'prior', plain past tense work too."),
    # repeat-not-x-but-y and repeat-what-x-cleft removed in 0.10.0
    # (CC-BY-SA-4.0 Vale/Wikipedia-derived patterns).
]

# Cluster rules — fire when ≥threshold tokens from a list appear within a
# bounded scope (paragraph or N-word window). High false-positive on any
# single token; deadly accurate as a cluster.
# (rule_id, token_regex, threshold, scope, severity, message)
# scope ∈ {"paragraph", "200w"}
CLUSTER_RULES: list[tuple[str, str, int, str, str, str]] = [
    # All four cluster rules (cluster-padded-vocab, cluster-hedges,
    # cluster-firstly-thirdly, cluster-significance-verbs) removed in 0.10.0
    # because they relied on Vale/Wikipedia-derived word lists carrying
    # CC-BY-SA-4.0 share-alike obligations. See CHANGELOG entry.
]


# Pairs / proximity rules. (rule_id, regex, severity, message, max_proximity_chars)
PROXIMITY_RULES: list[tuple[str, str, str, str, int]] = [
    ("doubled-cleft",
     r"\bWhat\s+\w+(?:\s+\w+){0,6}?\s+(?:makes|is|carries|needs|does|matters|changes|survives)\s+\w+(?:\s+\w+){0,6}?\s+is\b",
     "warn",
     "Doubled 'What X is Y' cleft (two within close range). Sharper tell than single use; convert at least one to plain subject-verb.",
     220),
]

# Pattern rules that flag every occurrence (not count-thresholded).
PATTERN_RULES: list[tuple[str, str, str, str, int]] = [
    # Emptied in 0.10.0 along with CLUSTER_RULES: every entry was derived from
    # the Vale/Wikipedia CC-BY-SA-4.0 word lists. The engine below is retained
    # so first-party entries fire without a code change. See CHANGELOG.
]


# Heuristic: long-sentence detector. Naive sentence split on . ! ? followed
# by whitespace + capital, abbreviation-aware just enough not to fire on
# "et al." or "vs.". Mirrors pencil's splitter loosely.
_ABBREVS = {"e.g.", "i.e.", "et al.", "vs.", "cf.", "etc.", "approx.",
            "Fig.", "Eq.", "Sec.", "Tab.", "Mr.", "Dr.", "Prof.",
            "St.", "Inc.", "Ltd.", "No.", "Vol.", "p.", "pp.", "Refs."}
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\[(])")

LONG_SENTENCE_WARN = 45
LONG_SENTENCE_ERROR = 65


# ---------------------------------------------------------------------------
# Markdown awareness
# ---------------------------------------------------------------------------

def _strip_code_and_math(text: str) -> str:
    """Replace fenced code, inline code, display math, and HTML comments
    with same-length whitespace so line/column offsets are preserved."""
    out = list(text)
    in_fence = False
    in_math_block = False
    in_comment = False
    line_start = 0
    i = 0
    n = len(text)
    while i < n:
        if text[i] == "\n":
            line_start = i + 1
            i += 1
            continue
        if not (in_fence or in_math_block or in_comment):
            # Detect new line-start fence/math/comment
            if i == line_start:
                rest = text[i:i + 3]
                if rest == "```":
                    in_fence = True
                    while i < n and text[i] != "\n":
                        out[i] = " "
                        i += 1
                    continue
                if rest[:2] == "$$":
                    in_math_block = True
                    while i < n and text[i] != "\n":
                        out[i] = " "
                        i += 1
                    continue
            if text[i:i + 4] == "<!--":
                in_comment = True
            elif text[i] == "`":
                end = text.find("`", i + 1)
                if end > 0 and "\n" not in text[i:end]:
                    for j in range(i, end + 1):
                        out[j] = " "
                    i = end + 1
                    continue
            elif text[i] == "$":
                end = text.find("$", i + 1)
                if end > 0 and "\n" not in text[i:end]:
                    for j in range(i, end + 1):
                        out[j] = " "
                    i = end + 1
                    continue
        else:
            if in_fence and text[i:i + 3] == "```":
                in_fence = False
                for j in range(i, min(i + 3, n)):
                    out[j] = " "
                i += 3
                continue
            if in_math_block and text[i:i + 2] == "$$":
                in_math_block = False
                out[i] = out[i + 1] = " "
                i += 2
                continue
            if in_comment and text[i:i + 3] == "-->":
                in_comment = False
                for j in range(i, min(i + 3, n)):
                    out[j] = " "
                i += 3
                continue
            out[i] = " " if text[i] != "\n" else "\n"
        i += 1
    return "".join(out)


def _line_col(text: str, offset: int) -> tuple[int, int]:
    """Convert a 0-based byte offset to (1-based line, 1-based column)."""
    line = text.count("\n", 0, offset) + 1
    last_nl = text.rfind("\n", 0, offset)
    col = offset - last_nl
    return line, col


def _excerpt(text: str, offset: int, span: int = 80) -> str:
    start = max(0, offset - 10)
    end = min(len(text), offset + span)
    return text[start:end].replace("\n", " ").strip()


# ---------------------------------------------------------------------------
# Per-rule audit functions
# ---------------------------------------------------------------------------

def _audit_hard_artifacts(text: str, source: str) -> list[Finding]:
    """Hard artifacts run against the RAW text (not source-with-code-stripped)
    because they often appear inside what looks like a citation or URL."""
    out = []
    for rule_id, pattern, message in HARD_ARTIFACT_RULES:
        for m in re.finditer(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
            line, col = _line_col(text, m.start())
            out.append(Finding(line, col, "error", rule_id, message,
                               _excerpt(text, m.start())))
    return out


def _audit_single_phrases(text: str, source: str) -> list[Finding]:
    out = []
    for rule_id, pattern, severity, message in SINGLE_PHRASE_RULES:
        suppress = _SUPPRESS_COMPILED.get(rule_id)
        for m in re.finditer(pattern, source, flags=re.IGNORECASE):
            if suppress is not None:
                # Anchor the collocation to THIS match: is the text ending at
                # this token a technical collocation (".*<techword> regime")?
                # A two-sided window would wrongly suppress a political 'regime'
                # that merely sits near a technical one.
                pre = source[max(0, m.start() - 40):m.end()]
                if suppress.search(pre):
                    continue  # benign technical context — not a tell
            line, col = _line_col(source, m.start())
            out.append(Finding(line, col, severity, rule_id, message,
                               _excerpt(text, m.start())))
    return out


def _audit_cluster_rules(text: str, source: str) -> list[Finding]:
    """Cluster rules: fire when ≥threshold matches appear within a paragraph
    or 200-word sliding window."""
    out = []
    paragraphs: list[tuple[int, str]] = []
    offset = 0
    for chunk in re.split(r"(\n\s*\n)", source):
        if chunk.strip():
            paragraphs.append((offset, chunk))
        offset += len(chunk)

    for rule_id, pattern, threshold, scope, severity, message in CLUSTER_RULES:
        regex = re.compile(pattern, flags=re.IGNORECASE)
        if scope == "paragraph":
            for para_offset, para in paragraphs:
                hits = list(regex.finditer(para))
                if len(hits) >= threshold:
                    line, col = _line_col(source, para_offset + hits[0].start())
                    out.append(Finding(line, col, severity, rule_id,
                                       f"{message} ({len(hits)} hits in this paragraph)",
                                       _excerpt(text, para_offset + hits[0].start())))
        elif scope == "200w":
            words = list(re.finditer(r"\S+", source))
            window = 200
            i = 0
            seen_starts: set[int] = set()
            while i + window < len(words):
                window_start = words[i].start()
                window_end = words[i + window].end()
                hits = list(regex.finditer(source, window_start, window_end))
                if len(hits) >= threshold:
                    if hits[0].start() not in seen_starts:
                        line, col = _line_col(source, hits[0].start())
                        out.append(Finding(line, col, severity, rule_id,
                                           f"{message} ({len(hits)} hits in a 200-word span)",
                                           _excerpt(text, hits[0].start())))
                        seen_starts.add(hits[0].start())
                    i += window  # advance past this window to avoid duplicates
                else:
                    i += 50  # slide forward
    return out


def _audit_repeated_phrases(text: str, source: str) -> list[Finding]:
    out = []
    for rule_id, pattern, max_count, severity, message in REPEATED_PHRASE_RULES:
        flags = re.IGNORECASE | (re.MULTILINE if rule_id.startswith("repeat-what") else 0)
        matches = list(re.finditer(pattern, source, flags=flags))
        if len(matches) <= max_count:
            continue
        for m in matches:
            line, col = _line_col(source, m.start())
            out.append(Finding(line, col, severity, rule_id,
                               f"{message} (this is occurrence {matches.index(m) + 1} of {len(matches)})",
                               _excerpt(text, m.start())))
    return out


def _audit_pattern_rules(text: str, source: str) -> list[Finding]:
    out = []
    for rule_id, pattern, severity, message, flags in PATTERN_RULES:
        for m in re.finditer(pattern, source, flags=flags):
            line, col = _line_col(source, m.start())
            out.append(Finding(line, col, severity, rule_id, message,
                               _excerpt(text, m.start())))
    return out


def _audit_long_sentences(text: str, source: str) -> list[Finding]:
    out = []
    cursor = 0
    for line_no, line in enumerate(source.split("\n"), start=1):
        if not line.strip() or line.lstrip().startswith(("#", "|", "-", "*", ">")):
            cursor += len(line) + 1
            continue
        # Split into sentences within this line
        idx = cursor
        for sent in _SENT_SPLIT.split(line):
            sent = sent.strip()
            if not sent:
                continue
            words = re.findall(r"\b\w+\b", sent)
            n = len(words)
            offset_in_text = source.find(sent[:40], idx) if len(sent) >= 40 else idx
            if offset_in_text < 0:
                offset_in_text = idx
            line_no2, col = _line_col(source, offset_in_text)
            if n >= LONG_SENTENCE_ERROR:
                out.append(Finding(line_no2, col, "warn", "sentence-too-long",
                                   f"{n}-word sentence. Break into shorter sentences; reviewers tire by clause 4.",
                                   _excerpt(text, offset_in_text)))
            elif n >= LONG_SENTENCE_WARN:
                out.append(Finding(line_no2, col, "info", "sentence-long",
                                   f"{n}-word sentence. Consider breaking up.",
                                   _excerpt(text, offset_in_text)))
            idx = offset_in_text + len(sent)
        cursor += len(line) + 1
    return out


def _audit_proximity_pairs(text: str, source: str) -> list[Finding]:
    """Flag patterns that are tells specifically when they appear close
    together (e.g., two clefts in adjacent sentences)."""
    out = []
    for rule_id, pattern, severity, message, prox in PROXIMITY_RULES:
        matches = list(re.finditer(pattern, source, flags=re.MULTILINE))
        if len(matches) < 2:
            continue
        for i, m in enumerate(matches):
            for j in range(i + 1, len(matches)):
                if matches[j].start() - m.end() <= prox:
                    line, col = _line_col(source, m.start())
                    out.append(Finding(line, col, severity, rule_id,
                                       f"{message} (paired with line {_line_col(source, matches[j].start())[0]})",
                                       _excerpt(text, m.start())))
                    break
    return out


def _audit_em_dash_density(text: str, source: str) -> list[Finding]:
    out = []
    offset = 0
    for line in source.split("\n"):
        n = line.count("—") + line.count("–")
        if n >= 3:
            line_no, col = _line_col(source, offset)
            out.append(Finding(line_no, 1, "info", "density-em-dash-line",
                               f"{n} em/en-dashes on one line. Convert most to commas, periods, or parentheses.",
                               _excerpt(text, offset)))
        offset += len(line) + 1
    return out


def _audit_bold_density(text: str, source: str) -> list[Finding]:
    """Flag mid-paragraph bold (more than one **...** span per paragraph,
    or a bold span that does not start at the beginning of its paragraph)."""
    out = []
    paragraphs = re.split(r"\n\s*\n", source)
    offset = 0
    for para in paragraphs:
        bolds = list(re.finditer(r"\*\*([^*\n]{2,})\*\*", para))
        if len(bolds) >= 3:
            m = bolds[0]
            line, col = _line_col(source, offset + m.start())
            out.append(Finding(line, col, "info", "bold-overuse",
                               f"{len(bolds)} bold spans in one paragraph. Pick one register: bold the lede only.",
                               _excerpt(text, offset + m.start())))
        offset += len(para) + 2
    return out


def audit_text(text: str, *, locked_spans: list[tuple[int, int]] | None = None) -> list[Finding]:
    """Run every rule against ``text`` and return findings sorted by location.

    If ``locked_spans`` is provided (list of (start_offset, end_offset)
    tuples), findings that fall inside any locked span are dropped — those
    are the human author's voice and not subject to anti-AI rules."""
    source = _strip_code_and_math(text)
    findings: list[Finding] = []
    findings += _audit_hard_artifacts(text, source)
    findings += _audit_single_phrases(text, source)
    findings += _audit_repeated_phrases(text, source)
    findings += _audit_pattern_rules(text, source)
    findings += _audit_long_sentences(text, source)
    findings += _audit_bold_density(text, source)
    findings += _audit_em_dash_density(text, source)
    findings += _audit_proximity_pairs(text, source)
    findings += _audit_cluster_rules(text, source)

    if locked_spans:
        offsets_by_line: dict[int, int] = {}
        running = 0
        for line_no, line in enumerate(text.split("\n"), start=1):
            offsets_by_line[line_no] = running
            running += len(line) + 1

        def in_locked(f: Finding) -> bool:
            line_offset = offsets_by_line.get(f.line, 0)
            char_offset = line_offset + f.column - 1
            for start, end in locked_spans:
                if start <= char_offset < end:
                    return True
            return False

        findings = [f for f in findings if not in_locked(f)]

    findings.sort()
    return findings


# ---------------------------------------------------------------------------
# Pencil sidecar integration
# ---------------------------------------------------------------------------

def _read_file(file_path: Path) -> str:
    """Read a markdown file or extract markdown cells from a Jupyter notebook.

    For .ipynb files: returns concatenated markdown-cell sources separated
    by blank lines. Code cells, outputs, and raw cells are skipped — only
    prose is audited."""
    if file_path.suffix == ".ipynb":
        nb = json.loads(file_path.read_text())
        cells = nb.get("cells", [])
        chunks = []
        for cell in cells:
            if cell.get("cell_type") != "markdown":
                continue
            source = cell.get("source", "")
            if isinstance(source, list):
                source = "".join(source)
            if source.strip():
                chunks.append(source.rstrip() + "\n")
        return "\n".join(chunks)
    return file_path.read_text()


def _load_locked_spans(file_path: Path) -> list[tuple[int, int]]:
    sc_path = file_path.with_suffix(file_path.suffix + ".pencil.json")
    if not sc_path.exists():
        return []
    sc = json.loads(sc_path.read_text())
    text = file_path.read_text()
    spans = []
    cursor = 0
    for s in sc.get("sentences", []):
        if s.get("status") != "locked":
            continue
        sent = s.get("text", "")
        if not sent:
            continue
        idx = text.find(sent, cursor)
        if idx < 0:
            continue
        spans.append((idx, idx + len(sent)))
        cursor = idx + len(sent)
    return spans


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

_SEV_GLYPH = {"info": "·", "warn": "!", "error": "X"}
_SEV_ANSI = {"info": "\033[90m", "warn": "\033[33m", "error": "\033[31m"}
_RESET = "\033[0m"


def format_findings(findings: list[Finding], *, color: bool = True) -> str:
    if not findings:
        return "clean — no AI-tell patterns detected."
    by_severity: dict[str, int] = {"info": 0, "warn": 0, "error": 0}
    by_rule: dict[str, int] = {}
    lines = []
    for f in findings:
        by_severity[f.severity] += 1
        by_rule[f.rule] = by_rule.get(f.rule, 0) + 1
        glyph = _SEV_GLYPH[f.severity]
        if color:
            sev = f"{_SEV_ANSI[f.severity]}{glyph} {f.severity}{_RESET}"
        else:
            sev = f"{glyph} {f.severity}"
        lines.append(f"  {f.line:>4}:{f.column:<3} {sev:<14} {f.rule:<28} {f.message}")
        lines.append(f"        > {f.excerpt[:110]}")
    summary = (f"\n{by_severity['error']} error · "
               f"{by_severity['warn']} warn · "
               f"{by_severity['info']} info "
               f"({len(findings)} total, {len(by_rule)} rules)")
    by_rule_lines = "\n".join(
        f"  {n:>3}  {rule}" for rule, n in sorted(by_rule.items(), key=lambda kv: -kv[1])
    )
    return "\n".join(lines) + summary + "\n\nrule counts:\n" + by_rule_lines


def format_cleared() -> str:
    """Render the 'do not chase' list — candidate tells deliberately not flagged."""
    lines = [
        "Candidate tells deliberately NOT flagged (the 'do not chase' list).",
        "Flag what the evidence supports, at the weight it supports it; over-",
        "flagging trains the writer to ignore the tool.",
        "",
    ]
    for candidate, why in CLEARED_CANDIDATES:
        lines.append(f"  · {candidate}")
        lines.append(f"      {why}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="muriel.aiism", description=__doc__.split("\n\n")[0])
    p.add_argument("file", nargs="?", help="markdown file to audit")
    p.add_argument("--severity", choices=SEVERITIES, default="warn",
                   help="exit nonzero if any finding is at or above this severity (default: warn)")
    p.add_argument("--respect-pencil", action="store_true",
                   help="skip findings inside pencil-locked sentences (reads <file>.pencil.json)")
    p.add_argument("--no-color", action="store_true", help="disable ANSI color")
    p.add_argument("--rule", action="append", help="filter to specific rule id (repeatable)")
    p.add_argument("--json", action="store_true", help="emit findings as JSON for tool integration")
    p.add_argument("--list-cleared", action="store_true",
                   help="print the candidate tells deliberately NOT flagged (the "
                        "'do not chase' list) and exit")
    args = p.parse_args(argv)

    if args.list_cleared:
        print(format_cleared())
        return 0
    if not args.file:
        p.error("a file argument is required (unless --list-cleared)")

    fp = Path(args.file)
    if not fp.exists():
        print(f"file not found: {fp}", file=sys.stderr)
        return 2

    text = _read_file(fp)
    locked_spans = _load_locked_spans(fp) if args.respect_pencil else []
    findings = audit_text(text, locked_spans=locked_spans)
    if args.rule:
        findings = [f for f in findings if f.rule in set(args.rule)]

    if args.json:
        payload = {
            "file": str(fp),
            "findings": [
                {"line": f.line, "column": f.column, "severity": f.severity,
                 "rule": f.rule, "message": f.message, "excerpt": f.excerpt}
                for f in findings
            ],
            "summary": {
                "total": len(findings),
                "error": sum(1 for f in findings if f.severity == "error"),
                "warn": sum(1 for f in findings if f.severity == "warn"),
                "info": sum(1 for f in findings if f.severity == "info"),
            },
        }
        print(json.dumps(payload, indent=2))
    else:
        print(format_findings(findings, color=not args.no_color))

    if not findings:
        return 0
    threshold = _SEV_ORDER[args.severity]
    worst = max(_SEV_ORDER[f.severity] for f in findings)
    return 1 if worst >= threshold else 0


if __name__ == "__main__":
    sys.exit(main())
